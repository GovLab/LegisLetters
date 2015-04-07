'''
legisletters: collect, archive, and make searchable legislators' letters
'''

import time
import logging
import elasticsearch
import sys
import requests
import hashlib

from legisletters.constants import REQUEST_HEADERS


def fetch_page(url):
    '''
    get page with requests, return full response (text & headers accessible as
    properties.)
    '''
    return requests.get(url, headers=REQUEST_HEADERS)


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


def els2text(els):
    '''
    Convert a series BeautifulSoup elements to plaintext
    '''
    arr = []
    for element in els:
        if hasattr(element, 'get_text'):
            arr.append(element.get_text())
    return u'\n'.join(arr)
