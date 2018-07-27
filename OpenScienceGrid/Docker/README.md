<img src='../OSG_logo.png' align=right height=110>
<img src='docker.png' align=right height=110>

Brian Blaylock  
July 27, 2018  

# My Docker Image
## https://hub.docker.com/r/blaylockbk/miniconda3_osg/

# How I created my Docker container for the Open Science Grid

Rather than building from a dockerfile, I created this Docker image interactively.

Preparatory steps:

1. Install Docker for Windows
2. Start Docker
3. Open PowerShell

Get the miniconda3 Docker image

    > docker pull continuumio/miniconda3

List images available. You should see the one we just pulled.

    > docker images

Update Docker image interactively. 
- [Look Here!](https://developer.basespace.illumina.com/docs/content/documentation/native-apps/manage-docker-image)
- [And Here!](https://support.opensciencegrid.org/support/solutions/articles/12000024676-docker-and-singularity-containers) for more info.

In Windows PowerShell, get the ID of the image and attach the ID

    > $ID = docker run -i -t -d continuumio/miniconda3 /bin/bash
    > docker attach $ID

That last command put us inside the container. Now lets get things we need set up.

Run some updates and installs:
    
    /# apt-get update
    /# apt-get install unzip
    /# apt-get install zip
    /# apt-get install vim
    /# pip install --upgrade pip

Install some python packages with `conda`:

    /# conda install -c conda-forge numpy
    /# conda install -c conda-forge matplotlib
    /# conda install -c conda-forge pygrib
    /# conda install -c conda-forge h5py
    /# conda install -c conda-forge netcdf4

Install `rclone` from binary: https://rclone.org/install/

    curl -O https://downloads.rclone.org/rclone-current-linux-amd64.zip
    unzip rclone-current-linux-amd64.zip
    cd rclone-*-linux-amd64
    cp rclone /usr/bin/
    chown root:root /usr/bin/rclone
    chmod 755 /usr/bin/rclone

Install `globus-cli` with `pip`:
	
    pip install globus-cli

Install `wgrib2`: [Look Here!](http://www.cpc.ncep.noaa.gov/products/wesley/wgrib2/compile_questions.html).

    /# apt-get install gcc
    /# apt-get install gfortran
    /# apt-get install make
    /# wget ftp://ftp.cpc.ncep.noaa.gov/wd51we/wgrib2/wgrib2.tgz
    /# tar -xzvf wgrib2.tgz
    /# cd grib2
    /# export CC=gcc
    /# export FC=gfortran
    /# make
    /# wgrib2/wgrib2 -config
    /# cd wgrib2
    /# cp wgrib2 /usr/bin/
    /# chown root:root /usr/bin/wgrib2
    /# chmod 755 /usr/bin/wgrib2
    /# cd /
    /# rm -r wgrib2.tgz
    /# rm -r grib2

Prepare mount for `/cvmfs`, in case we need it later:

    /# mkdir -p /cvmfs

Exit the container:

    /# exit

Commit the changes to our image:

    > docker commit $ID continuumio/miniconda3

Make sure the software was saved in the container by running the image:

    > docker run -i -t continuumio/miniconda3 /bin/bash

After trying `pygrib` and other things, exit out of the container and push the changes to Docker hub. Before you can push to Docker hub, go to [Docker Hub](https://hub.docker.com/) and create a new repository. Mine is named `blaylockbk/miniconda3_osg`.

Back in PowerShell, rename the image:

    > docker tag continuumio/minioconda3 blaylockbk/miniconda3_osg

Login to Docker and push the Docker image to Docker Hub:

    > docker login
    Username:
    Password:
    > docker push blaylockbk/miniconda3_osg

After pushing the Docker image, I contacted OSG support and they did the rest to get it on the OSG cvmfs.

---

## Using this container on OSG
The people at OSG convert the Docker container to a Singularity container. You can test your script in the container with 

    singularity shell /cvmfs/singularity.opensciencegrid.org/opensciencegrid/miniconda3_osg:latest/

**Warning: Exit the Singularity container before you submit jobs to `condor`!**

In your submit script, set the following:

    requirements = HAS_SINGULARITY == True
    +SingularityImage = "/cvmfs/singularity.opensciencegrid.org/opensciencegrid/miniconda3_osg:latest/"

---

**Note:** When using matplotlib in this image, use the `Agg` backend. 

    import matplotlib as mpl
    mpl.use('Agg')
    import matplotlib.pyplot as plt