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
from legisletters.constants import LEGISLATORS_BY_URL


def get_logger(name):
    '''
    Obtain a logger outputing to stderr with specified name. Defaults to INFO
    log level.
    '''
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter('%(asctime)-15s %(message)s'))
    logger.addHandler(handler)
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


def get_legislator_from_url(url, date):
    '''
    Obtain legislator info based off of url or date.  If date is None, then the
    most recent term is used.
    '''
    #if not legislators:
    #    legislators = LEGISLATORS_BY_URL.get(parsed.netloc.replace('www.', ''))

    legislator = LEGISLATORS_BY_URL[urlparse.urlparse(url).netloc]

    if date:
        for start, end, term in legislator['terms']:
            if date >= start and date < end:
                break
    else:
        _, _, term = legislator['terms'][-1]

    if term['type'] == 'sen':
        term['type'] = 'Senate'
    elif term['type'] == 'rep':
        term['type'] = 'House of Representatives'

    return {
        'name': legislator['name'],
        'bio': legislator['bio'],
        # http://bioguide.congress.gov/bioguide/photo/S/S000033.jpg
        'id': legislator['id'],
        'term': term
    }
