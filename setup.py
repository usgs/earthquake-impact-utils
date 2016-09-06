from distutils.core import setup
import os.path

setup(name='impactutils',
      version='0.1dev',
      description='USGS Earthquake Impact Utilities',
      author='Mike Hearne',
      author_email='mhearne@usgs.gov',
      url='https://github.com/usgs/earthquake-impact-utils',
      packages=['impactutils','impactutils.textformat',
                'impactutils.io','impactutils.colors',
                'impactutils.mapping'],)
