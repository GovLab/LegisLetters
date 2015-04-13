from elasticsearch

RUN apt-get update
RUN apt-get -yq install python-pip nginx

COPY legisletters /legisletters
COPY default /etc/nginx/sites-available/default

RUN pip install -r /legisletters/requirements.txt
