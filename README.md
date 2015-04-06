# LegisLetters

Coding space for the LegisLetters project.

### Installation

Docker preferred.

    ./build.sh
    ./run.sh
    ./exec.sh

You will then be able to run all relevant scripts

### Usage

For now, output is piped through stdout, and log messages through stderr.  Make
sure to set python's encoding.

    PYTHONIOENCODING=utf_8 python scrapers.py > out.txt

### Contributions

Please make sure all files pass `pylint` and `pyflakes`.
