'''
legisletters: collect, archive, and make searchable legislators' letters
'''

from legisletters.utils import get_index, get_logger
from legisletters.constants import ES_INDEX_NAME

if __name__ == '__main__':
    LOGGER = get_logger(__name__)
    INDEX = get_index(ES_INDEX_NAME, LOGGER)

    HITS = INDEX.search(size=1000)['hits']['hits']  # pylint: disable=unexpected-keyword-arg
    #print len(hits)
    import pdb
    pdb.set_trace()
