#!/usr/bin/env python

import shutil
import tempfile
import os.path
import numpy as np
from xml.dom import minidom
from impactutils.io.table import read_excel, dataframe_to_xml
import pandas as pd


def test_write_xml():
    # where is this script?
    homedir = os.path.dirname(os.path.abspath(__file__))
    datadir = os.path.join(homedir, '..', 'data')
    complete_file = os.path.join(datadir, 'complete_pgm.xlsx')
    mmimin_file = os.path.join(datadir, 'minimum_mmi.xlsx')
    shakemap_file = os.path.join(datadir, 'shakemap.xlsx')
    tempdir = None
    try:
        tempdir = tempfile.mkdtemp()
        df, reference = read_excel(complete_file)
        xmlfile = os.path.join(tempdir, 'foo.xml')
        dataframe_to_xml(df, xmlfile, reference=reference)
        target1 = '<psa03 flag="0" value="5.1200"/>'
        target2 = '<station code="MX.XALA" lat="19.5299" lon="-96.9020" name="Veracruz" netid="MX" dist="594.0" intensity="1.7" source="National Seismic Service" elev="5.1">'
        target3 = '<pgv flag="0" value="0.8455"/>'
        target4 = '<comp name="H1" orientation="h">'
        target5 = '<psa03 flag="0" value="10.3070"/>'
        target6 = '<psa30 flag="0" value="2.0700"/>'
        target7 = '<psa10 flag="0" value="2.2230"/>'
        target8 = '<psa30 flag="0" value="1.8800"/>'
        target9 = '<station code="MX.ACAM" lat="20.0432" lon="-100.7168" name="Guanajuato" netid="MX" dist="913.1" intensity="0.7" source="National Seismic Service" elev="5.1">'
        target10 = 'station code="MX.ACP2" lat="16.8743" lon="-99.8865" name="Guerrero" netid'
        with open(xmlfile, 'r') as f:
            xmlstr = f.read()
        assert target1 in xmlstr
        assert target2 in xmlstr
        assert target3 in xmlstr
        assert target4 in xmlstr
        assert target5 in xmlstr
        assert target6 in xmlstr
        assert target7 in xmlstr
        assert target8 in xmlstr
        assert target9 in xmlstr
        assert target10 in xmlstr
        xmlfile = os.path.join(tempdir, 'bar.xml')
        df_mmimin, reference = read_excel(mmimin_file)
        dataframe_to_xml(df_mmimin, xmlfile, reference=reference)

        xmlfile = os.path.join(tempdir, 'shakemap.xml')
        df_shakemap, reference = read_excel(shakemap_file)
        dataframe_to_xml(df_shakemap, xmlfile, reference=reference)
        root = minidom.parse(xmlfile)
        stationlist = root.getElementsByTagName('stationlist')[0]
        station = stationlist.getElementsByTagName('station')[0]
        comp = station.getElementsByTagName('comp')[0]
        pga = comp.getElementsByTagName('pga')[0]
        assert station.getAttribute('code') == "I1.8226"
        assert comp.getAttribute('name') == 'H1'
        tvalue = float(pga.getAttribute('value'))
        np.testing.assert_almost_equal(tvalue, 0.1026)
        root.unlink()

    except Exception:
        raise AssertionError('Could not write XML file.')
    finally:
        if tempdir is not None:
            shutil.rmtree(tempdir)


