'''
legisletters: collect, archive, and make searchable legislators' letters
'''

import traceback

from legisletters.constants import ES_INDEX_NAME, ES_RAW_DOC_TYPE, LETTER_IDENTIFIERS
from legisletters.utils import get_index, get_logger

LOGGER = get_logger(__name__)

if __name__ == '__main__':

    ES = get_index(ES_INDEX_NAME, LOGGER)

    for doc in ES.search(size=1000, doc_type=ES_RAW_DOC_TYPE)['hits']['hits']:  # pylint: disable=unexpected-keyword-arg
        try:
            _id = doc['_id']
            html = doc['_source']['html']

            identifier = None
            for possible_identifier in LETTER_IDENTIFIERS:
                if possible_identifier in html.lower():
                    identifier = possible_identifier
                    break

            url = _id.split('#')[0]

            ES.update(doc['_index'], ES_RAW_DOC_TYPE, id=doc['_id'], body={
                'doc': {
                    'html': html,
                    'identifier': identifier,
                    'url': url
                }
            })
            LOGGER.info("++OK: %s", doc['_id'])
        except Exception as err:  #pylint: disable=broad-except
            traceback.print_exc(err)
            LOGGER.error("--ERR: %s (%s)", doc['_id'], err)
