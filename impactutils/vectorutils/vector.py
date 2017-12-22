#!/usr/bin/env python

import numpy as np
from .point import Point
from .ecef import latlon2ecef, ecef2latlon


class Vector(object):
    """
    Three-dimensional vector object, stored as three floats of x,y,z.

    Todo:
        - Optimize/vectorize calculations like dot/cross for arrays of
          vectors.
    """

    def __init__(self, x, y, z):
        """
        Create three dimensional vector object in cartesian space.

        Args:
            x: x coordinate (float).
            y: y coordinate (float).
            z: z coordinate (float).

        Returns:
            Vector object containing x,y,z coordinates as floats.
        """
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)

    @classmethod
    def fromPoint(cls, oqpoint):
        """
        Class method which allows user to create a Vector from a GEM Hazardlib
        Point object.  The Point lat, lon, depth values are converted to
        Earth-Centered-Earth-Fixed (ECEF) cartesian coordinates.

        Args:
            oqpoint: Point object.

        Returns:
            A Vector object.
        """
        x, y, z = latlon2ecef(
            oqpoint.latitude, oqpoint.longitude, oqpoint.depth)
        return Vector(x, y, z)

    @classmethod
    def fromTuple(cls, a):
        """
        Class method which allows user to create a Vector from an x/y/z tuple.

        Args:
            a: an x/y/z tuple.

        Returns:
            A Vector object.
        """
        x, y, z = a
        return Vector(x, y, z)

    def __add__(self, other):
        """
        Add another Vector object to this one (x+x,y+y,z+z).

        Args:
            other: Another Vector object

        Returns:
            A third Vector object.

        Raises:
            TypeError: If other is not a Vector object.
        """
        if not isinstance(other, Vector):
            raise TypeError("Cannot add Vector and %s objects" % type(other))
        return Vector(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other):
        """
        Subtract another Vector object from this one (x+x,y+y,z+z).

        Args:
            other: Another Vector object.

        Returns:
            A third Vector object.

        Raises:
            TypeError: If other is not a Vector object.
        """
        if not isinstance(other, Vector):
            raise TypeError(
                "Cannot subtract Vector and %s objects" %
                type(other))
        return Vector(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, length):
        """
        Multiply the Vector by a scalar, changing it's length.

        Args:
            length: A scalar number.

        Returns:
            A Vector object.

        Raises:
            TypeError: when length is not a number.
        """
        try:
            length = float(length)
        except ValueError:
            raise TypeError(
                "Cannot multiply Vector and %s objects" %
                type(length))
        return Vector(self.x * length, self.y * length, self.z * length)

    def __rmul__(self, length):
        """
        Multiply the Vector by a scalar, changing it's length.

        Args:
            length: A scalar number.

        Returns:
            A Vector object.

        Raises:
            TypeError: When length is not a number.
        """
        try:
            length = float(length)
        except ValueError:
            raise TypeError(
                "Cannot multiply Vector and %s objects" %
                type(length))
        return Vector(self.x * length, self.y * length, self.z * length)

    def __eq__(self, other):
        """
        Check equality between this Vector and another.

        Args:
            other: Another Vector object.

        Returns:
            True or False.

        Raises:
            TypeError: If other is not a Vector object.
        """
        if not isinstance(other, Vector):
            raise TypeError(
                "Cannot compare Vector and %s objects" %
                type(other))
        if other.x == self.x and other.y == self.y and other.z == self.z:
            return True
        return False

    def distance(self, other):
        """
        Calculate distance between this Vector and another.

        Args:
            other: Another Vector object.

        Returns:
            float distance between Vectors.

        Raises:
            TypeError: If other is not a Vector object.
        """
        if not isinstance(other, Vector):
            raise TypeError(
                "Cannot calculate distance between Vector and %s objects" %
                type(other))
        return np.sqrt((self.x - other.x)**2 + (self.y - other.y)
                       ** 2 + (self.z - other.z)**2)

    def cross(self, other):
        """
        Calculate cross product between this Vector and another.

        Args:
            other: Another Vector object.

        Returns:
            a Vector object.

        Raises:
            TypeError: If other is not a Vector object.
        """
        if not isinstance(other, Vector):
            raise TypeError(
                "Cannot calculate cross product between Vector and %s objects"
                % type(other))
        cp = np.cross(self.getArray(), other.getArray())
        return Vector(cp[0], cp[1], cp[2])

    def dot(self, other):
        """
        Calculate dot product between this Vector and another.

        Args:
            other: Another Vector object.

        Returns:
           a float dot product.

        Raises:
            TypeError: If other is not a Vector object.
        """
        if not isinstance(other, Vector):
            raise TypeError(
                "Cannot calculate cross product between Vector and %s objects"
                % type(other))
        dp = np.dot(self.getArray(), other.getArray())
        return dp

    def getArray(self):
        """
        Returns:
            3 element Numpy array of [x,y,z]
        """
        return np.array((self.x, self.y, self.z))

    def getTuple(self):
        """
        Returns:
            3 element tuple of (x,y,z)
        """
        return (self.x, self.y, self.z)

    def norm(self):
        """
        Returns:
            Normalized Vector.
        """
        length = np.sqrt(self.x**2 + self.y**2 + self.z**2)
        x = self.x / length
        y = self.y / length
        z = self.z / length
        return Vector(x, y, z)

    def mag(self):
        """
        Returns:
            Length of Vector (float).
        """
        length = np.sqrt(self.x**2 + self.y**2 + self.z**2)
        return length

    def toPoint(self):
        """
        Convert the Vector to a Point object, after translating
        back to lat, lon, depth.

        Returns:
            Point: A Point object.
        """
        lat, lon, dep = ecef2latlon(self.x, self.y, self.z)
        return Point(lon, lat, dep)

    def __repr__(self):
        """
        String representation of Vector.
        """
        return '<x=%.4f,y=%.4f,z=%.4f>' % (self.x, self.y, self.z)
