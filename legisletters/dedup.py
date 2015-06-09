'''
legisletters: collect, archive, and make searchable legislators' letters
'''

from legisletters.constants import ES_INDEX_NAME, ES_RAW_DOC_TYPE
from legisletters.utils import get_index, get_logger, add_raw_doc
import traceback

#from legisletters.scraper import download_url

LOGGER = get_logger(__name__)

if __name__ == '__main__':

    ES = get_index(ES_INDEX_NAME, LOGGER)

    QUERY = {
        "fields": ["url"],
        "filter": {
            "missing": {
                "field": "pdf"
            }
        }
    }

    OFFSET = 0
    QUERY_SIZE = 100
    while True:
        LOGGER.info('%s docs in raw_letter, offset %s', ES.count('legisletters', ES_RAW_DOC_TYPE),
                    OFFSET)
        DOCS = ES.search(index='legisletters',  # pylint: disable=unexpected-keyword-arg
                         size=QUERY_SIZE, doc_type=ES_RAW_DOC_TYPE, body=QUERY,
                         from_=OFFSET)['hits']['hits']

        if len(DOCS) == 0:
            break

        for doc in DOCS:
            if len(doc['_id']) == 20:
                continue

            url = doc['fields']['url'][0]
            url_query = {
                "query": {
                    "query_string": {
                        "query": '"' + url + '"',
                        "default_field": "url"
                    }
                }
            }
            url_docs = ES.search(index='legisletters',  # pylint: disable=unexpected-keyword-arg
                                 doc_type=ES_RAW_DOC_TYPE,
                                 body=url_query)['hits']['hits']

            # delete possible search results
            if 'searchresults' in url.lower():
                for doc in url_docs:
                    LOGGER.info('deleting %s for %s (searchResults)', doc['_id'], url)
                    try:
                        ES.delete(index='legisletters', doc_type=ES_RAW_DOC_TYPE,
                                  id=doc['_id'])
                    except: #pylint: disable=bare-except
                        LOGGER.warn(traceback.format_exc())
            else:
                keepdata = {}

                # just use the one with the latest scrape time
                for doc in url_docs:
                    if doc['_source'].get('scrapeTime') > keepdata.get('scrapeTime'):
                        keepdata = doc['_source']

                if keepdata:
                    add_raw_doc(ES, keepdata, LOGGER, 'replace')
                else:
                    for doc in url_docs:
                        LOGGER.info('deleting %s for %s (no scrapeTime)', doc['_id'], url)
                        try:
                            ES.delete(index=ES_INDEX_NAME,
                                      doc_type=ES_RAW_DOC_TYPE, id=doc['_id'])
                        except: #pylint: disable=bare-except
                            LOGGER.warn(traceback.format_exc())

        OFFSET += QUERY_SIZE
