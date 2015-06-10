'''
legisletters: collect, archive, and make searchable legislators' letters
'''

import re
import traceback
import json
import elasticsearch

from bs4 import BeautifulSoup
from dateutil import parser

from legisletters.constants import (ES_INDEX_NAME, ES_LETTER_DOC_TYPE,
                                    ES_RAW_DOC_TYPE, END_RECIPIENTS_RE,
                                    END_TEXT_RE, END_SIGNATURES_RE)

from legisletters.utils import (html2text, get_logger, get_index,
                                get_legislator_from_url)


LOGGER = get_logger(__name__)
NON_LETTERS = re.compile(r'\W+')


def find_date(text):
    '''
    Find a date in a goop of text.
    '''
    #for line in text.split('\n'):
    #    line = line.strip()
    words = NON_LETTERS.split(text)
    for i in xrange(0, 4):
        if len(words[i:i+4]) < 3:
            break
        try:
            try:  # resolve issue with Tuesday, August 26 resolving to this year
                four_words = ' '.join(words[i:i+4]).strip()
                if four_words:
                    return parser.parse(four_words)
            except ValueError:
                three_words = ' '.join(words[i:i+3]).strip()
                if three_words:
                    return parser.parse(three_words)
        except ValueError:
            pass
        #import pdb
        #pdb.set_trace()


def is_duplicate(url):
    '''
    Determine whether this letter shares a URL with another document.
    '''
    hits = ES.search(index='legisletters',  # pylint: disable=unexpected-keyword-arg
                     body={"query": {"query_string": {
                         "query": '"' + url + '"',
                         "default_field": "url"
                     }}},
                     doc_type=ES_RAW_DOC_TYPE)['hits']['hits']
    return len(hits) > 1


def delete_raw_letter(doc_id):
    '''
    Delete raw_letter by doc_id
    '''
    ES.delete(index='legisletters', id=doc_id, doc_type=ES_RAW_DOC_TYPE)


def process_letter(text, identifier, doc_id): #pylint: disable=too-many-locals
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
    parsed[u'pressDate'] = find_date(parsed[u'pressReleaseText'])

    try:
        recipients1, recipients2, remainder = re.split(END_RECIPIENTS_RE, remainder, maxsplit=1)
        parsed['recipients'] = html2text(recipients1 + recipients2)
    except ValueError:

        # Remove bad scrape from past
        # if is_duplicate(url):
        #     delete_raw_letter(doc_id)

        LOGGER.warn("Could not identify recipients in %s, aborting", doc_id)

        # If we were able to find PDFs, this is a legit letter, just no text
        # available
        if parsed['pdfs']:
            return parsed
        else:
            raise Exception("No text or PDFs")

    split = re.split(END_TEXT_RE, remainder)
    if len(split) > 1:
        remainder = split[-1]
        letter_text = ''.join(split[0:-1])
    else:
        parsed['text'] = html2text(remainder)
        LOGGER.warn("Could not identify letter text in %s, aborting", doc_id)
        #pdb.set_trace()
        return parsed

    parsed['letterDate'] = find_date(parsed['recipients'])
    parsed['text'] = re.sub(r'\s+', ' ', html2text(letter_text))

    try:
        signatures, remainder = re.split(END_SIGNATURES_RE, remainder, maxsplit=1)
        parsed[u'signatures'] = html2text(signatures)

    except ValueError:
        LOGGER.warn("Could not identify end of signatures in %s, aborting", doc_id)

    return parsed


if __name__ == '__main__':

    DESTRUCTIVE = False

    ES = get_index(ES_INDEX_NAME, LOGGER)
    if DESTRUCTIVE == True:
        try:
            ES.indices.delete_mapping(index=ES_INDEX_NAME, doc_type=ES_LETTER_DOC_TYPE)
        except elasticsearch.exceptions.NotFoundError:
            pass
    ES.indices.put_mapping(index=ES_INDEX_NAME, doc_type=ES_LETTER_DOC_TYPE,
                           body=json.load(open('mappings/letter_mapping.json', 'r')))

    OFFSET = 0
    QUERY_SIZE = 100
    while True:
        DOCS = ES.search(size=QUERY_SIZE, index='legisletters',  # pylint: disable=unexpected-keyword-arg
                         from_=OFFSET, doc_type=ES_RAW_DOC_TYPE, body={"query": {
                             "constant_score": {
                                 "filter": {
                                     "exists": {
                                         "field": "html"
                                     }
                                 }
                             }
                         }})['hits']['hits']

        if len(DOCS) == 0:
            break

        for doc in DOCS:
            try:
                source = doc['_source']
                url_ = source['url']
                if '/searchresults' in url_.lower():
                    LOGGER.info("--SKIP: %s (seems to be a search page)", doc['_id'])
                    continue

                parsed_letter = process_letter(source['html'],
                                               source['identifier'],
                                               doc['_id'])
                parsed_letter['url'] = url_
                date = parsed_letter.get('letterDate', parsed_letter.get('pressDate'))
                parsed_letter['hostLegislator'] = get_legislator_from_url(url_, date)

                if ES.exists(doc['_index'], doc_type=ES_LETTER_DOC_TYPE, id=doc['_id']):
                    if DESTRUCTIVE:
                        ES.delete(doc['_index'], ES_LETTER_DOC_TYPE, id=doc['_id'])
                    else:
                        LOGGER.info("++EXISTS: %s", doc['_id'])
                        continue

                ES.create(doc['_index'], ES_LETTER_DOC_TYPE, id=doc['_id'], body=parsed_letter)
                LOGGER.info("++OK: %s", doc['_id'])

            except Exception as err:  #pylint: disable=broad-except
                traceback.print_exc(err)
                LOGGER.error("--ERR: %s (%s)", doc['_id'], err)
                #pdb.set_trace()

        OFFSET += QUERY_SIZE
        #break # uncomment to do just do 100 docs

# "stopwords": ["the","to","and","of","in","a","that","for","this","you","is","with","as","on","are","we","have","by","your","be","has","from","it","an","these","not","our","sincerely","will","or","at","their","would","more","which","other","its","all","if","been","also","ensure","provide","any","urge","than","while","should","thank","can","they","such","was","about","including","but","new","work","who","many","write","one","united","know","so","were","year","over","may","important","under","no","time","only","department","act","look","there","regarding","make","well","some","years","could","those","efforts","use","must","ask","into","when","do","1","i","issue","address","continue","believe","since","matter","how","further","what","process","attention","through","take","critical","significant","made","working","country","both","states","forward","support","request","u.s","state","federal","recent","congress","government","american","information","law","public","national","administration","writing","against","help","given","need","additional","during","long","current","however","most","concerns","without","response","consideration","future","them","out","two","does","policy","last","action","between","protect","us","first","because","whether","million","across","services","used","number","appreciate","already","understand","before","had","full","people","service","order","concerned","recently","now","issues","concern","being","report","following","strong","consider","addition","up","like","impact","within","2","3","4","5","6","7","8","9","even","possible","office","system","part","clear","after","review","percent","necessary","program","please","based","several","americans","actions","serious","questions","plan","officials","families","committee","fully","end","according","proposed","three"] # pylint: disable=line-too-long
