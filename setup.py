from distutils.core import setup
import os.path
import versioneer

setup(name='earthquake-impact-utils',
      version=versioneer.get_version(),
      cmdclass=versioneer.get_cmdclass(),
      description='USGS Earthquake Impact Utilities',
      author='Mike Hearne',
      author_email='mhearne@usgs.gov',
      url='https://github.com/usgs/earthquake-impact-utils',
      package_data={
          'impactutils': [
              os.path.join('data', 'cities1000.txt')]
      },
      packages=['impactutils', 'impactutils.textformat',
                'impactutils.io', 'impactutils.colors',
                'impactutils.mapping',
                'impactutils.time',
                'impactutils.transfer',
                'impactutils.extern',
                'impactutils.vectorutils',
                'impactutils.extern.scp',
                'impactutils.extern.openquake',
                'impactutils.comcat']
)
