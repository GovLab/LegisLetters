'''
legisletters: collect, archive, and make searchable legislators' letters
'''

import re
import traceback

from bs4 import BeautifulSoup

from legisletters.constants import ES_INDEX_NAME
from legisletters.utils import els2text, get_logger, get_index


RECIPIENTS, TEXT, SIGNATURES, ATTACHMENTS = ('recipients', 'text',
                                             'signatures', 'attachments')
END_RECIPIENTS_RE = re.compile('(dear)|(to the)', re.IGNORECASE)
END_TEXT_RE = re.compile('(sincerely)', re.IGNORECASE)

LOGGER = get_logger(__name__)


def process_letter(text, identifier, doc_id):
    '''
    process a letter from its text and known identifier.

    returns None if the letter can't be processed.
    '''
    matcher = re.compile(identifier, re.IGNORECASE)
    enclosing_el = BeautifulSoup(text)
    matching_text = enclosing_el.find(text=matcher)

    if not matching_text:
        raise Exception("can't find letter identifier {}".format(identifier))

    # Ascend through tags to find important enclosing block
    enclosing_el = matching_text.parent
    while enclosing_el.parent.get_text() == enclosing_el.get_text():
        enclosing_el = enclosing_el.parent

    press_release = els2text(enclosing_el.previous_siblings)
    full_letter_plus_attachments = enclosing_el.next_siblings

    sections = {
        RECIPIENTS: [],
        TEXT: [],
        SIGNATURES: [],
        #ATTACHMENTS: []
    }
    cur_section = RECIPIENTS

    for element in full_letter_plus_attachments:
        if not hasattr(element, 'get_text'):
            continue

        sections[cur_section].append(element)

        if cur_section == RECIPIENTS and END_RECIPIENTS_RE.search(element.get_text()):
            cur_section = TEXT
        elif cur_section == TEXT and END_TEXT_RE.search(element.get_text()):
            cur_section = SIGNATURES

    for section, value in sections.iteritems():
        if not value:
            LOGGER.warn("Could not extract value for '%s' in %s", section, doc_id)

    return {
        u'pressReleaseText': press_release,
        u'recipients': els2text(sections[RECIPIENTS]),
        u'text': els2text(sections[TEXT]),
        u'signatures': els2text(sections[SIGNATURES]),
        #u'attachments': els2text(sections[ATTACHMENTS])
    }


if __name__ == '__main__':

    ES = get_index(ES_INDEX_NAME, LOGGER)

    for doc in ES.search(size=1000)['hits']['hits']:  # pylint: disable=unexpected-keyword-arg
        try:
            source = doc['_source']
            html = source['html']
            text_identifier = doc['_source']['identifier']
            source.update(process_letter(html, text_identifier, doc['_id']))
            ES.update(doc['_index'], doc['_type'], doc['_id'], body={
                'doc': source
            })
            LOGGER.info("++OK: %s", doc['_id'])
        except Exception as err:  #pylint: disable=broad-except
            traceback.print_exc(err)
            LOGGER.error("--ERR: %s (%s)", doc['_id'], err)
