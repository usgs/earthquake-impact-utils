# stdlib imports
import json

# third party imports
import h5py

# local imports


class HDFContainerBase(object):
    def __init__(self, hdfobj):
        """
        Instantiate an HDFContainer from an open h5py File Object.

        Args:
            hdfobj:  Open h5py File Object.
        """
        self._hdfobj = hdfobj

    @classmethod
    def create(cls, hdf_file):
        """
        Create empty container in input hdf_file.

        Args:
            hdf_file: Path to HDF file to be created.

        Returns:
            HDF instance.
        """
        hdfobj = h5py.File(hdf_file, "w")
        return cls(hdfobj)

    @classmethod
    def load(cls, hdf_file):
        """
        Instantiate an HDFContainer from an HDF5 file.

        Args:
            hdf_file: Valid path to HDF5 file.

        Returns:
            Instance of HDFContainer.
        """
        hdfobj = h5py.File(hdf_file, "r+")
        return cls(hdfobj)

    def close(self):
        """
        Close the HDF file.
        """
        self._hdfobj.close()

    def getFileName(self):
        """
        Return the name of the HDF5 file associated with this object..

        Returns:
            (str): Name of the file associated with this object.
        """
        return self._hdfobj.filename

    def _makeGroup(self, base, groups):
        if base not in self._hdfobj:
            group = self._hdfobj.create_group(base)
        else:
            group = self._hdfobj[base]
        for gg in groups:
            if gg not in group:
                group = group.create_group(gg)
            else:
                group = group[gg]
        return group

    def _getGroup(self, base, groups):
        if base not in self._hdfobj:
            raise LookupError('No %s in %s' % (base, self.getFileName()))
        group = self._hdfobj[base]
        for gg in groups:
            if gg not in group:
                raise LookupError('Group %s not in %s' % (gg, base))
            group = group[gg]
        return group

    def _getGroupPaths(self, dd):
        plist = []
        try:
            k = dd.keys()
        except Exception:
            return plist
        for kk in k:
            paths = self._getGroupPaths(dd[kk])
            if len(paths) > 0:
                for path in paths:
                    nn = kk + '/' + path
                    plist.append(nn)
            else:
                plist.append(kk)
        return plist

    #
    # Dictionaries
    #
    def getDictionary(self, groups, name):
        """Return a dictionary stored in container.

        Args:
            groups (list): A list of sub groups of the dictionaries
                group leading to 'name'. May be empty.
            name (str): String name of HDF group under which dictionary is
                stored.

        Returns:
            dict: Dictionary that was stored in input named group.
        """
        dict_group = self._getGroup('dictionaries', groups)
        if name not in dict_group:
            raise LookupError('Dictionary %s not in %s'
                              % (name, self.getFileName()))
        mdataset = dict_group[name]
        outstring = mdataset.value.decode('utf-8')
        outdict = json.loads(outstring)
        return outdict

    def setDictionary(self, groups, name, dictionary):
        """
        Store a dictionary in the HDF file, in group name.

        Args:
            groups (list): A list of sub groups of the dictionaries
                group leading to 'name'. May be empty.
            name (str): String name of HDF group under which dictionary will
                be stored.
            dictionary (dict): Dictionary to be stored. Must be JSON
                serializable.

        Returns:
            nothing: Nothing.
        """
        dict_group = self._makeGroup('dictionaries', groups)
        inbytes = json.dumps(dictionary).encode('utf-8')
        dict_group.create_dataset(name, data=inbytes)

        return

    def dropDictionary(self, groups, name):
        """
        Delete dictionary from container.

        Args:
            groups (list): A list of sub groups of the dictionaries
                group leading to 'name'. May be empty.
            name (str): The name of the dictionary to be deleted.

        Returns:
            nothing: Nothing.
        """
        dict_group = self._getGroup('dictionaries', groups)
        if name not in dict_group:
            raise LookupError('dictionary %s not in %s'
                              % (name, self._hdfobj.filename))
        del dict_group[name]
        return

    def getDictionaries(self):
        """
        Return list of paths to dictionaries stored in container.

        Returns:
          (list) List of names of dictionaries stored in container.
        """
        if 'dictionaries' not in self._hdfobj:
            return []
        return self._getGroupPaths(self._hdfobj['dictionaries'])

    #
    # Arrays
    #

    def setArray(self, groups, name, array, metadata=None, compression=True):
        """
        Store a numpy array and optional metadata in the HDF file, in group
        name.

        Args:
            groups (list): A list of sub groups of the array
                group leading to 'name'. May be empty.
            name (str): String name of HDF group under which list will be
                stored.
            array (np.ndarray) Numpy array.
            metadata (dict) Dictionary containing basic types.
            compression (bool): Boolean indicating whether dataset should be
                compressed using the gzip algorithm.

        Returns:
            nothing: Nothing.
        """
        if compression:
            compression = 'gzip'
        else:
            compression = None

        array_group = self._makeGroup('arrays', groups)

        if name in array_group:
            raise LookupError('%s already exists in %s' %
                              (name, self._hdfobj.filename))

        dset = array_group.create_dataset(name, data=array,
                                          compression=compression)
        if metadata:
            for key, value in metadata.items():
                dset.attrs[key] = value
        return dset

    def getArray(self, groups, name):
        """
        Retrieve an array of data and any associated metadata from a dataset.

        Args:
            groups (list): A list of sub groups of the array
                group leading to 'name'. May be empty.
            name (str): The name of the dataset holding the data and metadata.

        Returns:
            tuple: An array of data, and a dictionary of metadata.
        """

        array_group = self._getGroup('arrays', groups)
        if name not in array_group:
            raise LookupError('Array %s not in %s'
                              % (name, self.getFileName()))
        dset = array_group[name]
        data = dset[()]
        metadata = {}
        for key, value in dset.attrs.items():
            metadata[key] = value
        return data, metadata

    def getArrays(self):
        """
        Return list of paths of arrays stored in container.

        Returns:
            list: List of names of arrays stored in container.
        """
        if 'arrays' not in self._hdfobj:
            return []
        return self._getGroupPaths(self._hdfobj['arrays'])

    def dropArray(self, groups, name):
        """
        Delete array from container.

        Args:
            groups (list): A list of sub groups of the array
                group leading to 'name'. May be empty.
            name (str): The name of the array to be deleted.

        """
        array_group = self._getGroup('arrays', groups)
        del array_group[name]

    #
    # Strings
    #

    def setString(self, groups, name, instring):
        """
        Store a string in the HDF file, as the attribute name under a special
        group.

        Args:
            groups (list): A list of sub groups of the string
                group leading to 'name'. May be empty.
            name (str): String name of group attribute under which string will
                be stored.
            instring (str): Python string.

        Returns:
            nothing: Nothing.
        """
        string_group = self._makeGroup('strings', groups)
        inbytes = instring.encode('utf-8')
        string_group.create_dataset(name, data=inbytes)
        return

    def getString(self, groups, name):
        """
        Retrieve a string from a attribute name in a special group.

        Args:
            groups (list): A list of sub groups of the string
                group leading to 'name'. May be empty.
            name (str): The name of the attribute containing the string.

        Returns:
            str: A Python string object.
        """
        string_group = self._getGroup('strings', groups)
        if name not in string_group:
            raise LookupError('Dictionary %s not in %s'
                              % (name, self.getFileName()))
        mdataset = string_group[name]
        outstring = mdataset.value.decode('utf-8')
        return outstring

    def getStrings(self):
        """
        Return list of names of strings stored in container.

        Returns:
          (list) List of names of strings stored in container.
        """
        if 'strings' not in self._hdfobj:
            return []
        return self._getGroupPaths(self._hdfobj['strings'])

    def dropString(self, groups, name):
        """
        Delete string from container.

        Args:
            groups (list): A list of sub groups of the string
                group leading to 'name'. May be empty.
            name (str): The name of the string to be deleted.

        Returns:
            nothing: Nothing.
        """
        string_group = self._getGroup('strings', groups)
        if name not in string_group:
            raise LookupError('string %s not in %s'
                              % (name, self._hdfobj.filename))
        del string_group[name]


