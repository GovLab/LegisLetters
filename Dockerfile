from elasticsearch

RUN apt-get update
RUN apt-get -yq install python-pip

COPY scripts /scripts
RUN pip install -r /scripts/requirements.txt

WORKDIR /scripts
