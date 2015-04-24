'''
legisletters: collect, archive, and make searchable legislators' letters
'''

import time
import logging
import elasticsearch
import sys
import requests
import hashlib
import urlparse

from bs4 import BeautifulSoup
from legisletters.constants import REQUEST_HEADERS, LEGISLATORS_BY_URL


def fetch_page(url, session=None):
    '''
    get page with requests, return full response (text & headers accessible as
    properties.)
    '''
    if not session:
        return requests.get(url, headers=REQUEST_HEADERS)
    else:
        return session.get(url, headers=REQUEST_HEADERS)


def get_logger(name):
    '''
    Obtain a logger outputing to stderr with specified name. Defaults to INFO
    log level.
    '''
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.addHandler(logging.StreamHandler(sys.stderr))
    return logger


def get_index(index_name, logger=None):
    '''
    Obtain an index with specified name.  Waits for elasticsearch to start.
    '''
    elastic = elasticsearch.Elasticsearch()
    while True:
        try:
            elastic.indices.create(index=index_name, ignore=400)  # pylint: disable=unexpected-keyword-arg
            break
        except elasticsearch.exceptions.ConnectionError:
            if logger:
                logger.info('waiting for elasticsearch')
            time.sleep(1)
    return elastic


def get_document_id(url, full_doc_html):
    '''
    Construct a document ID based off of the URL and full document html,
    including the press release.

    Concatenates the URL and a SHA1 hash of the HTML of the current text.
    '''
    return u'{}#{}'.format(url, hashlib.sha1(full_doc_html).hexdigest())


def html2text(html):
    '''
    Convert a glob of html to text.
    '''
    return BeautifulSoup(html).get_text('\n').replace(u'\xa0', ' ')


def get_legislator_from_url(url):
    '''
    Obtain the name of a legislator from the URL of the document.
    '''
    parsed = urlparse.urlparse(url)
    return LEGISLATORS_BY_URL.get(parsed.netloc)
