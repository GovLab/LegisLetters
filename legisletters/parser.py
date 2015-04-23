'''
legisletters: collect, archive, and make searchable legislators' letters
'''

import re
import traceback
import json
import elasticsearch
#import pdb

from bs4 import BeautifulSoup
from dateutil import parser

from legisletters.constants import (ES_INDEX_NAME, ES_LETTER_DOC_TYPE,
                                    ES_RAW_DOC_TYPE, END_RECIPIENTS_RE,
                                    END_TEXT_RE, END_SIGNATURES_RE)

from legisletters.utils import html2text, get_logger, get_index


RECIPIENTS, TEXT, SIGNATURES, ATTACHMENTS = ('recipients', 'text',
                                             'signatures', 'attachments')

LOGGER = get_logger(__name__)
NON_LETTERS = re.compile(r'\W+')


def find_date(text):
    '''
    Find a date in a goop of text.
    '''
    words = NON_LETTERS.split(text)
    for i in xrange(0, len(words)):
        if len(words) < i + 2:
            break
        try:
            return parser.parse(' '.join(words[i:i+3]))
        except ValueError:
            pass


def process_letter(text, identifier, doc_id):
    '''
    process a letter from its text and known identifier.

    returns None if the letter can't be processed.
    '''
    parsed = {}

    matcher = re.compile(identifier, re.IGNORECASE)

    soup = BeautifulSoup(text)
    parsed['pdfs'] = [pdf.get('href') for pdf in soup.select('a[href*=".pdf"]')]
    parsed['pdfs'].extend([pdf.get('href') for pdf in soup.findAll(
        name='a', text=re.compile('pdf', re.IGNORECASE))])

    press_release, remainder = matcher.split(text, maxsplit=1)
    parsed[u'pressReleaseText'] = html2text(press_release)
    parsed[u'pressDate'] = find_date(press_release)

    try:
        recipients1, recipients2, remainder = re.split(END_RECIPIENTS_RE, remainder, maxsplit=1)
        parsed['recipients'] = html2text(recipients1 + recipients2)
    except ValueError:
        LOGGER.warn("Could not identify recipients in %s, aborting", doc_id)
        if len(remainder) > 200:
            pass
            #pdb.set_trace()
        return parsed

    try:
        letter_text1, letter_text2, letter_text3, remainder = re.split(
            END_TEXT_RE, remainder, maxsplit=1)
        letter_text = letter_text1 + letter_text2 + letter_text3
    except ValueError:
        parsed['text'] = html2text(remainder)
        LOGGER.warn("Could not identify letter text in %s, aborting", doc_id)
        #pdb.set_trace()
        return parsed

    parsed['letterDate'] = find_date(letter_text)
    parsed['text'] = html2text(letter_text)

    try:
        signatures, remainder = re.split(END_SIGNATURES_RE, remainder, maxsplit=1)
        parsed[u'signatures'] = html2text(signatures)

    except ValueError:
        LOGGER.warn("Could not identify end of signatures in %s, aborting", doc_id)

    return parsed


if __name__ == '__main__':

    ES = get_index(ES_INDEX_NAME, LOGGER)
    ES.indices.delete_mapping(index=ES_INDEX_NAME, doc_type=ES_LETTER_DOC_TYPE)
    ES.indices.put_mapping(index=ES_INDEX_NAME, doc_type=ES_LETTER_DOC_TYPE,
                           body=json.load(open('legisletters/letter_mapping.json', 'r')))

    for doc in ES.search(size=1000, index='legisletters',  # pylint: disable=unexpected-keyword-arg
                         doc_type=ES_RAW_DOC_TYPE)['hits']['hits']:
        try:
            source = doc['_source']
            url = source['url']
            if '/searchresults' in url.lower():
                LOGGER.info("--SKIP: %s (seems to be a search page)", doc['_id'])
                continue

            parsed_letter = process_letter(source['html'], source['identifier'], doc['_id'])
            parsed_letter['url'] = url

            try:
                ES.delete(doc['_index'], ES_LETTER_DOC_TYPE, id=doc['_id'])
            except elasticsearch.NotFoundError:
                pass
            ES.create(doc['_index'], ES_LETTER_DOC_TYPE, id=doc['_id'], body=parsed_letter)
            LOGGER.info("++OK: %s", doc['_id'])
        except Exception as err:  #pylint: disable=broad-except
            traceback.print_exc(err)
            LOGGER.error("--ERR: %s (%s)", doc['_id'], err)
            #pdb.set_trace()

# "stopwords": ["the","to","and","of","in","a","that","for","this","you","is","with","as","on","are","we","have","by","your","be","has","from","it","an","these","not","our","sincerely","will","or","at","their","would","more","which","other","its","all","if","been","also","ensure","provide","any","urge","than","while","should","thank","can","they","such","was","about","including","but","new","work","who","many","write","one","united","know","so","were","year","over","may","important","under","no","time","only","department","act","look","there","regarding","make","well","some","years","could","those","efforts","use","must","ask","into","when","do","1","i","issue","address","continue","believe","since","matter","how","further","what","process","attention","through","take","critical","significant","made","working","country","both","states","forward","support","request","u.s","state","federal","recent","congress","government","american","information","law","public","national","administration","writing","against","help","given","need","additional","during","long","current","however","most","concerns","without","response","consideration","future","them","out","two","does","policy","last","action","between","protect","us","first","because","whether","million","across","services","used","number","appreciate","already","understand","before","had","full","people","service","order","concerned","recently","now","issues","concern","being","report","following","strong","consider","addition","up","like","impact","within","2","3","4","5","6","7","8","9","even","possible","office","system","part","clear","after","review","percent","necessary","program","please","based","several","americans","actions","serious","questions","plan","officials","families","committee","fully","end","according","proposed","three"] # pylint: disable=line-too-long
