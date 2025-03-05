FROM python:3.12-alpine

# Install required packages
RUN apk add --no-cache git nginx sqlite-libs uwsgi-python3

# Create necessary directories
RUN mkdir -p /data
RUN mkdir -p /usr/var/nzgd_map-instance
RUN chown -R nobody:nobody /usr/var/nzgd_map-instance


# Install pdoc for documentation generation
#RUN pip install --no-cache-dir "git+https://github.com/ucgmsim/nzgd_map#egg=nzgd_map" uwsgi
RUN pip install --no-cache-dir "git+https://github.com/ucgmsim/nzgd_map@for_container#egg=nzgd_map"


COPY nzgd.ini /nzgd.ini
COPY start.sh /start.sh
RUN chmod +x /start.sh

# Copy nginx config
COPY nginx.conf /etc/nginx/nginx.conf

# Start nginx in the foreground
CMD /start.sh
