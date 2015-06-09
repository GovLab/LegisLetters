'''
legisletters: collect, archive, and make searchable legislators' letters
'''

import time
import logging
import elasticsearch
import sys
import urlparse
import traceback

from bs4 import BeautifulSoup
from legisletters.constants import LEGISLATORS_BY_URL, ES_INDEX_NAME, ES_RAW_DOC_TYPE


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


def strip_script_from_soup(element):
    '''
    Remove script tags from an element.  Modifies in-place.
    '''
    for script in element.findAll('script'):
        script.extract()


def add_raw_doc(elastic, body, logger, exists_behavior='warn'):
    '''
    Add a raw doc, but only if it hasn't been added yet.
    '''
    url = body['url']
    same_url_docs = elastic.search(index=ES_INDEX_NAME, doc_type=ES_RAW_DOC_TYPE, body={
        "query": {
            "query_string": {
                "query": '"' + url + '"',
                "default_field": "url"
            }
        }
    })['hits']['hits']

    if len(same_url_docs) > 0:
        if exists_behavior == 'warn':
            logger.warn('Doc already exists with URL %s, skipping', url)
            return
        elif exists_behavior == 'pdb':
            import pdb
            pdb.set_trace()
            return
        elif exists_behavior == 'raise':
            raise Exception('Doc already exists with URL {}, skipping'.format(url))
        elif exists_behavior == 'replace':
            for doc in same_url_docs:
                logger.info('deleting %s for %s (add_raw_doc:replace)', doc['_id'], url)
                try:
                    elastic.delete(index=ES_INDEX_NAME, doc_type=ES_RAW_DOC_TYPE,
                                   id=doc['_id'])
                except: #pylint: disable=bare-except
                    logger.warn(traceback.format_exc())

    logger.info('adding raw doc for %s', url)
    elastic.index(index=ES_INDEX_NAME, doc_type=ES_RAW_DOC_TYPE, body=body)
