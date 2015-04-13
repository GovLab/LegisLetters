# LegisLetters

Coding space for the LegisLetters project.

### Installation

Docker preferred.

    ./build.sh
    ./run.sh
    ./exec.sh

You will then be able to run all relevant scripts

### Usage

Inside the docker container, this will add to the Elasticsearch database:

    python scrapers.py

### Rebuilding

You'll need `npm`, `bower`, and `grunt` to build.

    npm install -g grunt-cli bower
    npm install
    bower install
    grunt

This will place updated HTML & JS in the `dist` folder, which is served by the
container `nginx`.

### Contributions

Please make sure all files pass `pylint` and `pyflakes`.
