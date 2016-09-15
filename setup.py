from distutils.core import setup
import os.path

setup(name='earthquake-impact-utils',
      version='0.1dev',
      description='USGS Earthquake Impact Utilities',
      author='Mike Hearne',
      author_email='mhearne@usgs.gov',
      url='https://github.com/usgs/earthquake-impact-utils',
      package_data = {'impactutils':[os.path.join('data', 'timezones.json')]},
      packages=['impactutils','impactutils.textformat',
                'impactutils.io','impactutils.colors',
                'impactutils.mapping','impactutils.time'],)
