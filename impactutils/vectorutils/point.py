from impactutils.extern.openquake import geodetic

class Point(object):
    """Simple point class to contain lat/lon/depth values."""

    def __init__(self,longitude,latitude,depth=0):
        """Create a Point object.

        Args:
            longitude (float): Longitude of a point.
            latitude (float): Latitude of a point.
            depth (float): Depth (km) of a point.
        """
        self.longitude = longitude
        self.latitude = latitude
        self.depth = depth

    @property
    def x(self):
        """Access the longitude of a point.

        Returns:
            float: Longitude value.
            
        """
        return self.longitude

    @property
    def y(self):
        """Access the latitude of a point.

        Returns:
            float: Latitude value.
            
        """
        return self.latitude

    @property
    def z(self):
        """Access the depth of a point.

        Returns:
            float: Depth value.
            
        """
        return self.depth

    def azimuth(self,point):
        """Get the angle (in degrees) between two points.

        Args:
            point (Point): Point object.
        Returns:
            float: Azimuth angle in degrees between this Point and input Point.
        """
        return geodetic.azimuth(self.longitude, self.latitude,
                                point.longitude, point.latitude)
    
    
