## Introduction

This repository contains the source code for the `nzgd_map` package which is a web application
that enables access to analysis-ready data products derived from data hosted on the New Zealand Geotechnical 
Database (NZGD). This repository also contains files for building a Docker image that can be used to run the
`nzgd_map` package in a containerized environment.

## Installation

### Installing outside a Docker container

#### Installing an uneditable version

To install an uneditable version of `nzgd_map` outside a Docker container, simply enter the following 
command in a terminal:

* `pip install "git+https://github.com/ucgmsim/nzgd_map#egg=nzgd_map"` 

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
and enter the following commands in a terminal. More information about the files in the `docker` folder can be found below.

* Open a terminal and change to the `docker` folder in the repository
    * e.g., `cd /home/username/src/nzgd_map/docker`
* Build the Docker image (which includes the `nzgd_map` package due to a pip install instruction in `Dockerfile`). Also note that `earthquakesuc` is our Docker Hub username.
    * If this is the first time building the image, or the `nzgd_map` package has not changed, run the following command:
        * `sudo docker build -t earthquakesuc/base .` 
    * If this is not the first time building the image, and the `nzgd_map` package has changed, run with `--no-cache` so the image will be built with the latest version of the `nzgd_map` package:
    * `sudo docker build -t --no-cache earthquakesuc/nzgd_map .` 

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

* Check the status of the `nzgd_map` service to ensure it is running.
    * `sudo systemctl status nzgd_map`

* Check the status of the `nzgd_map` container to ensure it is running.
    * `sudo docker ps`

### Logging in to Docker Hub
Open a terminal and enter the following command:
sudo docker login`

The terminal will show a message like the following:

    USING WEB BASED LOGIN
    To sign in with credentials on the command line, use 'docker login -u <username>'

    Your one-time device confirmation code is: JGPX-PVKR
    Press ENTER to open your browser or submit your device code here: https://login.docker.com/activate

    Waiting for authentication in the browser…

If a web browser does not open automatically, copy the URL provided in the message and paste it into a 
web browser. On the web page that opens, enter the one-time device confirmation code provided in 
the message, and our organization's Docker Hub username and password to log in.

## Files for building a Docker image

This section explains the files used to build the Docker image. Every line from these files is 
followed by an explanation of its purpose.

### nzgd_map.service

**File line:**
`[Unit]`

**Explanation:**
Contains metadata and defines relationships with other services.

**File line:**  
`Description=NZGD Map Service`  

**Explanation:**  
Provides a short description of the service as "NZGD Map Service".

**File line:**  
`After=snap.docker.dockerd.service`  

**Explanation:**  
Ensures that this service starts only after the Docker daemon service (snap.docker.dockerd.service) has started.

**File line:**  
`Requires=snap.docker.dockerd.service`  

**Explanation:**  
Declares a dependency on the Docker daemon service, ensuring it is running before this service starts.

**File line:** 
`[Service]`

**Explanation:**
Controls how the service process executes and behaves.

**File line:**  
`TimeoutStartSec=0`  

**Explanation:**  
Sets the start timeout to 0 seconds, meaning systemd will wait indefinitely for the service to start.

**File line:**  
`Restart=always`  

**Explanation:**  
Configures systemd to always restart the service if it stops for any reason.

**File line:**  
`ExecStartPre=/snap/bin/docker pull earthquakesuc/nzgd_map`  

**Explanation:**  
Runs this command before starting the service; it pulls the latest Docker image "earthquakesuc/nzgd_map".

**File line:**  
`ExecStart=/snap/bin/docker run --rm --name %n -p 7777:80 -v /mnt/mantle_data/nzgd_map:/usr/var/nzgd_map-instance earthquakesuc/nzgd_map`  

**Explanation:**  
Starts the Docker container using the pulled image with the following options:  
- **--rm:** Automatically removes the container when it exits.  
- **--name %n:** Names the container based on the service name.  
- **-p 7777:80:** Maps host port 7777 to container port 80.  
- **-v /mnt/mantle_data/nzgd_map:/usr/var/nzgd_map-instance:** Mounts a host directory into the container.

**File line:**  
`ExecStop=/snap/bin/docker stop %n`  

**Explanation:**  
Stops the Docker container gracefully when the service is stopped.

**File line:**  
`ExecStopPost=/snap/bin/docker rm %n`  

**Explanation:**  
Removes the container after stopping to clean up any remnants.

**[Install]**

**File line:**  
`WantedBy=default.target`  

**Explanation:**  
Specifies that the service should be started when the default system target (usually multi-user mode) is reached.

--- 

### Dockerfile

**FROM python:3.12-alpine**

**File line:**  
`FROM python:3.12-alpine`  

**Explanation:**  
Specifies the base image for the Docker container using the official Python 3.12 image based on Alpine Linux, which is a lightweight distribution suitable for production environments.


**File line:**  
`RUN apk add --no-cache git nginx sqlite-libs uwsgi-python3`  

**Explanation:**  
Uses Alpine’s package manager (`apk`) to install the necessary packages (git, nginx, sqlite libraries, and uwsgi for Python3) without caching, which helps keep the image size small.

**File line:**  
`RUN mkdir -p /data`  

**Explanation:**  
Creates the `/data` directory if it does not already exist.

**File line:**  
`RUN mkdir -p /usr/var/nzgd_map-instance`  

**Explanation:**  
Creates the `/usr/var/nzgd_map-instance` directory, which is used for storing instance-specific data for the NZGD map service.

**File line:**  
`RUN chown -R nobody:nobody /usr/var/nzgd_map-instance`  

**Explanation:**  
Changes the ownership of the `/usr/var/nzgd_map-instance` directory (and its contents) recursively to the user and group “nobody” for improved security.

**File line:**  
RUN pip install --no-cache-dir "git+https://github.com/ucgmsim/nzgd_map#egg=nzgd_map" uwsgi`  

