#!/usr/bin/env python


from datetime import datetime
import tempfile
import string
import os.path
import random

import numpy as np
import pandas as pd

from impactutils.io.container import HDFContainer

TIMEFMT = '%Y-%d-%m %H:%M:%S.%f'


def test_hdf_dictonaries():
    f, testfile = tempfile.mkstemp()
    os.close(f)
    try:
        container = HDFContainer.create(testfile)

        # test simple dictionary
        print('Test simple dictionary...')
        indict1 = {'name': 'Fred', 'age': 34,
                   'dob': datetime(1950, 1, 1, 23, 43, 12).strftime(TIMEFMT)}
        container.setDictionary('person', indict1)
        outdict = container.getDictionary('person')
        assert outdict == indict1

        # this should fail because we can't serialize datetimes to json.
        try:
            indict1 = {'name': 'Fred', 'age': 34,
                       'dob': datetime(1950, 1, 1, 23, 43, 12)}
            container.setDictionary('person', indict1)
        except TypeError as te:
            print('Expected failure: %s' % str(te))
            assert 1 == 1

        # test more complicated dictionary
        print('Test complex dictionary...')
        indict2 = {'names': ['Fred', 'Akyüz'], 'ages': [34, 33]}
        container.setDictionary('people', indict2)
        outdict = container.getDictionary('people')
        assert outdict == indict2

        # test getDictionaryNames()
        print('Test dictionary names...')
        names = container.getDictionaries()
        assert sorted(names) == sorted(['person', 'people'])

        # test dropping a dictionary
        container.dropDictionary('person')
        assert container.getDictionaries() == ['people']

        # try closing container and reopening
        container.close()
        container2 = HDFContainer.load(testfile)
        assert container2.getDictionaries() == ['people']

    except Exception:
        assert 1 == 2
    finally:
        os.remove(testfile)


def test_hdf_lists():
    f, testfile = tempfile.mkstemp()
    os.close(f)
    try:
        container = HDFContainer.create(testfile)

        # test setting a list of strings
        inlist = ['one', 'two', 'three']
        container.setList('test_list1', inlist)
        assert container.getList('test_list1') == inlist

        # test setting a list of numbers
        inlist = [5.4, 1.2, 3.4]
        container.setList('test_list2', inlist)
        assert container.getList('test_list2') == inlist

        # test getlists
        assert sorted(container.getLists()) == [
            'test_list1', 'test_list2']

        # test setting a list with dictionaries in it
        inlist = [{'a': 1}, {'b': 2}]
        container.setList('test_list3', inlist)

        # drop a list
        container.dropList('test_list1')
        assert sorted(container.getLists()) == ['test_list2', 'test_list3']

        # close container, re-open
        container.close()
        container2 = HDFContainer.load(testfile)
        assert sorted(container2.getLists()) == ['test_list2', 'test_list3']

    except Exception:
        assert 1 == 2
    finally:
        os.remove(testfile)


def test_hdf_arrays():
    f, testfile = tempfile.mkstemp()
    os.close(f)
    try:
        container = HDFContainer.create(testfile)

        # test simple array, without compression
        print('Test simple array...')
        data = np.random.rand(4, 3)
        metadata = {'xmin': 54.1, 'xmax': 123.1}
        container.setArray('testdata1', data, metadata, compression=False)
        outdata, outmetadata = container.getArray('testdata1')
        np.testing.assert_array_equal(outdata, data)
        assert outmetadata == metadata

        # test array with nans, and compression on
        print('Test nans array...')
        data = np.random.rand(4, 3)
        data[1, 1] = np.nan
        metadata = {'xmin': 54.1, 'xmax': 123.1}
        container.setArray('testdata2', data, metadata, compression=True)
        outdata, outmetadata = container.getArray('testdata2')
        np.testing.assert_array_equal(outdata, data)
        assert outmetadata == metadata

        # test getArrayNames
        print('Test array names...')
        names = container.getArrays()
        assert sorted(names) == sorted(['testdata1', 'testdata2'])

        # drop an array
        container.dropArray('testdata1')
        names = container.getArrays()
        assert names == ['testdata2']

        # close container, re-open
        container.close()
        container2 = HDFContainer.load(testfile)
        assert container2.getArrays() == ['testdata2']

    except Exception:
        assert 1 == 2
    finally:
        os.remove(testfile)


def test_hdf_strings():
    f, testfile = tempfile.mkstemp()
    os.close(f)
    try:
        container = HDFContainer.create(testfile)

        # test simple string
        print('Test simple string...')
        string1 = "These are the times that try men's souls."
        container.setString('test_string1', string1)
        outstring = container.getString('test_string1')
        assert outstring == string1

        # test unicode string
        print('Test unicode string...')
        string2 = "#SOURCE: Barka, A., H. S. Akyüz, E. Altunel, G. Sunal, Z. Çakir,"
        container.setString('test_string2', string2)
        outstring = container.getString('test_string2')
        assert outstring == string2

        # test getstrings
        print('Test string names...')
        names = container.getStrings()
        assert names == ['test_string1', 'test_string2']

        # drop string
        container.dropString('test_string1')
        assert container.getStrings() == ['test_string2']

        # test a really big string
        sets = string.ascii_uppercase + string.digits + string.ascii_lowercase
        num_chars = 1000000
        print('Making a really big string...')
        big_string = ''.join(random.choice(sets) for _ in range(num_chars))
        container.setString('big', big_string)
        big_string2 = container.getString('big')
        assert big_string == big_string2

        # close container, re-open
        container.close()
        container2 = HDFContainer.load(testfile)
        assert container2.getStrings() == ['big', 'test_string2']

    except Exception:
        assert 1 == 2
    finally:
        os.remove(testfile)


def test_hdf_dataframes():
    f, testfile = tempfile.mkstemp()
    os.close(f)
    try:
        container = HDFContainer.create(testfile)

        # test pandas dataframe
        print('Test dataframe...')
        d = {'Time': [datetime(1900, 1, 1), datetime(2000, 1, 1)],
             'ID': ['thing1', 'thing2'],
             'Number': np.array([12.34, 25.67])}
        df = pd.DataFrame(d)
        container.setDataFrame('testframe1', df)
        outdf = container.getDataFrame('testframe1')
        assert outdf['Number'].sum() == df['Number'].sum()
        assert outdf['Time'][0] == df['Time'][0]

        # test another dataframe
        df2 = pd.DataFrame(data=[4, 5, 6, 7], index=range(0, 4), columns=['A'])
        container.setDataFrame('testframe2', df2)
        outdf = container.getDataFrame('testframe2')
        outdf['A'].sum() == df2['A'].sum()

        # test getdataframes
        assert sorted(container.getDataFrames()) == [
            'testframe1', 'testframe2']

        # drop a dataframe
        container.dropDataFrame('testframe1')
        assert container.getDataFrames() == ['testframe2']

        # close container, re-open
        container.close()
        container2 = HDFContainer.load(testfile)
        assert container2.getDataFrames() == ['testframe2']

    except Exception:
        assert 1 == 2
    finally:
        os.remove(testfile)


if __name__ == '__main__':
    test_hdf_dictonaries()
    test_hdf_lists()
    test_hdf_arrays()
    test_hdf_strings()
    test_hdf_dataframes()
