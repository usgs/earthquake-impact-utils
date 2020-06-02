# !/usr/bin/env python

# stdlib imports
from datetime import datetime
import os.path
import random
import string
import tempfile

# third party imports
import numpy as np
import pandas as pd
import pytz
import pytest

# local imports
from impactutils.io.smcontainers import \
    HDFContainerBase, ShakeMapContainerBase, ShakeMapOutputContainer


TIMEFMT = '%Y-%d-%m %H:%M:%S.%f'


def test_hdf_dictonaries():
    f, testfile = tempfile.mkstemp()
    os.close(f)
    try:
        container = HDFContainerBase.create(testfile)

        # before we put anything in here, let's make sure we get empty lists from
        # all of the methods that are supposed to return lists of stuff.
        assert container.getDictionaries() == []
        assert container.getArrays() == []
        assert container.getStrings() == []

        # test simple dictionary
        print('Test simple dictionary...')
        indict1 = {'name': 'Fred', 'age': 34,
                   'dob': datetime(1950, 1, 1, 23, 43, 12).strftime(TIMEFMT)}
        container.setDictionary('', 'person', indict1)
        outdict = container.getDictionary('', 'person')
        assert outdict == indict1

        # this should fail because we can't serialize datetimes to json.
        try:
            indict1 = {'name': 'Fred', 'age': 34,
                       'dob': datetime(1950, 1, 1, 23, 43, 12)}
            container.setDictionary('', 'person', indict1)
        except TypeError as te:
            print(f'Expected failure: {str(te)}')
            assert 1 == 1

        # test more complicated dictionary
        print('Test complex dictionary...')
        indict2 = {'names': ['Fred', 'Akyüz'], 'ages': [34, 33]}
        container.setDictionary('', 'people', indict2)
        outdict = container.getDictionary('', 'people')
        assert outdict == indict2

        # test getDictionaryNames()
        print('Test dictionary names...')
        names = container.getDictionaries()
        assert sorted(names) == sorted(['person', 'people'])

        # test dropping a dictionary
        container.dropDictionary('', 'person')
        assert container.getDictionaries() == ['people']

        # try closing container and reopening
        container.close()
        container2 = ShakeMapOutputContainer.load(testfile)
        assert container2.getDictionaries() == ['people']

        # test filename
        assert container2.getFileName() == testfile

        # test LookupError exception
        with pytest.raises(Exception) as a:
            container2.getDictionary('invalid', 'invalid')
        with pytest.raises(Exception) as a:
            container2.dropDictionary('invalid', 'invalid')

        # test datatype
        dt_invalid = container2.getDataType()
        assert dt_invalid == None
        with pytest.raises(Exception) as a:
            container2.setDataType('invalid')
        container2.setDataType('grid')
        with pytest.raises(Exception) as a:
            container2.setDataType('points')
        dt = container2.getDataType()
        assert dt == 'grid'

        # test metadata
        with pytest.raises(Exception) as a:
            container2.getMetadata()
        container2.setMetadata({'': 'test1'})
        # should replace the first
        container2.setMetadata({'': 'test2'})
        md = container2.getMetadata()
        assert md == {'': 'test2'}

        # test grids
        with pytest.raises(Exception) as a:
            container2.getIMTGrids('', '')
        container2.setIMTGrids('pga', [1, 2, 3], {"mean": "test"},
                               [0, 0, 0], {"std": "test"}, 'Larger')
        grid = container2.getIMTGrids('pga', 'Larger')
        target_grid = {'mean': np.array([1, 2, 3]),
                       'mean_metadata': {'mean': 'test'},
                       'std': np.array([0, 0, 0]),
                       'std_metadata': {'std': 'test'}}
        for key in target_grid.keys():
            if not isinstance(target_grid[key], str):
                np.testing.assert_array_equal(grid[key], target_grid[key])
            else:
                assert grid[key] == target_grid[key]
        with pytest.raises(Exception) as a:
            container2.getIMTGrids('pga', 'invalid')

        # test imt arrays (not valid because type is grid)
        with pytest.raises(Exception) as a:
            container2.setIMTArrays('pga', 'lons', 'lats', ids,
                                    'imt_mean', 'mean_metadata', 'imt_std',
                                    'std_metadata', 'component')
        with pytest.raises(Exception) as a:
            container2.getIMTArrays('pga', 'component')

        container2.close()
    except Exception:
        assert 1 == 2
    finally:
        os.remove(testfile)


def test_hdf_arrays():
    f, testfile = tempfile.mkstemp()
    os.close(f)
    try:
        container = HDFContainerBase.create(testfile)

        # test simple array, without compression
        print('Test simple array...')
        data = np.random.rand(4, 3)
        metadata = {'xmin': 54.1, 'xmax': 123.1}
        container.setArray('', 'testdata1', data,
                           metadata=metadata, compression=False)
        outdata, outmetadata = container.getArray('', 'testdata1')
        np.testing.assert_array_equal(outdata, data)
        assert outmetadata == metadata

        # test array with nans, and compression on
        print('Test nans array...')
        data = np.random.rand(4, 3)
        data[1, 1] = np.nan
        metadata = {'xmin': 54.1, 'xmax': 123.1}
        container.setArray('', 'testdata2', data,
                           metadata=metadata, compression=True)
        outdata, outmetadata = container.getArray('', 'testdata2')
        np.testing.assert_array_equal(outdata, data)
        assert outmetadata == metadata

        # test getArrayNames
        print('Test array names...')
        names = container.getArrays()
        assert sorted(names) == sorted(['testdata1', 'testdata2'])

        # drop an array
        container.dropArray('', 'testdata1')
        names = container.getArrays()
        assert names == ['testdata2']

        # close container, re-open
        container.close()
        container2 = HDFContainerBase.load(testfile)
        assert container2.getArrays() == ['testdata2']

        # test LookupError exception
        with pytest.raises(Exception) as a:
            container2.setArray('', 'testdata2', [1, 2, 3])
        with pytest.raises(Exception) as a:
            container2.getArray('invalid', 'invalid')

        container2.close()

    except Exception:
        assert 1 == 2
    finally:
        os.remove(testfile)


