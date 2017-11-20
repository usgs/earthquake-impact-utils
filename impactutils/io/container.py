#!/usr/bin/env python

# stdlib imports
from datetime import datetime
import collections
import copy

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


class HDFContainer(object):
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
        group_name = '__dictionary_%s__' % name
        if group_name not in self._hdfobj:
            raise LookupError('Dictionary %s not in %s'
                              % (name, self.getFileName()))
        mgroup = self._hdfobj[group_name]
        dict = _h5group2dict(mgroup)
        return dict

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
        indict = copy.deepcopy(dictionary)
        group_name = '__dictionary_%s__' % name
        mgroup = self._hdfobj.create_group(group_name)
        _dict2h5group(indict, mgroup)
        return mgroup

    def dropDictionary(self, name):
        """
        Delete dictionary from container.

        Args:
            name (str): The name of the dictionary to be deleted.

        """
        _drop_item(self._hdfobj, name, 'dictionary')

    def getDictionaries(self):
        """
        Return list of names of dictionaries stored in container.

        Returns:
          (list) List of names of dictionaries stored in container.
        """

        dictionaries = _get_type_list(self._hdfobj, 'dictionary')
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
        if isinstance(inlist[0], dict):
            raise TypeError('lists with dictionaries are not supported.')
        dtype = type(inlist[0])
        for element in inlist[1:]:
            if type(element) != dtype:
                raise TypeError('Heterogeneous lists are not supported.')

        newlist = _encode_list(inlist[:])  # encode a copy of the list
        group_name = '__list_%s__' % name
        mgroup = self._hdfobj.create_group(group_name)
        mgroup.attrs['list'] = _encode_list(newlist)
        return mgroup

    def getList(self, name):
        """Return a list stored in container.

        Args:
            name (str): String name of HDF group under which list is stored.

        Returns:
            list: List that was stored in input named group.
        """
        group_name = '__list_%s__' % name
        if group_name not in self._hdfobj:
            raise LookupError('List %s not in %s' % (name, self.getFileName()))
        mgroup = self._hdfobj[group_name]
        outlist = _decode_list(mgroup.attrs['list'])
        return outlist

    def getLists(self):
        """
        Return list of names of lists stored in container.

        Returns:
            list: List of names of lists stored in container.
        """
        lists = _get_type_list(self._hdfobj, 'list')
        return lists

    def dropList(self, name):
        """
        Delete list from container.

        Args:
            name (str): The name of the list to be deleted.

        """
        _drop_item(self._hdfobj, name, 'list')

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
        array_name = '__array_%s__' % name
        dset = self._hdfobj.create_dataset(
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

        array_name = '__array_%s__' % name
        if array_name not in self._hdfobj:
            raise LookupError('Array %s not in %s'
                              % (name, self.getFileName()))
        dset = self._hdfobj[array_name]
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
        arrays = _get_type_list(self._hdfobj, 'array')
        return arrays

    def dropArray(self, name):
        """
        Delete array from container.

        Args:
            name (str): The name of the array to be deleted.

        """
        _drop_item(self._hdfobj, name, 'array')

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

        # Create a special group to hold all of these strings as attributes.
        group_name = '__string_%s__' % name
        mgroup = self._hdfobj.create_group(group_name)

        mgroup.attrs['string'] = instring
        return mgroup

    def getString(self, name):
        """
        Retrieve a string from a attribute name in a special group.

        Args:
            name (str): The name of the attribute containing the string.

        Returns:
            str: A Python string object.
        """
        group_name = '__string_%s__' % name
        if group_name not in self._hdfobj:
            raise LookupError('String %s not in %s'
                              % (name, self.getFileName()))
        outstring = self._hdfobj[group_name].attrs['string']
        return outstring

    def getStrings(self):
        """
        Return list of names of strings stored in container.

        Returns:
          (list) List of names of strings stored in container.
        """
        strings = _get_type_list(self._hdfobj, 'string')
        return strings

    def dropString(self, name):
        """
        Delete string from container.

        Args:
            name (str): The name of the string to be deleted.

        """
        _drop_item(self._hdfobj, name, 'string')

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
        framedict = dataframe.to_dict('list')
        for cname, column in framedict.items():
            if isinstance(column[0], pd.Timestamp):
                column = [c.to_pydatetime() for c in column]
                framedict[cname] = column
        group_name = '__dataframe_%s__' % name
        mgroup = self._hdfobj.create_group(group_name)
        _dict2h5group(framedict, mgroup)
        return mgroup

    def getDataFrame(self, name):
        """Return a DataFrame stored in container.

        Args:
            name (str): String name of HDF group under which DataFrame is
                stored.

        Returns:
            dict: DataFrame that was stored in input named group.
        """
        group_name = '__dataframe_%s__' % name
        if group_name not in self._hdfobj:
            raise LookupError('DataFrame %s not in %s'
                              % (name, self.getFileName()))
        mgroup = self._hdfobj[group_name]
        datadict = _h5group2dict(mgroup)
        for key, value in datadict.items():
            try:
                HistoricTime.strptime(value[0], TIMEFMT)
                value = [HistoricTime.strptime(v, TIMEFMT) for v in value]
                datadict[key] = value
            except:
                pass
        dataframe = pd.DataFrame(datadict)
        return dataframe

    def getDataFrames(self):
        """
        Return list of names of DataFrames stored in container.

        Returns:
            list: List of names of dictionaries stored in container.
        """
        dataframes = _get_type_list(self._hdfobj, 'dataframe')
        return dataframes

    def dropDataFrame(self, name):
        """
        Delete dataframe from container.

        Args:
            name (str): The name of the dataframe to be deleted.

        """
        _drop_item(self._hdfobj, name, 'dataframe')

    #
    # Dataframes
    #


def _h5group2dict(group):
    """
    Recursively create dictionaries from groups in an HDF file.

    Args:
        group: HDF5 group object.

    Returns:
        dict: Dictionary of metadata (possibly containing other dictionaries).
    """
    tdict = {}
    for (key, value) in group.attrs.items():  # attrs are NOT subgroups

        if isinstance(value, bytes):
            value = value.decode('utf8')
            try:
                value = HistoricTime.strptime(value, TIMEFMT)
            except ValueError:
                pass
        elif isinstance(value, str):
            try:
                value = HistoricTime.strptime(value, TIMEFMT)
            except ValueError:
                pass
        tdict[key] = value

    for (key, value) in group.items():  # these are going to be the subgroups
        tdict[key] = _h5group2dict(value)
    return _convert(tdict)


def _dict2h5group(mydict, group):
    """
    Recursively save dictionaries into groups in an HDF group..

    Args:
        mydict (dict):
            Dictionary of values to save in group or dataset.  Dictionary
            can contain objects of the following types: str, unicode, int,
            float, long, list, tuple, np. ndarray, dict,
            datetime.datetime, collections.OrderedDict
        group:
            HDF group or dataset in which to storedictionary of data.

    Returns
        nothing
    """
    for (key, value) in mydict.items():
        tvalue = type(value)
        if tvalue not in ALLOWED:
            if tvalue.__bases__[0] not in ALLOWED:
                raise TypeError('Unsupported metadata value type "%s"'
                                % tvalue)
        if isinstance(value, dict):
            subgroup = group.create_group(key)
            _dict2h5group(value, subgroup)
            continue
        elif isinstance(value, datetime):
            # convert datetime to a string, as there is no good
            # floating point format for datetimes before 1970.
            value = value.strftime(TIMEFMT)
        elif isinstance(value, list):
            value = _encode_list(value)
        elif isinstance(value, str):
            value = value.encode('utf8')
        else:
            pass
        group.attrs[key] = value


def _encode_list(value):
    for i, val in enumerate(value):
        if isinstance(val, list):
            value[i] = _encode_list(val)
        elif isinstance(val, datetime):
            value[i] = val.strftime('%Y-%m-%d %H:%M:%S.%f').encode('utf8')
        elif isinstance(val, str):
            value[i] = val.encode('utf8')
        elif isinstance(val, dict):
            raise TypeError('Lists cannot contain dictionaries.')
        else:
            value[i] = val
    return value


def _decode_list(value):
    outlist = []
    for i, val in enumerate(value):
        if isinstance(val, list):
            outlist.append(_decode_list(val))
        elif isinstance(val, bytes):
            tval = val.decode('utf8')
            try:
                outlist.append(HistoricTime.strptime(tval, TIMEFMT))
            except ValueError:
                outlist.append(tval)
        elif isinstance(val, dict):
            raise TypeError('Lists cannot contain dictionaries.')
        else:
            outlist.append(val)
    return outlist


def _convert(data):
    """
    Recursively convert the bytes elements in a dictionary's values, lists,
    and tuples into ascii.

    Args:
        data (dict): A dictionary.

    Returns;
        A copy of the dictionary with the byte strings converted to ascii.
    """
    if isinstance(data, bytes):
        return data.decode('utf8')
    if isinstance(data, dict):
        return dict(map(_convert, data.items()))
    if isinstance(data, tuple):
        return tuple(map(_convert, data))
    if type(data) in (np.ndarray, list):
        return list(map(_convert, data))
    return data


def _get_type_list(hdfobj, pattern):
    """
    Return the list of groups or datasets from hdf object matching a given
    pattern.

    Args:
        hdfobj: h5py File object.
        pattern (str): String to search. Examples could include "dictionary",
            "string","array", etc.

    Returns:
        list: List of un-mangled data set or group names.

    """
    names = []
    for group_name in hdfobj.keys():
        if group_name.startswith('__%s' % pattern):
            dname = group_name.replace('__%s_' % pattern, '').replace('__', '')
            names.append(dname)
    return names


def _drop_item(hdfobj, name, pattern):
    """
    Drop a group or dataset from the HDF object.

    Args:
        hdfobj: h5py File object.
        name: Un-mangled name of group or dataset to delete.
        pattern: The type of group or dataset to be deleted ("dictionary",
            "string","array", etc.)
    """

    group_name = '__%s_%s__' % (pattern, name)
    if group_name not in hdfobj:
        raise LookupError('%s %s not in %s'
                          % (pattern, name, self.getFileName()))
    del hdfobj[group_name]
