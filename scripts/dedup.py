'''
legisletters: collect, archive, and make searchable legislators' letters
'''

from legisletters.constants import ES_INDEX_NAME, ES_RAW_LETTER_DOC_TYPE
from legisletters.utils import get_index, get_logger

from legisletters.scraper import download_url

LOGGER = get_logger(__name__)

if __name__ == '__main__':

    ES = get_index(ES_INDEX_NAME, LOGGER)

    QUERY = {
        "filter": {
            "missing": {
                "field": "recipients"
            }
        }
    }

    for doc in ES.search(size=100, doc_type=ES_LETTER_DOC_TYPE, body=QUERY)['hits']['hits']:  # pylint: disable=unexpected-keyword-arg
        print doc['_source']['url']
        download_url(doc['_source']['url'], ES)
