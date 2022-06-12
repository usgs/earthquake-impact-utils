#!/bin/bash


unamestr=`uname`
if [ "$unamestr" == 'Linux' ]; then
    prof=~/.bashrc
    mini_conda_url=https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh
    matplotlibdir=~/.config/matplotlib
    env_file=environment_linux.yml
elif [ "$unamestr" == 'FreeBSD' ] || [ "$unamestr" == 'Darwin' ]; then
    prof=~/.bash_profile
    mini_conda_url=https://repo.continuum.io/miniconda/Miniconda3-latest-MacOSX-x86_64.sh
    matplotlibdir=~/.matplotlib
    env_file=environment_osx.yml
else
    echo "Unsupported environment. Exiting."
    exit
fi

source $prof

VENV=impact
CC_PKG=c-compiler
openquake_deps=0

# create a matplotlibrc file with the non-interactive backend "Agg" in it.
if [ ! -d "$matplotlibdir" ]; then
    mkdir -p $matplotlibdir
fi
matplotlibrc=$matplotlibdir/matplotlibrc
if [ ! -e "$matplotlibrc" ]; then
    echo "backend : Agg" > "$matplotlibrc"
    echo "NOTE: A non-interactive matplotlib backend (Agg) has been set for this user."
elif grep -Fxq "backend : Agg" $matplotlibrc ; then
    :
elif [ ! grep -Fxq "backend" $matplotlibrc ]; then
    echo "backend : Agg" >> $matplotlibrc
    echo "NOTE: A non-interactive matplotlib backend (Agg) has been set for this user."
else
    sed -i '' 's/backend.*/backend : Agg/' $matplotlibrc
    echo "###############"
    echo "NOTE: $matplotlibrc has been changed to set 'backend : Agg'"
    echo "###############"
fi


# Is conda installed?
conda --version
if [ $? -ne 0 ]; then
    echo "No conda detected, installing miniconda..."

    curl -L $mini_conda_url -o miniconda.sh;
    echo "Install directory: $HOME/miniconda"

    bash miniconda.sh -f -b -p $HOME/miniconda

    # Need this to get conda into path
    . $HOME/miniconda/etc/profile.d/conda.sh
else
    echo "conda detected, installing $VENV environment..."
fi


openquake_list=(
      "decorator>=4.3"
      "django>=3.2"
      "requests>=2.20"
      "setuptools"
      "toml"
)

# Choose an environment file based on platform
# only add this line if it does not already exist
grep "/etc/profile.d/conda.sh" $prof
if [ $? -ne 0 ]; then
    echo ". $_CONDA_ROOT/etc/profile.d/conda.sh" >> $prof
fi

package_list=(
    "cartopy=0.20.2"
    "cython>=0.29.23"
    "fiona>=1.8.13"
    "h5py>=2.10.0"
    "ipython"
    "jupyter"
    "lxml>=3.5"
    "matplotlib>=3.5"
    "numpy=1.21"
    "obspy>=1.2.2"
    "openpyxl>=3.0"
    "openssl=1.1.1"
    "pandas>=1.4.2"
    "paramiko>=2.8.1"
    "pip"
    "proj=8.2.0"
    "ps2ff>=1.5.2"
    "psutil>=5.8.0"
    "pyproj>=3.3.0"
    "pytest>=6.2.4"
    "pytest-cov>=2.12.1"
    "python>=3.8"
    "$CC_PKG"
    "scipy>=1.8.1"
    "shapely>=1.8.0"
    "xlrd>=2.0.1"
)

echo "Installing mamba from conda-forge"

conda install mamba -y -n base -c conda-forge

# Start in conda base environment
echo "Activate base virtual environment"
conda activate base

# Remove existing environment if it exists
conda remove -y -n $VENV --all
conda clean -y --all

if [ $openquake_deps == 1 ]; then
    package_list=( "${package_list[@]}" "${openquake_list[@]}" )
    echo ${package_list[*]}
fi

# Create a conda virtual environment
conda config --add channels 'defaults'
conda config --add channels 'conda-forge'
conda config --set channel_priority flexible
# conda config --set channel_priority strict
# conda config --set channel_priority disabled

echo "Creating the $VENV virtual environment:"
mamba create -y -n $VENV ${package_list[*]}

# Bail out at this point if the conda create command fails.
# Clean up zip files we've downloaded
if [ $? -ne 0 ]; then
    echo "Failed to create conda environment.  Resolve any conflicts, then try again."
    exit
fi


# Activate the new environment
echo "Activating the $VENV virtual environment"
conda activate $VENV

# upgrade pip, mostly so pip doesn't complain about not being new...
pip install --upgrade pip

# Install OQ from github to get NGA East since it isn't in a release yet.
echo "Installing OpenQuake from github..."
pip install --upgrade --no-dependencies https://github.com/gem/oq-engine/archive/engine-3.12.zip
if [ $? -ne 0 ];then
    echo "Failed to pip install OpenQuake. Exiting."
    exit 1
fi

# Need this to get around the fiona circular import error.
mamba install gdal=3.4.2 -c conda-forge -y

# This package
echo "Installing impactutils..."
pip install -e .

# Tell the user they have to activate this environment
echo "Type 'conda activate $VENV' to use this new virtual environment."
