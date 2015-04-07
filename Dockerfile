from elasticsearch

RUN apt-get update
RUN apt-get -yq install python-pip

COPY legisletters /legisletters
RUN pip install -r /legisletters/requirements.txt