def test_hdf_strings():
    f, testfile = tempfile.mkstemp()
    os.close(f)
    try:
        container = HDFContainerBase.create(testfile)

        # test simple string
        print('Test simple string...')
        string1 = "These are the times that try men's souls."
        container.setString('', 'test_string1', string1)
        outstring = container.getString('', 'test_string1')
        assert outstring == string1

        # test unicode string
        print('Test unicode string...')
        string2 = "#SOURCE: Barka, A., H. S. Akyüz, E. Altunel, G. Sunal, Z. Çakir,"
        container.setString('', 'test_string2', string2)
        outstring = container.getString('', 'test_string2')
        assert outstring == string2

        # test getstrings
        print('Test string names...')
        names = container.getStrings()
        assert names == ['test_string1', 'test_string2']

        # drop string
        container.dropString('', 'test_string1')
        assert container.getStrings() == ['test_string2']

        # test a really big string
        sets = string.ascii_uppercase + string.digits + string.ascii_lowercase
        num_chars = 1000000
        print('Making a really big string...')
        big_string = ''.join(random.choice(sets) for _ in range(num_chars))
        container.setString('', 'big', big_string)
        big_string2 = container.getString('', 'big')
        assert big_string == big_string2

        # close container, re-open
        container.close()
        container2 = ShakeMapOutputContainer.load(testfile)
        assert container2.getStrings() == ['big', 'test_string2']

        # test LookupError exception
        with pytest.raises(Exception) as a:
            container2.getString('', 'invalid')
        with pytest.raises(Exception) as a:
            container2.dropString('', 'invalid')
        with pytest.raises(Exception) as a:
            container2.getConfig()

        # test rupture dictionaries
        with pytest.raises(Exception) as a:
            container2.setRuptureDict('invalid type')
        container2.setRuptureDict({'': 'test1'})
        # should replace the first
        container2.setRuptureDict({'': 'test2'})
        rup = container2.getRuptureDict()
        assert rup == {'': 'test2'}

        # test station dictionaries
        with pytest.raises(Exception) as a:
            container2.setStationDict('invalid type')
        container2.setStationDict({'': 'test1'})
        # should replace the first
        container2.setStationDict({'': 'test2'})
        stat = container2.getStationDict()
        assert stat == {'': 'test2'}

        # test version dictionaries
        container2.setVersionHistory({'': 'test1'})
        # should replace the first
        container2.setVersionHistory({'': 'test2'})
        version = container2.getVersionHistory()
        assert version == {'': 'test2'}

        # test point options
        with pytest.raises(Exception) as a:
            container2.dropIMT('pga')
        container2.setDataType('points')
        ids = np.array([n.encode("ascii", "ignore") for n in ['a', 'b', 'c']])
        container2.setIMTArrays('pga', np.array([3, 2, 1]), np.array([2, 4, 6]),
                                ids, np.array([1, 2, 3]),
                                {"mean": "test"}, np.array([0, 0, 0]),
                                {"std": "test"}, 'Larger')
        arrs = container2.getIMTArrays('pga', 'Larger')
        target_arrs = {'lons': np.array([3, 2, 1]),
                       'lats': np.array([2, 4, 6]),
                       'ids': np.array([b'a', b'b', b'c'], dtype='|S1'),
                       'mean': np.array([1, 2, 3]),
                       'mean_metadata': {'mean': 'test'},
                       'std': np.array([0, 0, 0]),
                       'std_metadata': {'std': 'test'}}
        for key in target_arrs.keys():
            if not isinstance(target_arrs[key], str):
                np.testing.assert_array_equal(arrs[key], target_arrs[key])
            else:
                assert arrs[key] == target_arrs[key]
        comps1 = container2.getComponents()
        np.testing.assert_array_equal(comps1, ['Larger'])
        comps2 = container2.getComponents('pga')
        np.testing.assert_array_equal(comps2, ['Larger'])
        container2.dropIMT('pga')
        comps = container2.getComponents('pga')
        np.testing.assert_array_equal(comps, [])
        # these are not valid because the type is points
        with pytest.raises(Exception) as a:
            container2.getIMTGrids('pga', 'component')
        with pytest.raises(Exception) as a:
            container2.setIMTGrids('pga', 'imt_mean', 'mean_metadata',
                                   'imt_std', 'std_metadata', 'component')

        container2.close()
    except Exception:
        assert 1 == 2
    finally:
        os.remove(testfile)


if __name__ == '__main__':
    test_hdf_dictonaries()
    test_hdf_arrays()
    test_hdf_strings()