**Explanation:**  
Installs the nzgd_map package directly from a Git repository without using the pip cache, ensuring the latest version 
for container deployment.

**File line:**  
`COPY nzgd.ini /nzgd.ini`  

**Explanation:**
Copies the `nzgd.ini` configuration file from the build context into the container’s root directory.

**File line:**
`COPY start.sh /start.sh`  

**Explanation:**  
Copies the `start.sh` script from the build context into the container’s root directory.

**File line:**  
`RUN chmod +x /start.sh`  

**Explanation:**  
Grants execute permission to the `start.sh` script so that it can be run as a command when the container starts.


**File line:**  
`COPY nginx.conf /etc/nginx/nginx.conf`  

**Explanation:**  
Copies the `nginx.conf` file from the build context into the container’s `/etc/nginx/` directory, replacing the default nginx configuration.

**File line:**  
`CMD /start.sh`  

**Explanation:**  
Sets the default command to run when the container starts; it executes the `start.sh` script, which is likely responsible for starting nginx (and possibly other services) in the foreground.

---

### nzgd.ini

**File line:**  
`[uwsgi]`  

**Explanation:**  
This section header indicates that the following configuration settings are for uWSGI.

**File line:**  
`module = nzgd_map.wsgi`  

**Explanation:**  
Specifies that the WSGI module to be used is `nzgd_map.wsgi`, which is the entry point for the WSGI application.

**File line:**  
`callable = app`  

**Explanation:**  
Indicates that within the specified module, the WSGI callable (i.e., the application object) is named `app`.

**File line:**  
`plugins = python3`  

**Explanation:**  
Instructs uWSGI to load the `python3` plugin, enabling support for Python 3.

**File line:**  
`master = true`  

**Explanation:**  
Enables the master process mode in uWSGI, which manages worker processes.

**File line:**  
`processes = 5`  

**Explanation:**  
Sets the number of worker processes to 5, allowing the application to handle multiple requests concurrently.

**File line:**  
`socket = /tmp/nzgd.sock`  

**Explanation:**  
Configures uWSGI to create a Unix socket at `/tmp/nzgd.sock` for communication between uWSGI and the web server.
It is **important** that the socket is created in the `/tmp` directory so that all processes have read/write access,
as Nginx will run under `root` while uWSGI will run under `nobody` (as specified further down in nzgd.ini)

**File line:**  
`chmod-socket = 666`  

