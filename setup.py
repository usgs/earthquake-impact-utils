from distutils.core import setup
import os.path

setup(name='earthquake-impact-utils',
      version='0.1dev',
      description='USGS Earthquake Impact Utilities',
      author='Mike Hearne',
      author_email='mhearne@usgs.gov',
      url='https://github.com/usgs/earthquake-impact-utils',
      packages=['earthquake-impact-utils','earthquake-impact-utils.testformat',
                'earthquake-impact-utils.io','earthquake-impact-utils.colors'],)
