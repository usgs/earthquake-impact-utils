#!/usr/bin/env python

# stdlib imports
from datetime import datetime
import collections
import copy
import json
import warnings

# third party imports
import h5py
import numpy as np
import pandas as pd

# local imports
from impactutils.time.ancient_time import HistoricTime


# list of allowed data types in dictionaries
ALLOWED = [str, int, float, bool, bytes,
           type(None),
           list, tuple, np.ndarray,
           np.float64, np.bool_, np.int64,
           dict, datetime, pd.Timestamp,
           collections.OrderedDict]

TIMEFMT = '%Y-%m-%d %H:%M:%S.%f'

GROUPS = {'dict': 'dictionaries',
          'list': 'lists',
          'string': 'strings',
          'array': 'arrays',
          'dataframe': 'dataframes'}


class HDFContainer(object):
    def __init__(self, hdfobj):
        """
        Instantiate an HDFContainer from an open h5py File Object.

        Args:
            hdfobj:  Open h5py File Object.
        """
        msg = ("The HDFContainer (impactutils.io.container.HDFContainer) "
               "is deprecated; use HDFContainerBase "
               "(impactutils.io.smcontainer.HDFContainerBase). "
               "This class will be removed.")
        warnings.warn(msg, DeprecationWarning, stacklevel=2)
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
        # probably should do some validating to make sure relevant data exists
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

    #
    # Dictionaries
    #
    def getDictionary(self, name):
        """Return a dictionary stored in container.

        Args:
            name (str): String name of HDF group under which dictionary is
                stored.

        Returns:
            dict: Dictionary that was stored in input named group.
        """
        dict_name = f'{name}'
        dict_group = self._hdfobj[GROUPS['dict']]
        if dict_name not in dict_group:
            raise LookupError(f'Dictionary {name} not in {self.getFileName()}')
        mdataset = dict_group[dict_name]
        outstring = mdataset[()].decode('utf-8')
        outdict = json.loads(outstring)
        return outdict

    def setDictionary(self, name, dictionary):
        """
        Store a dictionary in the HDF file, in group name.

        Args:
            name (str): String name of HDF group under which dictionary will be
                stored.
            dictionary (dict): Dictionary containing any of the following
                combinations of elements:
                - str, int, float, bool, bytes, type(None),
                  list, tuple, np.ndarray,
                  np.float64, np.bool_, np.int64,
                  dict, datetime, pd.Timestamp,
                  xcollections.OrderedDict
        Returns:
            Group: HDF5 Group object.
        """
        dict_name = f'{name}'
        if GROUPS['dict'] not in self._hdfobj:
            dict_group = self._hdfobj.create_group(GROUPS['dict'])
        else:
            dict_group = self._hdfobj[GROUPS['dict']]

        inbytes = json.dumps(dictionary).encode('utf-8')
        mdataset = dict_group.create_dataset(dict_name, data=inbytes)

        return mdataset

    def dropDictionary(self, name):
        """
        Delete dictionary from container.

        Args:
            name (str): The name of the dictionary to be deleted.

        """
        mdict = f'{name}'
        dict_group = self._hdfobj[GROUPS['dict']]
        if mdict not in dict_group:
            raise LookupError(
                f'dictionary {name} not in {self._hdfobj.filename}')
        del dict_group[mdict]

    def getDictionaries(self):
        """
        Return list of names of dictionaries stored in container.

        Returns:
          (list) List of names of dictionaries stored in container.
        """
        if GROUPS['dict'] not in self._hdfobj:
            return []
        dictionaries = list(self._hdfobj[GROUPS['dict']].keys())
        return dictionaries

    #
    # Lists
    #
    def setList(self, name, inlist):
        """
        Store a homogenous list in the HDF file.

        Args:
            name (str): String name of HDF group under which list will be
                stored.
            inlist (list): List containing any of the following data types:
                - str, int, float, bool, bytes, type(None),
                  list, tuple, np.ndarray,
                  np.float64, np.bool_, np.int64,
                  dict, datetime, pd.Timestamp,
                  collections.OrderedDict

        Returns:
            Group: HDF5 Group object.
        """
        list_name = f'{name}'
        if GROUPS['list'] not in self._hdfobj:
            list_group = self._hdfobj.create_group(GROUPS['list'])
        else:
            list_group = self._hdfobj[GROUPS['list']]

        inbytes = json.dumps(inlist).encode('utf-8')
        mdataset = list_group.create_dataset(list_name, data=inbytes)

        return mdataset

    def getList(self, name):
        """Return a list stored in container.

        Args:
            name (str): String name of HDF group under which list is stored.

        Returns:
            list: List that was stored in input named group.
        """
        list_name = f'{name}'
        list_group = self._hdfobj[GROUPS['list']]
        if list_name not in list_group:
            raise LookupError(f'List {name} not in {self.getFileName()}')
        mdataset = list_group[list_name]
        outstring = mdataset[()].decode('utf-8')
        outlist = json.loads(outstring)
        return outlist

    def getLists(self):
        """
        Return list of names of lists stored in container.

        Returns:
            list: List of names of lists stored in container.
        """
        if GROUPS['list'] not in self._hdfobj:
            return []
        lists = list(self._hdfobj[GROUPS['list']].keys())
        return lists

    def dropList(self, name):
        """
        Delete list from container.

        Args:
            name (str): The name of the list to be deleted.

        """
        mlist = f'{name}'
        list_group = self._hdfobj[GROUPS['list']]
        if mlist not in list_group:
            raise LookupError(f'list {name} not in {self._hdfobj.filename}')
        del list_group[mlist]

    #
    # Arrays
    #

    def setArray(self, name, array, metadata=None, compression=True):
        """
        Store a numpy array and optional metadata in the HDF file, in group
        name.

        Args:
            name (str): String name of HDF group under which list will be
                stored.
            array (np.ndarray) Numpy array.
            metadata (dict) Dictionary containing any of the following data
                types:
                - str, int, float, bool, bytes, type(None),
                  list, tuple, np.ndarray,
                  np.float64, np.bool_, np.int64,
                  dict, datetime, pd.Timestamp,
                  collections.OrderedDict
            compression (bool): Boolean indicating whether dataset should be
                compressed using the gzip algorithm.

        Returns:
            Dataset: HDF5 Dataset object.
        """
        if compression:
            compression = 'gzip'
        else:
            compression = None

        array_name = f'{name}'
        if GROUPS['array'] not in self._hdfobj:
            array_group = self._hdfobj.create_group(GROUPS['array'])
        else:
            array_group = self._hdfobj[GROUPS['array']]

        dset = array_group.create_dataset(
            array_name, data=array, compression=compression)
        if metadata:
            for key, value in metadata.items():
                dset.attrs[key] = value
        return dset

    def getArray(self, name):
        """
        Retrieve an array of data and any associated metadata from a dataset.

        Args:
            name (str): The name of the dataset holding the data and metadata.

        Returns:
            tuple: An array of data, and a dictionary of metadata.
        """

        array_name = f'{name}'
        array_group = self._hdfobj[GROUPS['array']]
        if array_name not in array_group:
            raise LookupError(f'Array {name} not in {self.getFileName()}')
        dset = array_group[array_name]
        data = dset[()]
        metadata = {}
        for key, value in dset.attrs.items():
            metadata[key] = value
        return data, metadata

    def getArrays(self):
        """
        Return list of names of arrays stored in container.

        Returns:
            list: List of names of arrays stored in container.
        """
        if GROUPS['array'] not in self._hdfobj:
            return []
        arrays = list(self._hdfobj[GROUPS['array']].keys())
        return arrays

    def dropArray(self, name):
        """
        Delete array from container.

        Args:
            name (str): The name of the array to be deleted.

        """
        marray = f'{name}'
        array_group = self._hdfobj[GROUPS['array']]
        if marray not in array_group:
            raise LookupError(f'Array {name} not in {self._hdfobj.filename}')
        del array_group[marray]

    #
    # Strings
    #

    def setString(self, name, instring):
        """
        Store a string in the HDF file, as the attribute name under a special
        group.

        Args:
            name (str): String name of group attribute under which string will
                be stored.
            instring (str): Python string.

        Returns:
            Group: HDF5 Group object.
        """

        string_name = f'{name}'
        if GROUPS['string'] not in self._hdfobj:
            string_group = self._hdfobj.create_group(GROUPS['string'])
        else:
            string_group = self._hdfobj[GROUPS['string']]

        inbytes = instring.encode('utf-8')
        mdataset = string_group.create_dataset(string_name, data=inbytes)

        return mdataset

    def getString(self, name):
        """
        Retrieve a string from a attribute name in a special group.

        Args:
            name (str): The name of the attribute containing the string.

        Returns:
            str: A Python string object.
        """
        string_name = f'{name}'
        string_group = self._hdfobj[GROUPS['string']]
        if string_name not in string_group:
            raise LookupError(f'Dictionary {name} not in {self.getFileName()}')
        mdataset = string_group[string_name]
        outstring = mdataset[()].decode('utf-8')
        return outstring

    def getStrings(self):
        """
        Return list of names of strings stored in container.

        Returns:
          (list) List of names of strings stored in container.
        """
        if GROUPS['string'] not in self._hdfobj:
            return []
        strings = list(self._hdfobj[GROUPS['string']].keys())
        return strings

    def dropString(self, name):
        """
        Delete string from container.

        Args:
            name (str): The name of the string to be deleted.

        """
        mstring = f'{name}'
        string_group = self._hdfobj[GROUPS['string']]
        if mstring not in string_group:
            raise LookupError(f'string {name} not in {self._hdfobj.filename}')
        del string_group[mstring]

    #
    # Dataframes
    #
    def setDataFrame(self, name, dataframe):
        """
        Store a pandas DataFrame in the HDF file, as a dictionary object.

        Args:
            name (str): String name of group under which DataFrame will be
                stored.
            dataframe (pd.DataFrame): pandas DataFrame.

        Returns:
            Group: HDF5 Group object.
        """
        dataframe_name = f'{name}'
        if GROUPS['dataframe'] not in self._hdfobj:
            dataframe_group = self._hdfobj.create_group(GROUPS['dataframe'])
        else:
            dataframe_group = self._hdfobj[GROUPS['dataframe']]

        inbytes = dataframe.to_json(date_format='iso').encode('utf-8')
        mdataset = dataframe_group.create_dataset(dataframe_name, data=inbytes)
        # use attributes to store time columns?
        cidx = dataframe.select_dtypes(include=['datetime64[ns]']).columns
        clist = cidx.tolist()
        cstr = json.dumps(clist)
        mdataset.attrs['time_columns'] = cstr.encode('utf-8')
        return mdataset

    def getDataFrame(self, name):
        """Return a DataFrame stored in container.

        Args:
            name (str): String name of HDF group under which DataFrame is
                stored.

        Returns:
            dict: DataFrame that was stored in input named group.
        """
        dataframe_name = f'{name}'
        dataframe_group = self._hdfobj[GROUPS['dataframe']]
        if dataframe_name not in dataframe_group:
            raise LookupError(f'Dataframe {name} not in {self.getFileName()}')
        mdataset = dataframe_group[dataframe_name]
        outstring = mdataset[()].decode('utf-8')

        # in setDataFrame, we stored the names of the
        # date/time columns in an attribute.  Let's use that
        # now to make sure those are read back in with the appropriate
        # type
        clist = json.loads(mdataset.attrs['time_columns'].decode('utf-8'))
        dataframe = pd.read_json(outstring, convert_dates=clist)

        return dataframe

    def getDataFrames(self):
        """
        Return list of names of DataFrames stored in container.

        Returns:
            list: List of names of dictionaries stored in container.
        """
        if GROUPS['dataframe'] not in self._hdfobj:
            return []
        dataframes = list(self._hdfobj[GROUPS['dataframe']].keys())
        return dataframes

    def dropDataFrame(self, name):
        """
        Delete dataframe from container.

        Args:
            name (str): The name of the dataframe to be deleted.

        """
        mdataframe = f'{name}'
        dataframe_group = self._hdfobj[GROUPS['dataframe']]
        if mdataframe not in dataframe_group:
            raise LookupError(
                f'dataframe {name} not in {self._hdfobj.filename}')
        del dataframe_group[mdataframe]

    #
    # Dataframes
    #