class ShakeMapContainerBase(HDFContainerBase):
    """
    Parent class for InputShakeMapContainer and OutputShakeMapContainer.
    """

    def setConfig(self, config):
        """
        Add the config as a dictionary to the HDF file.

        Args:
            config (dict--like): Dict--like object with configuration
                information.
        """
        if 'config' in self.getDictionaries():
            self.dropDictionary([], 'config')
        self.setDictionary([], 'config', config)

    def getConfig(self):
        """
        Retrieve configuration dictionary from container.

        Returns:
            dict: Configuration dictionary.
        Raises:
            AttributeError: If config dictionary has not been set in
                the container.
        """
        if 'config' not in self.getDictionaries():
            raise AttributeError('Configuration not set in container.')
        return self.getDictionary([], 'config')

    def setRuptureDict(self, rupture):
        """
        Store Rupture dict in container.

        Args:
            rupture (dict): Dictionary representation of Rupture.
        Raises:
            TypeError: If input object or dictionary does not
                represent a Rupture object.
        """
        if 'rupture' in self.getDictionaries():
            self.dropDictionary([], 'rupture')
        if not isinstance(rupture, dict):
            fmt = 'Input dict does not represent a rupture object.'
            raise TypeError(fmt)
        self.setDictionary([], 'rupture', rupture)

    def getRuptureDict(self):
        """
        Retrieve Rupture dictionary from container.

        Returns:
            dict: Dictionary representatin of (one of) a
                Point/Quad/EdgeRupture class.
        Raises:
            AttributeError: If rupture object has not been set in
                the container.
        """
        if 'rupture' not in self.getDictionaries():
            raise AttributeError('Rupture object not set in container.')
        return self.getDictionary([], 'rupture')

    def setStationDict(self, stationdict):
        """
        Store (JSON-like) station dictionary in container.

        Args:
            stationdict (dict-like): Station dict object.
        Raises:
            TypeError: If input object is not a dictionary.
        """
        if not isinstance(stationdict, dict):
            fmt = 'Input object is not a dictionary.'
            raise TypeError(fmt)
        if 'stations_dict' in self.getDictionaries():
            self.dropDictionary([], 'stations_dict')
        self.setDictionary([], 'stations_dict', stationdict)

    def getStationDict(self):
        """
        Retrieve (JSON-like) station dictionary from container.

        Returns:
            dict-like: Station dictionary.
        Raises:
            AttributeError: If station dictionary has not been set in
                the container.
        """
        if 'stations_dict' not in self.getDictionaries():
            raise AttributeError('Station dictionary not set in container.')
        return self.getDictionary([], 'stations_dict')

    def setVersionHistory(self, history_dict):
        """
        Store a dictionary containing version history in the container.

        Args:
            history_dict (dict): Dictionary containing version history. ??
        """
        if 'version_history' in self.getDictionaries():
            self.dropDictionary([], 'version_history')
        self.setDictionary([], 'version_history', history_dict)
        return

    def getVersionHistory(self):
        """
        Return the dictionary containing version history.

        Returns:
          dict: Dictionary containing version history, or None.
        Raises:
            AttributeError: If version history has not been set in
                the container.
        """

        if 'version_history' not in self.getDictionaries():
            return {}
        return self.getDictionary([], 'version_history')


