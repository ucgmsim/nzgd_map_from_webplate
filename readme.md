## Introduction

This repository contains the source code for the `nzgd_map` package. This is a web application
that enables access to analysis-ready data products derived from data hosted on the New Zealand Geotechnical 
Database (NZGD). This repository also contains files for building a Docker image that can be used to run the
`nzgd_map` package in a containerized environment.

## Installation

### Installing outside a Docker container

#### Installing an uneditable version

To install an uneditable version of `nzgd_map` outside a Docker container, simply enter the following 
command in a terminal:

* `pip install "git+https://github.com/ucgmsim/nzgd_map"` 

#### Installing an editable version

To install an editable version of `nzgd_map` outside a Docker container, enter the commands below in a terminal:

* Change to the directory that you want to clone the repository to
    * e.g., `cd /home/username/src/` 
* Clone the repository from GitHub
    * `git clone git@github.com:ucgmsim/nzgd_map.git`

* Install the package in editable mode
    * `cd nzgd_map`
    * `pip install -e .`

### Installing inside a Docker container

To install the `nzgd_map` package inside a Docker container, use the files in the `docker` folder 
and enter the following commands in a terminal. For more information about the files in the `docker` folder,
refer to the relevant section below.

* Open a terminal and change to the `docker` folder in the repository
    * e.g., `cd /home/username/src/nzgd_map/docker`
* Build the Docker image (which includes the `nzgd_map` package due to a pip install instruction in `Dockerfile`). 
Also note that `earthquakesuc` is our Docker Hub username.
    * If this is the first time building the image, or the `nzgd_map` package has not changed, run the following command:
        * `sudo docker build -t earthquakesuc/nzgd_map .` 
    * If this is not the first time building the image, and the `nzgd_map` package has changed, run with `--no-cache` 
  so the image will be built with the latest version of the `nzgd_map` package:
    * `sudo docker build --no-cache -t earthquakesuc/nzgd_map .`

* Push the image to Docker Hub (see the section below on logging in to Docker Hub)
    * `sudo docker push earthquakesuc/nzgd_map`

* Copy `nzgd_map.service` to the machine where you want to run the `nzgd_map` package. For example, on Mantle,
    * `cp nzgd_map.service /etc/systemd/system/`

* Reload the systemd unit files. For example, on Mantle,
    *  `sudo systemctl daemon-reload`

* Pull the latest Docker image from Docker Hub and run the `nzgd_map` container by starting the `nzgd_map` service.
    * If the service is not currently running, start it.
        * `sudo systemctl start nzgd_map`
    * If the service is already running, restart it.
        * `sudo systemctl restart nzgd_map`

* Check the status of the `nzgd_map` service to ensure it is running
    * `sudo systemctl status nzgd_map`

* Check the status of the `nzgd_map` container to ensure it is running
    * `sudo docker ps`

### Logging in to Docker Hub
Open a terminal and enter the following command:
`sudo docker login`

The terminal will show a message like the following:

    USING WEB BASED LOGIN
    To sign in with credentials on the command line, use 'docker login -u <username>'

    Your one-time device confirmation code is: XXXX-XXXX
    Press ENTER to open your browser or submit your device code here: https://login.docker.com/activate

    Waiting for authentication in the browser…

If a web browser does not open automatically, copy the URL provided in the message and paste it into a 
web browser. On the web page that opens, enter the one-time device confirmation code provided in 
the message, and our organization's Docker Hub username and password to log in.

## Files for building a Docker image

The following files in the `docker` directory setup the NZGD map service in a container, and run it on startup with systemd. 

- [Service file to start NZGD map service](docker/root_docker_nzgd_map.service)
- [Dockerfile defining NZGD map container](docker/Dockerfile)
- [uWSGI configuration for NZGD server](docker/nzgd.ini)
- [nginx config exposing server outside the container](docker/nginx.conf)
- [Entrypoint script that runs when container is executed](docker/start.sh)
