'''
legisletters: collect, archive, and make searchable legislators' letters
'''

import urllib
import traceback
import datetime
import re
from bs4 import BeautifulSoup

from legisletters.constants import ES_INDEX_NAME, ES_LETTER_DOC_TYPE, LETTER_IDENTIFIERS
from legisletters.utils import get_logger, fetch_page, get_document_id, get_index

LOGGER = get_logger(__name__)

SITE = "senate.gov"
START = 0


def scrape_google(query, site, start=0):
    '''
    Scrape a query from google for a specific site.
    '''
    entity = urllib.quote(query)
    site_restrict = urllib.quote('site:%s' % site)
    url = "http://www.google.com/search?q=%s+%s&start=%d" % (entity, site_restrict, start)
    LOGGER.info("Processing %s", url)
    results = []
    response = fetch_page(url)
    soup = BeautifulSoup(response.text)
    results.extend([
        process_url_from_google(t.a['href']) for t in soup.findAll('h3', attrs={'class': 'r'})])
    return results


def process_url_from_google(url):
    '''
    Extract actual URL from the google forwarding link
    '''
    return urllib.unquote(url[7:].split('&')[0])


def extract_text_from_letter(full_page):
    '''
    Isolate the relevant section of press release + letter from a full page of
    HTML.

    Returns two tuple, the text and the identifier used.

    Raises exception if none of the identifiers work.
    '''
    letter_soup = BeautifulSoup(full_page)
    for identifier in LETTER_IDENTIFIERS:
        matcher = re.compile(identifier, re.IGNORECASE)
        matching_text = letter_soup.find(text=matcher)

        if matching_text:
            enclosing_el = matching_text.parent

            # Ascend through tags to find important enclosing block
            while enclosing_el.parent.get_text() == enclosing_el.get_text():
                enclosing_el = enclosing_el.parent

            return unicode(enclosing_el.parent), identifier

    raise Exception("Cannot identify letter in text")


if __name__ == '__main__':

    ES = get_index(ES_INDEX_NAME, LOGGER)

    for letter_identifier in LETTER_IDENTIFIERS:
        for i in range(0, 50):
            for u in scrape_google('"{}"'.format(letter_identifier), SITE, int(10*i)):
                try:
                    resp = fetch_page(u)
                    if 'html' not in resp.headers['content-type']:
                        raise Exception("Not HTML (content type {})".format(
                            resp.headers['content-type']))

                    original_html, text_identifier = extract_text_from_letter(resp.text)

                    scrape_time = datetime.datetime.now()

                    doc_id = get_document_id(u, original_html.encode('utf8'))

                    ES.index(index=ES_INDEX_NAME,
                             doc_type=ES_LETTER_DOC_TYPE,
                             id=doc_id,
                             body={
                                 'url': u,
                                 'html': original_html,
                                 'identifier': text_identifier,
                                 'scrapeTime': scrape_time
                             })
                    LOGGER.info("++OK: %s", u)
                except Exception as err:  #pylint: disable=broad-except
                    traceback.print_exc(err)
                    LOGGER.error("--ERR: %s (%s)", u, err)
