#!/usr/bin/python
import numpy as np
import zipfile
import tempfile
import sys
import io
import os.path

from impactutils.extern.openquake.geodetic import geodetic_distance
import pandas as pd

if sys.version_info.major == 3:
    import urllib.request as request
else:
    import urllib2 as request

GEONAME_URL = "http://download.geonames.org/export/dump/cities1000.zip"


def _fetchGeoNames():
    """
    Internal method to retrieve a cities1000.txt file from GeoNames.

    Returns:
        Path to local cities1000.txt file.
    """
    fh = request.urlopen(GEONAME_URL)
    data = fh.read()
    fh.close()
    f = io.BytesIO(data)
    myzip = zipfile.ZipFile(f)
    fdir = tempfile.mkdtemp()
    myzip.extract("cities1000.txt", fdir)
    myzip.close()
    return os.path.join(fdir, "cities1000.txt")


class Cities(object):
    """
    Handles loading and searching for cities.
    """

    REQFIELDS = ["name", "lat", "lon"]  # class variable

    def __init__(self, dataframe):
        """Construct a Cities object from a pandas DataFrame.
        Args:
            dataframe: pandas DataFrame,  where each row represents a city.
                Columns include:
                - name Name of the city (required).
                - lat Latitude of city (required).
                - lon Longitude of city (required).
                - pop Population of city (optional).
                - iscap Boolean indicating capital status (optional).
                - placement String indicating where city label
                  should be placed relative to city coordinates,
                   one of: E,W,N,S,NE,SE,SW,NW (optional).
                - xoff Longitude offset for label relative to city coordinates
                  (optional).
                - yoff Latitude offset for label relative to city coordinates
                  (optional).

        Raises:
            KeyError: When any of required columns are missing.

        Returns:
            Cities instance.
        """
        if len(set(dataframe.columns).intersection(set(self.REQFIELDS))) < 3:
            raise KeyError(f"Missing some of required keys: {self.REQFIELDS}")
        self._dataframe = dataframe.copy()

    # "magic" methods
    def __len__(self):
        """Return the number of cities in the Cities object.

        Returns:
            Number of cities in the Cities object.
        """
        return len(self._dataframe)

    def __repr__(self):
        """
        Return the string to represent the Cities instance.

        Returns:
            String representing Cities instance.
        """
        return str(self._dataframe)

    @classmethod
    def fromDefault(cls):
        """
        Load the cities data set from the text file included in the
        distribution for this module.

        Returns:
            Cities instance.
        """
        # where is this file?
        homedir = os.path.dirname(os.path.abspath(__file__))
        cityfile = os.path.join(homedir, "..", "data", "cities1000.txt")
        return cls.fromGeoNames(cityfile)

    @classmethod
    def fromGeoNames(cls, cityfile=None):
        """
        Load a cities data set from a GeoNames cities1000.txt file or by
        downloading it from GeoNames, then loading it.

        Args:
            cityfile: Path to cities1000.txt file from GeoNames, or None (file
                will be downloaded).

        Returns:
            Cities instance.
        """
        CAPFLAG1 = "PPLC"
        CAPFLAG2 = "PPLA"
        delete_folder = False
        if cityfile is None:
            cityfile = _fetchGeoNames()
            delete_folder = True

        mydict = {"name": [], "ccode": [], "lat": [], "lon": [], "iscap": [], "pop": []}
        f = open(cityfile, "rt", encoding="latin-1")
        for line in f.readlines():
            parts = line.split("\t")
            tname = parts[2].strip()
            if not tname:
                continue
            myvals = np.array([ord(c) for c in tname])
            if len((myvals > 127).nonzero()[0]):
                continue
            mydict["name"].append(tname)
            mydict["ccode"].append(parts[8].strip())
            mydict["lat"].append(float(parts[4].strip()))
            mydict["lon"].append(float(parts[5].strip()))
            capfield = parts[7].strip()
            iscap = (capfield == CAPFLAG1) or (capfield == CAPFLAG2)
            mydict["iscap"].append(iscap)
            mydict["pop"].append(int(parts[14].strip()))
        f.close()
        if delete_folder:
            fdir, bname = os.path.split(cityfile)
            os.remove(cityfile)
            os.rmdir(fdir)
        df = pd.DataFrame.from_dict(mydict)
        return cls(df)

    @classmethod
    def fromCSV(cls, csvfile):
        """Load data from a csv file

        Args:
            csvfile: CSV file containing city data, must have at least columns
                name,lat,lon.

        Returns:
            Cities instance
        """
        df = pd.read_csv(csvfile)
        return cls(df)

    def len(self):
        """Get the number of cities contained in this object.

        Returns:
            Number of cities contained in this object.
        """
        return len(self._dataframe)

    def save(self, filename):
        """Save City internal dataframe to CSV file.

        Args:
            filename: Output filename to save data to.

        Returns:
            None
        """
        self._dataframe.to_csv(filename)

    def sortByColumns(self, columns, ascending=True):
        """Sort list of cities by input column names.

        Args:
            columns: String name or list of names of any of the columns that
                are in the internal dataframe. See getColumns(). Only the
                required set of columns (see __init__ method) are guaranteed
                to be present, but subclasses of Cities may add more.
            ascending: Boolean indicating which direction values should be
                sorted.

        Raises:
            KeyError: When column(s) are not in the list of dataframe columns.
        """
        bad_columns = set(columns).difference(set(self._dataframe.columns()))
        if bad_columns:
            raise KeyError(
                f"Column(s) not in list of DataFrame columns: {str(bad_columns)}"
            )
        if pd.__version__ < "0.17.0":
            self._dataframe = self._dataframe.sort(columns=columns, ascending=ascending)
        else:
            self._dataframe = self._dataframe.sort_values(
                by=columns, ascending=ascending
            )

    def getColumns(self):
        """Return list of column names in internal data frame.

        Returns:
            List of column names in internal data frame.
        """
        return list(self._dataframe.columns)

    def limitByBounds(self, bounds):
        """Search for cities within a bounding box (xmin,xmax,ymin,ymax).

        Args:
            bounds: Sequence containing xmin,xmax,ymin,ymax (decimal degrees).

        Returns:
            New Cities instance containing smaller cities data set.
        """
        # TODO: figure out what to do with a meridian crossing?
        newdf = self._dataframe.copy()
        xmin, xmax, ymin, ymax = bounds
        newdf = newdf.loc[
            (newdf["lat"] >= ymin)
            & (newdf["lat"] <= ymax)
            & (newdf["lon"] >= xmin)
            & (newdf["lon"] <= xmax)
        ]
        return type(self)(newdf)

    def limitByRadius(self, lat, lon, radius):
        """Search for cities within a radius (km) around a central point.

        Args:
            lat: Central latitude coordinate (dd).
            lon: Central longitude coordinate (dd).
            radius: Radius (km) around which cities will be searched.

        Returns:
            New Cities instance containing smaller cities data set.
        """
        # TODO: figure out what to do with a meridian crossing?
        newdf = self._dataframe.copy()
        dist = geodetic_distance(
            lon, lat, self._dataframe["lon"], self._dataframe["lat"]
        )
        newdf["dist"] = dist
        newdf = newdf[newdf["dist"] <= radius]
        del newdf["dist"]
        return type(self)(newdf)

    def limitByPopulation(self, pop, minpop=0):
        """Search for cities above a certain population threshold.

        Args:
            pop: Population threshold.
            minpop: Population above which cities should be included.

        Raises:
            KeyError: When Cities instance does not contain population data.
            ValueError: When minpop >= pop.

        Returns:
            New Cities instance containing cities where population > pop.
        """
        if "pop" not in self._dataframe.columns:
            raise KeyError("Cities instance does not contain population " "information")
        if minpop >= pop:
            raise ValueError(
                "Minimum population must be less than " "population threshold."
            )
        newdf = self._dataframe.copy()
        newdf = newdf[newdf["pop"] >= pop]
        return type(self)(newdf)

    def limitByGrid(self, nx=2, ny=2, cities_per_grid=20):
        """
        Create a smaller Cities dataset by gridding cities, then limiting
        cities in each grid by population.

        Args:
            nx: Desired number of columns for grid.
            ny: Desired number of rows for grid.
            cities_per_cell: Maximum number of cities allowed per grid cell.

        Raises:
            KeyError: When Cities instance does not contain population data.

        Returns:
            New Cities instance containing cities limited by number in each
            grid cell.
        """
        if "pop" not in self._dataframe.columns:
            raise KeyError("Cities instance does not contain population " "information")
        xmin = self._dataframe["lon"].min()
        xmax = self._dataframe["lon"].max()
        ymin = self._dataframe["lat"].min()
        ymax = self._dataframe["lat"].max()
        dx = (xmax - xmin) / nx
        dy = (ymax - ymin) / ny
        newdf = None
        # start from the bottom left of our grid, and trim our cities.

        for i in range(0, ny):
            cellymin = ymin + (i * dy)
            cellymax = cellymin + dy
            for j in range(0, nx):
                cellxmin = xmin + (j * dx)
                cellxmax = cellxmin + dx
                tcities = self.limitByBounds((cellxmin, cellxmax, cellymin, cellymax))
                # older versions of pandas use a different sort function
                if pd.__version__ < "0.17.0":
                    tdf = tcities._dataframe.sort(columns="pop", ascending=False)
                else:
                    tdf = tcities._dataframe.sort_values(by="pop", ascending=False)
                tdf = tdf[0:cities_per_grid]
                if newdf is None:
                    newdf = tdf.copy()
                else:
                    newdf = pd.concat([newdf, tdf])
        return type(self)(newdf)

    def limitByName(self, cityname):
        """Find all cities that match a given cityname (or regular expression).

        Args:
            cityname: Input city name (i.e., "Los Angeles").

        Returns:
            Cities instance containing cities with names that match the input
            name/regular expression.
        """
        newdf = self._dataframe[self._dataframe.name.str.contains(cityname)]
        return type(self)(newdf)

    def getDataFrame(self):
        """Return a copy of the internal pandas DataFrame containing city data.

        Returns:
            pandas DataFrame at least containing columns 'name','lat','lon'
        """
        return self._dataframe.copy()

    def getBounds(self):
        """Return the bounds of the Cities dataset.

        Returns:
            Tuple containing (xmin, xmax, ymin, ymax).
        """
        # TODO: figure out meridian crossing??
        xmin = self._dataframe["lon"].min()
        xmax = self._dataframe["lon"].max()
        ymin = self._dataframe["lat"].min()
        ymax = self._dataframe["lat"].max()
        return (xmin, xmax, ymin, ymax)

    def getCities(self):
        """Return arrays of lat,lon,names from Cities DataFrame.

        Returns:
            tuple of (lat, lon, names) where each is a numpy array.
        """
        lat = self._dataframe["lat"].values
        lon = self._dataframe["lon"].values
        names = self._dataframe["name"].values
        return (lat, lon, names)

    def project(self, mbasemap):
        """Use a Basemap instance to project city lat/lon to projected x/y.

        Args:
            mbasemap: Basemap instance.
        """
        x, y = mbasemap(self._dataframe["lon"].values, self._dataframe["lat"].values)
        self._dataframe["x"] = x
        self._dataframe["y"] = y
