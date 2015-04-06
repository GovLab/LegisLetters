'''
docstring
'''

import urllib
import logging
import sys
import re
import traceback
import json
import requests
from bs4 import BeautifulSoup

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)
LOGGER.addHandler(logging.StreamHandler(sys.stderr))

QUERY = "\"the full text of the letter is below\""
SITE = "senate.gov"
START = 0
DATA = []
RECIPIENTS, TEXT, SIGNATURES, ATTACHMENTS = ('recipients', 'text',
                                             'signatures', 'attachments')
REQUEST_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.1.19) '
                  'Gecko/20081202 Firefox (Debian-2.0.0.19-0etch1)'
}


def fetch_page(url):
    '''
    get page with requests, return text response
    '''
    #request = urllib2.Request(url)
    #request.add_header('User-Agent',
    #                   'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.1.19) '
    #                   'Gecko/20081202 Firefox (Debian-2.0.0.19-0etch1)')
    #opener = urllib2.build_opener(urllib2.HTTPRedirectHandler())
    #return opener.open(request)
    return requests.get(url, headers=REQUEST_HEADERS).text


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
    soup = BeautifulSoup(response)
    results.extend([
        process_url_from_google(t.a['href']) for t in soup.findAll('h3', attrs={'class': 'r'})])
    return results


def process_url_from_google(url):
    '''
    Extract actual URL from the google forwarding link
    '''
    return urllib.unquote(url[7:].split('&')[0])


def els2text(els):
    '''
    Convert a series BeautifulSoup elements to plaintext
    '''
    arr = []
    for element in els:
        if hasattr(element, 'text'):
            arr.append(element.text)
    return u'\n'.join(arr)


def process_letter(url):
    '''
    load and process a letter from its url

    returns None if the letter can't be processed.
    '''
    matcher = re.compile('full text of the letter', re.IGNORECASE)
    letter_page = fetch_page(url)
    letter_soup = BeautifulSoup(letter_page)
    matching_text = letter_soup.find(text=matcher)

    if not matching_text:
        return

    fulltext_el = matching_text.parent
    enclosing_el = fulltext_el.parent

    press_release = els2text(fulltext_el.previous_siblings)
    full_letter_plus_attachments = fulltext_el.next_siblings

    sections = {
        RECIPIENTS: [],
        TEXT: [],
        SIGNATURES: [],
        ATTACHMENTS: []
    }
    cur_section = RECIPIENTS

    for element in full_letter_plus_attachments:
        if not hasattr(element, 'text'):
            continue

        sections[cur_section].append(element)

        if cur_section == RECIPIENTS and 'dear' in element.text.lower():
            cur_section = TEXT
        elif cur_section == TEXT and 'sincerely' in element.text.lower():
            cur_section = SIGNATURES

    return {
        u'url': url,
        u'originalHTML': unicode(enclosing_el),
        u'pressReleaseText': press_release,
        u'recipients': els2text(sections[RECIPIENTS]),
        u'text': els2text(sections[TEXT]),
        u'signatures': els2text(sections[SIGNATURES]),
        u'attachments': els2text(sections[ATTACHMENTS])
    }


if __name__ == '__main__':

    for i in range(0, 1):
        DATA.extend(scrape_google(QUERY, SITE, int(10*i)))

    #with codecs.open('out.txt', 'w+', 'utf-8') as f:
    for p in DATA:
        try:
            sys.stdout.write(json.dumps(process_letter(p), indent=2))
            sys.stdout.write(u'\n')
            LOGGER.info("++OK: %s", p)
        except Exception as err:  #pylint: disable=broad-except
            traceback.print_exc(err)
            LOGGER.error("--ERR: %s (%s)", p, err)
        sys.stdout.flush()
