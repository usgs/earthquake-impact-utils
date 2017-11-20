#!/bin/bash

VENV=impact
PYVER=3.5

# Is conda installed?
conda=$(which conda)
if [ ! "$conda" ] ; then
    wget https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh \
        -O miniconda.sh;
    bash miniconda.sh -f -b -p $HOME/miniconda
    export PATH="$HOME/miniconda/bin:$PATH"
fi

conda update -q -y conda
conda config --prepend channels conda-forge

DEPARRAY=(numpy=1.11\
          matplotlib=2.0.2\
          h5py=2.7.0 \
          cartopy=0.15.1\
          pandas=0.20.3\
          fiona=1.7.8\
          shapely=1.5.17 \
          pytest=3.2.0 \
          pytest-cov=2.5.1 \
          pytest-mpl=0.7 \
          pycrypto=2.6.1 \
          paramiko=2.1.2 \
          beautifulsoup4=4.6.0)

# Is the Travis flag set?
travis=0
while getopts t FLAG; do
  case $FLAG in
    t)
      travis=1
      ;;
  esac
done

# Append additional deps that are not for Travis CI
if [ $travis == 0 ] ; then
    DEPARRAY+=(ipython=6.1.0 \
	       spyder=3.2.1 \
	       jupyter=1.0.0 \
	       seaborn=0.8.0 \
	       sphinx=1.6.3)
fi


# Turn off whatever other virtual environment user might be in
source deactivate

# Remove any previous virtual environments called shakelib2
CWD=`pwd`
cd $HOME;
conda remove --name $VENV --all -y
cd $CWD

# Create a conda virtual environment
echo "Creating the $VENV virtual environment"
echo "with the following dependencies:"
echo ${DEPARRAY[*]}
conda create --name $VENV -y python=$PYVER ${DEPARRAY[*]}

# Activate the new environment
echo "Activating the $VENV virtual environment"
source activate $VENV

# Install psutil
echo "Installing psutil..."
conda install -y psutil

# OpenQuake v2.5.0
echo "Downloading OpenQuake v2.5.0..."
curl --max-time 60 --retry 3 -L \
    https://github.com/gem/oq-engine/archive/v2.5.0.zip -o openquake.zip
pip -q install --no-deps openquake.zip
rm openquake.zip

# This package
echo "Installing impact-utils..."
pip install -e .

# Tell the user they have to activate this environment
echo "Type 'source activate $VENV' to use this new virtual environment."