def test_read_tables():
    homedir = os.path.dirname(os.path.abspath(
        __file__))  # where is this script?
    datadir = os.path.join(homedir, '..', 'data')

    ##########################################
    # these files should all read successfully
    ##########################################
    tmpdir = tempfile.mkdtemp()
    try:
        complete_file = os.path.join(datadir, 'complete_pgm.xlsx')
        df_complete, _ = read_excel(complete_file)
        np.testing.assert_almost_equal(df_complete['H1']['PGA'].sum(), 569.17)
        xmlfile = os.path.join(tmpdir, 'complete_pgm.xml')
        dataframe_to_xml(df_complete, xmlfile)

        pgamin_file = os.path.join(datadir, 'minimum_pga.xlsx')
        df_pgamin, _ = read_excel(pgamin_file)
        np.testing.assert_almost_equal(df_pgamin['UNK']['PGA'].sum(), 569.17)
        xmlfile = os.path.join(tmpdir, 'minimum_pga.xml')
        dataframe_to_xml(df_pgamin, xmlfile)

        mmimin_file = os.path.join(datadir, 'minimum_mmi.xlsx')
        df_mmimin, _ = read_excel(mmimin_file)
        np.testing.assert_almost_equal(
            df_mmimin['INTENSITY'].sum(), 45.199872273516036)
        xmlfile = os.path.join(tmpdir, 'minimum_mmi.xml')
        dataframe_to_xml(df_mmimin, xmlfile)

        missing_data_file = os.path.join(datadir, 'missing_rows.xlsx')
        df, _ = read_excel(missing_data_file)
        assert np.isnan(df['H1']['SA(0.3)'].iloc[3])
        xmlfile = os.path.join(tmpdir, 'missing_rows.xml')
        dataframe_to_xml(df, xmlfile)

        sm2xml_example = os.path.join(datadir, 'sm2xml_output.xlsx')
        df, _ = read_excel(sm2xml_example)
        np.testing.assert_almost_equal(
            df['HHZ']['PGA'].sum(), 150.82342541678645)
        xmlfile = os.path.join(tmpdir, 'sm2xml_output.xml')
        dataframe_to_xml(df, xmlfile)

    except Exception:
        assert 1 == 2
    finally:
        shutil.rmtree(tmpdir)

    ##########################################
    # these files should all fail
    ##########################################
    try:
        missing_file = os.path.join(datadir, 'missing_columns.xlsx')
        read_excel(missing_file)
        assert 1 == 2
    except KeyError:
        assert 1 == 1

    try:
        wrong_file = os.path.join(datadir, 'wrong_channels.xlsx')
        read_excel(wrong_file)
        assert 1 == 2
    except KeyError:
        assert 1 == 1

    try:
        nodata_file = os.path.join(datadir, 'no_data.xlsx')
        read_excel(nodata_file)
        assert 1 == 2
    except KeyError:
        assert 1 == 1

    try:
        emptyrow_file = os.path.join(datadir, 'empty_row.xlsx')
        read_excel(emptyrow_file)
        assert 1 == 2
    except IndexError:
        assert 1 == 1

    try:
        noref_file = os.path.join(datadir, 'no_reference.xlsx')
        read_excel(noref_file)
        assert 1 == 2
    except KeyError:
        assert 1 == 1


def test_dataframe_to_xml():
    homedir = os.path.dirname(os.path.abspath(
        __file__))  # where is this script?
    datadir = os.path.join(homedir, '..', 'data')
    amps_output = os.path.join(datadir, 'amps.csv')
    df = pd.read_csv(amps_output)
    outdir = tempfile.mkdtemp()
    try:
        xmlfile = os.path.join(outdir, 'foo_dat.xml')
        dataframe_to_xml(df, xmlfile)
        # HNN,psa10,0.0107
        root = minidom.parse(xmlfile)
        comps = root.getElementsByTagName('comp')
        for comp in comps:
            if comp.getAttribute('name') == 'HNN':
                psa10 = comp.getElementsByTagName('psa10')[0]
                value = float(psa10.getAttribute('value'))
                assert value == 0.0107
    except Exception:
        assert 1 == 2
    finally:
        shutil.rmtree(outdir)


# Use DYFI raw data and attempt to create a valid
# Shakemap input XML.
def test_read_dyfi():
    homedir = os.path.dirname(os.path.abspath(
        __file__))  # where is this script?
    datadir = os.path.join(homedir, '..', 'data')
    dyfi_file = os.path.join(datadir, 'example_dyfi.csv')
    df = pd.read_csv(dyfi_file)
    np.testing.assert_almost_equal(df['INTENSITY_STDDEV'].sum(), 1.472)
    np.testing.assert_almost_equal(df['NRESP'].sum(), 25)

    outdir = tempfile.mkdtemp()
    try:
        xmlfile = os.path.join(outdir, 'dyfi_dat.xml')
        dataframe_to_xml(df, xmlfile)
        root = minidom.parse(xmlfile)
        stations = root.getElementsByTagName('station')
        for station in stations:
            assert float(station.getAttribute('intensity')) > 1
            assert float(station.getAttribute('intensity_stddev')) > 0.1
            assert int(station.getAttribute('nresp')) > 1

    except Exception:
        assert 1 == 2
    finally:
        shutil.rmtree(outdir)


if __name__ == '__main__':
    test_read_dyfi()
    test_write_xml()
    test_read_tables()
    test_dataframe_to_xml()
