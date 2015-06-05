'''
legisletters: collect, archive, and make searchable legislators' letters
'''

import urllib
import traceback
import datetime
import re
import requests
import json
import base64
import time
import random
from bs4 import BeautifulSoup

from legisletters.constants import (ES_INDEX_NAME, ES_RAW_DOC_TYPE, UA_STRINGS,
                                    LETTER_IDENTIFIERS, LEGISLATORS_BY_URL)
from legisletters.utils import get_logger, fetch_page, get_document_id, get_index

LOGGER = get_logger(__name__)
SESSIONS = []
for ua_string in UA_STRINGS:
    SESSIONS.append(requests.session())
    SESSIONS[-1].headers.update({'User-Agent': ua_string})


def scrape_google(query, site, start=0):
    '''
    Scrape a query from google for a specific site.

    Returns a list of results and a bool of whether this is the last page.
    '''
    entity = urllib.quote(query)
    site_restrict = urllib.quote('site:%s' % site)
    url = "https://www.google.com/search?q=%s+%s&start=%d" % (entity, site_restrict, start)
    LOGGER.info("Processing %s", url)
    results = []
    holdoff = 120
    while True:
        response = fetch_page(url, session=random.choice(SESSIONS))
        if 'Our systems have detected unusual traffic from your computer network.' in response.text:
            LOGGER.warn("Rate-limited by Google, waiting %s seconds", holdoff)
            time.sleep(holdoff)
            holdoff *= 2
        else:
            break
    if "No results found for" in response.text:
        return results, True
    soup = BeautifulSoup(response.text)
    results.extend([
        process_url_from_google(t.a['href']) for t in soup.findAll('h3', attrs={'class': 'r'})])
    is_last_page_ = 'Next</span' not in response.text
    return results, is_last_page_


def process_url_from_google(url):
    '''
    Extract actual URL from the google forwarding link
    '''
    #return urllib.unquote(url[7:].split('&')[0])
    # If we use https, google gives us real links
    return url


def extract_text_from_letter(full_page):
    '''
    Isolate the relevant section of press release + letter from a full page of
    HTML.

    Returns two tuple, the text and the identifier used.

    Raises exception if none of the identifiers work.
    '''
    letter_soup = BeautifulSoup(full_page)
    for identifier in ('full text', 'text of the'):
        matcher = re.compile(identifier, re.IGNORECASE)
        matching_text = letter_soup.find(text=matcher)

        if matching_text:
            enclosing_el = matching_text.parent

            # Ascend through tags to find important enclosing block
            while enclosing_el.parent.get_text() == enclosing_el.get_text() or \
                  len(enclosing_el.get_text()) < 100:
                enclosing_el = enclosing_el.parent

            return unicode(enclosing_el.parent), identifier

    raise Exception("Cannot identify letter in text")


def download_url(url, elastic):
    '''
    Download raw content for URL
    '''
    resp = fetch_page(url, session=random.choice(SESSIONS))
    if 'html' in resp.headers['content-type']:
        original_html, text_identifier = extract_text_from_letter(resp.text)

        scrape_time = datetime.datetime.now()

        doc_id = get_document_id(url, original_html.encode('utf8'))

        elastic.index(index=ES_INDEX_NAME,
                      doc_type=ES_RAW_DOC_TYPE,
                      id=doc_id,
                      body={
                          'url': url,
                          'html': original_html,
                          'identifier': text_identifier,
                          'scrapeTime': scrape_time
                      })
    elif 'pdf' in resp.headers['content-type']:
        encoded = base64.encodestring(resp.content)
        doc_id = get_document_id(url, encoded)

        scrape_time = datetime.datetime.now()

        elastic.index(index=ES_INDEX_NAME,
                      doc_type=ES_RAW_DOC_TYPE,
                      id=doc_id,
                      body={
                          'url': url,
                          'pdf': {
                              '_content': encoded,
                              '_language': 'en',
                              '_content_type': 'application/pdf'
                          },
                          'scrapeTime': scrape_time
                      })

    else:
        raise Exception("Not PDF or HTML (content type {})".format(
            resp.headers['content-type']))


if __name__ == '__main__':

    #SESSION.get('https://www.google.com/foo')  # get some cookies in the session
    ES = get_index(ES_INDEX_NAME, LOGGER)
    ES.indices.put_mapping(index=ES_INDEX_NAME, doc_type=ES_RAW_DOC_TYPE,
                           body=json.load(open('legisletters/raw_letter_mapping.json', 'r')))

    for site_ in LEGISLATORS_BY_URL.keys()[100:]:
    #for site_ in ('www.schatz.senate.gov', ):
        for letter_identifier in LETTER_IDENTIFIERS:
            LOGGER.info('Scraping "%s" from Google', letter_identifier)
            for i in range(0, 50):
                urls, is_last_page = scrape_google(
                    '"{}"'.format(letter_identifier), site_, int(10*i))
                for u in urls:
                    try:
                        download_url(u, ES)
                        LOGGER.info("++OK: %s", u)
                    except Exception as err:  #pylint: disable=broad-except
                        traceback.print_exc(err)
                        LOGGER.error("--ERR: %s (%s)", u, err)

                sleeptime = random.randint(30, 60)
                LOGGER.info('Sleeping for %s seconds', sleeptime)
                time.sleep(sleeptime)
                if is_last_page:
                    LOGGER.info('Finishing "%s" after %s pages', letter_identifier, i)
                    break