class ShakeMapOutputContainer(ShakeMapContainerBase):
    """
    HDF container for Shakemap output data.

    This class provides methods for getting and setting IMT data.
    The philosophy here is that an IMT consists of both the mean results and
    the standard deviations of those results, thus getIMTArrays() (when data
    type is 'points') and getIMTGrids() (when data type is 'grids') returns a
    dictionary with both, plus metadata for each data layer.


    """

    def setDataType(self, datatype):
        """
        Sets the type of the IMT, Vs30, and distance data stored in this
        file. This function should not be called by the user -- the value
        will be set by the first call to setIMTGrids() or setIMTArray().

        Args:
            datatype (str): Either 'points' or 'grid'.

        Returns:
            Nothing.
        """

        if datatype != 'points' and datatype != 'grid':
            raise TypeError('Trying to set unknown data type: %s' %
                            (datatype))
        group_name = 'file_data_type'

        if group_name in self.getDictionaries():
            current_data_type = self.getDictionary([], group_name)['type']
            if current_data_type != datatype:
                raise TypeError(
                    'Trying to set data type to %s; file already type %s'
                    % (datatype, current_data_type))
            #
            # Data type is already set; don't have to do anything
            #
            return
        type_dict = {'type': datatype}
        self.setDictionary([], group_name, type_dict)
        return

    def getDataType(self):
        """
        Returns the format of the IMT, Vs30, and distance data stored in
        this file: either 'points' or 'grid'. None is returned if no data
        have been set.

        Returns:
            str or None: Either 'grid' or 'points' or None.
        """

        group_name = 'file_data_type'
        if group_name in self.getDictionaries():
            return self.getDictionary([], group_name)['type']
        return None

    def setMetadata(self, info):
        """Store the metadata dictionary "info".

        Args:
            info (dict): A dictionary of metadata.

        Returns:
            nothing: Nothing.
        """
        if 'info.json' in self.getDictionaries():
            self.dropDictionary([], 'info.json')
        self.setDictionary([], 'info.json', info)
        return

    def getMetadata(self):
        """Get metadata dictionary, i.e., 'info.json'.

        Returns:
            dict: Metadata dictionary.
        """
        if 'info.json' not in self.getDictionaries():
            raise LookupError('No metadata in %s' % (self.getFileName()))
        return self.getDictionary([], 'info.json')

    def setIMTGrids(self, imt_name, imt_mean, mean_metadata,
                    imt_std, std_metadata, component,
                    compression=True):
        """
        Store IMT mean and standard deviation objects as datasets.

        Args:
            imt_name (str): Name of the IMT (MMI, PGA, etc.) to be stored.
            imt_mean (numpy array): Array of IMT mean values to be stored.
            mean_metadata (dict): Dictionary containing metadata for mean IMT
                grid.
            imt_std (numpy array): Array of IMT standard deviation values
                to be stored.
            std_metadata (dict): Dictionary containing metadata for mean IMT
                grid.
            component (str): Component type, i.e. 'Larger','rotd50',etc.
            compression (bool): Boolean indicating whether dataset should be
                compressed using the gzip algorithm.

        Returns:
            nothing: Nothing.
        """

        if self.getDataType() == 'points':
            raise TypeError('Setting grid data in a file containing points')
        self.setDataType('grid')

        sub_groups = ['imts', component, imt_name]
        self.setArray(sub_groups, 'mean', imt_mean, mean_metadata)
        self.setArray(sub_groups, 'std', imt_std, std_metadata)
        return

    def getIMTGrids(self, imt_name, component):
        """
        Retrieve a Grid2D object and any associated metadata from the
        container.

        Args:
            imt_name (str):
                The name of the IMT stored in the container.
            component (str):
                The component of the IMT.

        Returns:
            dict: Dictionary containing 4 items:
                   - mean Numpy array for IMT mean values.
                   - mean_metadata Dictionary containing any metadata
                     describing mean layer.
                   - std Numpy array for IMT standard deviation values.
                   - std_metadata Dictionary containing any metadata
                     describing standard deviation layer.
        """

        if self.getDataType() != 'grid':
            raise TypeError('Requesting grid data from file containing points')

        sub_groups = ['imts', component, imt_name]
        mean_dset, mean_metadata = self.getArray(sub_groups, 'mean')
        std_dset, std_metadata = self.getArray(sub_groups, 'std')
        mean_data = mean_dset[()]
        std_data = std_dset[()]

        # create an output dictionary
        imt_dict = {
            'mean': mean_data,
            'mean_metadata': mean_metadata,
            'std': std_data,
            'std_metadata': std_metadata
        }
        return imt_dict

    def setIMTArrays(self, imt_name, lons, lats, ids,
                     imt_mean, mean_metadata,
                     imt_std, std_metadata,
                     component, compression=True):
        """
        Store IMT mean and standard deviation objects as datasets.

        Args:
            imt_name (str): Name of the IMT (MMI, PGA, etc.) to be stored.
            lons (Numpy array): Array of longitudes of the IMT data.
            lats (Numpy array): Array of latitudes of the IMT data.
            ids (Numpy array): Array of ID strings corresponding to the
                locations given by lons and lats.
            imt_mean (Numpy array): Array of IMT mean values to be stored.
            mean_metadata (dict): Dictionary containing metadata for mean IMT
                grid.
            imt_std (Numpy array): Array of IMT standard deviation values
                to be stored.
            std_metadata (dict): Dictionary containing metadata for mean IMT
                grid.
            component (str): Component type, i.e. 'Larger','rotd50',etc.
            compression (bool): Boolean indicating whether dataset should be
                compressed using the gzip algorithm.

        Returns:
            nothing: Nothing.
        """

        if self.getDataType() == 'grid':
            raise TypeError('Setting point data in a file containing grids')
        self.setDataType('points')

        #
        # Check that all of the arrays are the same
        # size
        #
        if lons.shape != lats.shape or \
           lons.shape != ids.shape or \
           lons.shape != imt_mean.shape or \
           lons.shape != imt_std.shape:
            raise ValueError('All input arrays must be the same shape')

        # set up the name of the group holding all the information for the IMT
        sub_groups = ['imts', component, imt_name]

        # create data sets containing the longitudes, latitudes, and ids

        self.setArray(sub_groups, 'lons', lons, compression=compression)
        self.setArray(sub_groups, 'lats', lats, compression=compression)
        self.setArray(sub_groups, 'ids', ids, compression=compression)

        self.setArray(sub_groups, 'mean', imt_mean, metadata=mean_metadata,
                      compression=compression)
        self.setArray(sub_groups, 'std', imt_std, metadata=std_metadata,
                      compression=compression)
        return

    def getIMTArrays(self, imt_name, component):
        """
        Retrieve the arrays and any associated metadata from the container.

        Args:
            imt_name (str): The name of the IMT stored in the container.

        Returns:
            dict: Dictionary containing 7 items:
                   - lons -- array of longitude coordinates
                   - lats -- array of latitude coordinates
                   - ids -- array of IDs corresponding to the coordinates
                   - mean -- array of IMT mean values.
                   - mean_metadata -- Dictionary containing any metadata
                     describing mean layer.
                   - std -- array of IMT standard deviation values.
                   - std_metadata -- Dictionary containing any metadata
                     describing standard deviation layer.
        """

        if self.getDataType() != 'points':
            raise TypeError('Requesting point data from file containing grids')

        sub_groups = ['imts', component, imt_name]

        dset, _ = self.getArray(sub_groups, 'lons')
        lons = dset[()]
        dset, _ = self.getArray(sub_groups, 'lats')
        lats = dset[()]
        dset, _ = self.getArray(sub_groups, 'ids')
        ids = dset[()]
        dset, mean_metadata = self.getArray(sub_groups, 'mean')
        mean_data = dset[()]
        dset, std_metadata = self.getArray(sub_groups, 'std')
        std_data = dset[()]

        # create an output dictionary
        imt_dict = {
            'lons': lons,
            'lats': lats,
            'ids': ids,
            'mean': mean_data,
            'mean_metadata': mean_metadata,
            'std': std_data,
            'std_metadata': std_metadata
        }
        return imt_dict

    def getIMTs(self, component=None):
        """Return list of names of available IMTs.

        Args:
            component (str): Optional string to filter result to only include
                IMTs available for this component. Default of None returns
                all IMTs regardless of component.

        Returns:
            list: List of names of IMTs.
        """

        imts = []
        if 'arrays' not in self._hdfobj or \
           'imts' not in self._hdfobj['arrays']:
            return imts

        if component is None:
            components = self._hdfobj['arrays']['imts'].keys()
            for comp in components:
                imtlist = self._hdfobj['arrays']['imts'][comp].keys()
                for imt in imtlist:
                    imts.append(comp + '/' + imt)
            return imts
        else:
            imtlist = self._hdfobj['arrays']['imts'][component].keys()
            for imt in imtlist:
                imts.append(imt)
            return imts

    def getComponents(self, imt_name=None):
        """
        Return list of components for given IMT.

        Args:
            imt_name (str): Name of IMT ('mmi', 'pga', etc.) If 'None',
                all the components in the file will be returned.

        Returns:
            list: List of names of components for given IMT.
        """
        if 'arrays' not in self._hdfobj or \
           'imts' not in self._hdfobj['arrays']:
            return []
        if imt_name is None:
            return self._hdfobj['arrays']['imts'].keys()
        else:
            components = []
            for component in self.getComponents():
                if imt_name in self._hdfobj['arrays']['imts'][component]:
                    components.append(component)
            return components

    def dropIMT(self, imt_name):
        """
        Delete IMT datasets from container.

        Args:
            name (str): The name of the IMT to be deleted.

        """
        if 'arrays' not in self._hdfobj or \
           'imts' not in self._hdfobj['arrays']:
            raise LookupError('No IMTs stored in HDF file %s'
                              % (self.getFileName()))
        components = self.getComponents(imt_name)
        for comp in components:
            del self._hdfobj['arrays']['imts'][comp][imt_name]
