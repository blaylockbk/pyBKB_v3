# How my Docker container for the Open Science Grid was created

Initial Steps

1. Install Docker for Windows.
2. Start Docker
3. Open PowerShell


Get miniconda3 Docker image

    > docker pull continuumio/miniconda3

Update Docker image interactively. [Look Here!](https://developer.basespace.illumina.com/docs/content/documentation/native-apps/manage-docker-image)

In Windows PowerShell store the ID of the image and attach the ID

    > $ID = docker run -i -t -d continuumio/miniconda3 /bin/bash
    > docker attach $ID

That last command put us in the container. Let's run some updates:
    
    /# apt-get update
    /# apt-get install unzip
    /# apt-get install zip

Install a python package:

    /# conda install -c conda-forge pygrib

Installed rclone from binary: https://rclone.org/install/

    curl -O https://downloads.rclone.org/rclone-current-linux-amd64.zip
    unzip rclone-current-linux-amd64.zip
    cd rclone-*-linux-amd64
    cp rclone /usr/bin/
    chown root:root /usr/bin/rclone
    chmod 755 /usr/bin/rclone

<strike>Installed globus-cli (didn't work)
	pip install globus</strike>

Exit the container

    /# exit

Commit the changes to our image

    > docker commit $ID continuumio/miniconda3

Make sure the software was saved in the container. Enter the container again while on my Surface3 C:\Users\blaylockbk:

    > docker run -i -t continuumio/miniconda3 /bin/bash

After trying pygrib and other things, exit out of the container and push the changes to Docker hub. Before you can push to Docker hub, go to hub.docker.com and create a new repository named `blaylockbk/miniconda3_osg`.

Back in PowerShell, rename the image:

    > docker tag continuumio/minioconda3 blaylockbk/miniconda3_osg

Push the docker image

    > docker login
    Username:
    Password:
    > docker push blaylockbk/miniconda3_osg