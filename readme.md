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
and enter the following commands in a terminal. Depending on whether Docker is configured to 
run as root or a user (rootless Docker), use 
[root_docker_nzgd_map.service](docker/root_docker_nzgd_map.service) or 
[rootless_docker_nzgd_map.service](docker/rootless_docker_nzgd_map.service), respectively.


* If Docker is run as root, skip these steps. Otherwise, if running Docker as a user (rootless Docker), follow these steps:
    * Enable and start the docker service for your user
        * `sudo systemctl enable --now docker`
    * Allow your user to "linger" to run services at start up
        * `sudo loginctl enable-linger $(whoami)`
    * Add the following lines to your `~/.bashrc` file.
        * `export PATH=/usr/bin:$PATH`
        * `export DOCKER_HOST=unix:///run/user/$(id -u)/docker.sock`

* Regardless of how Docker is run (root or rootless), perform the following steps:
    * In a terminal, change to the `docker` folder in the repository
        * e.g., `cd /home/username/src/nzgd_map/docker`
    * Build the Docker image (which includes the `nzgd_map` package due to a pip install command in `Dockerfile`). 
    In the following command, `earthquakesuc` is our Docker Hub username.
        * If this is the first time building the image, or the `nzgd_map` package has not changed, run the following command:
            * `docker build -t earthquakesuc/nzgd_map .` (add `sudo` if running as root) 
        * If this is not the first time building the image, and the `nzgd_map` package has changed, run with `--no-cache` 
      so the image will be built with the latest version of the `nzgd_map` package:
            * `docker build --no-cache -t earthquakesuc/nzgd_map .` (add `sudo` if running as root) 

    * Push the image to Docker Hub (see the section below on logging in to Docker Hub)
        * `docker push earthquakesuc/nzgd_map` (add `sudo` if running as root) 

    * Copy the relevant service file to the machine where you want to run the `nzgd_map` package.
        * If running Docker as root:
            * `cp root_docker_nzgd_map.service /etc/systemd/system/`
        * If running Docker as a user (rootless Docker)
            * `cp rootless_docker_nzgd_map.service /etc/systemd/system/`
    * Reload the systemd unit files.
        *  `sudo systemctl daemon-reload`

    * Pull the latest Docker image from Docker Hub and run the `nzgd_map` container by starting the relevant service (`root_docker_nzgd_map` or `rootless_docker_nzgd_map`).
        * If the service is not currently running, start it.
            * `sudo systemctl start rootless_docker_nzgd_map` or `sudo systemctl start root_docker_nzgd_map`
        * If the service is already running, restart it.
            * `sudo systemctl restart rootless_docker_nzgd_map` or `sudo systemctl restart root_docker_nzgd_map`

    * Check the status of the service to ensure it is running
        * `sudo systemctl status rootless_docker_nzgd_map` or `sudo systemctl status root_docker_nzgd_map`

    * Check the status of the `nzgd_map` container to ensure it is running
        * `docker ps` (add `sudo` if running as root)

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

The following files in the `docker` directory set up the NZGD map service in a container, and run it on startup with systemd. 

- [If running Docker as root: Service file to start NZGD map service](docker/root_docker_nzgd_map.service)
- [If running Docker as a user (Rootless Docker): Service file to start NZGD map service](docker/rootless_docker_nzgd_map.service)
- [Dockerfile defining NZGD map container](docker/Dockerfile)
- [uWSGI configuration for NZGD server](docker/nzgd.ini)
- [nginx config exposing server outside the container](docker/nginx.conf)
- [Entrypoint script that runs when container is executed](docker/start.sh)