**Explanation:**  
Sets the permissions for the socket to `666`, making it readable and writable by all users.

**File line:**  
`vacuum = true`  

**Explanation:**  
Ensures that uWSGI cleans up (removes) the socket file when it shuts down.

**File line:**  
`uid = nobody`  

**Explanation:**  
Specifies that the uWSGI processes should run under the `nobody` user for improved security.

**File line:**  
`gid = nobody`  

**Explanation:**  
Specifies that the uWSGI processes should run under the `nobody` group for security purposes.

**File line:**  
`die-on-term = true`  

**Explanation:**  
Configures uWSGI to shut down gracefully when it receives a termination signal.

**File line:**  
`route-run = fixpathinfo:`  

**Explanation:**  
Sets a routing rule to fix the `PATH_INFO` in the request environment, which can help ensure the application receives the correct URL path.

**File line:**  
`pythonpath = /usr/local/lib/python3.12/site-packages`  

**Explanation:**  
Adds the specified directory to the Python module search path, ensuring that Python packages located there can be found and imported.
This is **important** as the `nzgd_map` package **cannot** be imported without this line.
---

### nginx.conf

**File line:**  
`worker_processes 1;`  

**Explanation:**  
Sets the number of worker processes that Nginx will spawn. In this case, only 1 worker process is created.

**File line:**  
`events { worker_connections 1024; }`  

**Explanation:**  
Begins the events block and sets the maximum number of simultaneous connections per worker process to 1024.


**File line:**  
`http {`  

**Explanation:**  
Starts the HTTP configuration block where settings for handling HTTP requests are defined.

**File line:**  
`    include /etc/nginx/mime.types;  # <- Ensures proper MIME types!`  

**Explanation:**  
Includes the MIME types configuration file that maps file extensions to MIME types. This ensures that files are served with the correct Content-Type header.

**File line:**  
``    server {``  

**Explanation:**  
Starts a server block which defines the configuration for a virtual server handling HTTP requests.

**File line:**  
``           listen 80;``  

**Explanation:**  
Instructs the server to listen for incoming HTTP requests on port 80.

**File line:**  
``           server_name localhost;``  

**Explanation:**  
Sets the server name to "localhost". This server block will handle requests directed to the hostname "localhost".

**File line:**  
``           location /nzgd {``  

**Explanation:**  
Begins a location block that matches requests starting with the URI `/nzgd`. This block defines how requests to that path should be handled.

**File line:**  
``                    include uwsgi_params;``  

**Explanation:**  
Includes the uWSGI parameters file, which defines necessary parameters for communicating with a uWSGI server.

**File line:**  
``                    uwsgi_pass unix:/tmp/nzgd.sock;``  

**Explanation:**  
Directs Nginx to forward matching requests to a uWSGI server through the Unix socket located at `/tmp/nzgd.sock`.

**File line:**  
``                    uwsgi_param SCRIPT_NAME /nzgd;``  

**Explanation:**  
Sets the `SCRIPT_NAME` parameter to `/nzgd` so that the uWSGI application correctly interprets the base URI for requests.

**File line:**  
``           }``  

**Explanation:**  
Closes the location block.


**File line:**  
``    }``  

**Explanation:**  
Closes the server block.

**File line:**  
`}`  

**Explanation:**  
Closes the HTTP configuration block.

### start.sh


**File line:**  
`#!/usr/bin/env sh`  

**Explanation:**  
Specifies the script interpreter by using the environment's `sh`. This is the shebang line that tells the system to execute the script with the shell interpreter.

**File line:**  
`echo "Starting nginx"`  

**Explanation:**  
Prints the message "Starting nginx" to the console, which serves as an informational log to indicate that the script is beginning the process of starting Nginx.

**File line:**  
`uwsgi --ini /nzgd.ini &`  

**Explanation:**  
Starts the uWSGI server using the configuration file `/nzgd.ini` and runs it in the background (due to the trailing `&`), allowing the script to continue executing subsequent commands.

**File line:**  
`nginx -g "daemon off;"`  

**Explanation:**  
Launches Nginx with the directive to run in the foreground (`daemon off;`). Running Nginx in the foreground is particularly useful in container environments to prevent the container from exiting.