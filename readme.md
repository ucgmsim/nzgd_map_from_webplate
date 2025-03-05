This app is intended to be deployed in a Docker container. The Dockerfile is included in the repository. 

To build the Docker image, run the following command in the root directory of the repository:


`cd /home/arr65/src/earthquakesuc/nzgd_map`

`sudo docker build -t earthquakesuc/nzgd_map .`

`sudo docker push earthquakesuc/nzgd_map`

Then to run on Mantle, just restart 

the service with the following command:

`sudo systemctl restart nzgd_map`

Which will automatically pull the latest image from Docker Hub and run it.

sudo systemctl daemon-reload
