'''
legisletters: collect, archive, and make searchable legislators' letters
'''

import re
import traceback

from bs4 import BeautifulSoup
from dateutil import parser

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
    press_date = None
    for element in enclosing_el.previous_siblings:
        if hasattr(element, 'get_text'):
            try:
                press_date = parser.parse(element.get_text())
                break
            except ValueError:
                pass

    full_letter_plus_attachments = enclosing_el.next_siblings

    sections = {
        RECIPIENTS: [],
        TEXT: [],
        SIGNATURES: [],
        #ATTACHMENTS: []
    }
    cur_section = RECIPIENTS

    letter_date = None
    for element in full_letter_plus_attachments:
        if not hasattr(element, 'get_text'):
            continue

        # Take the first parseable date as the letter date.
        if not letter_date:
            try:
                letter_date = parser.parse(element.get_text())
                continue
            except ValueError:
                pass

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
        u'letterDate': letter_date,
        u'pressDate': press_date,
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

# "stopwords": ["the","to","and","of","in","a","that","for","this","you","is","with","as","on","are","we","have","by","your","be","has","from","it","an","these","not","our","sincerely","will","or","at","their","would","more","which","other","its","all","if","been","also","ensure","provide","any","urge","than","while","should","thank","can","they","such","was","about","including","but","new","work","who","many","write","one","united","know","so","were","year","over","may","important","under","no","time","only","department","act","look","there","regarding","make","well","some","years","could","those","efforts","use","must","ask","into","when","do","1","i","issue","address","continue","believe","since","matter","how","further","what","process","attention","through","take","critical","significant","made","working","country","both","states","forward","support","request","u.s","state","federal","recent","congress","government","american","information","law","public","national","administration","writing","against","help","given","need","additional","during","long","current","however","most","concerns","without","response","consideration","future","them","out","two","does","policy","last","action","between","protect","us","first","because","whether","million","across","services","used","number","appreciate","already","understand","before","had","full","people","service","order","concerned","recently","now","issues","concern","being","report","following","strong","consider","addition","up","like","impact","within","2","3","4","5","6","7","8","9","even","possible","office","system","part","clear","after","review","percent","necessary","program","please","based","several","americans","actions","serious","questions","plan","officials","families","committee","fully","end","according","proposed","three"]
