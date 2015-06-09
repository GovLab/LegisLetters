'''
legisletters: collect, archive, and make searchable legislators' letters
'''

import traceback
import datetime
import re
import requests
import json
import base64
import random
import urlparse
import time

from bs4 import BeautifulSoup

from legisletters.constants import (ES_INDEX_NAME, ES_RAW_DOC_TYPE, UA_STRINGS,
                                    LETTER_IDENTIFIERS, LEGISLATORS_BY_URL)
from legisletters.utils import (get_logger, get_index, strip_script_from_soup,
                                add_raw_doc, have_raw_url)

LOGGER = get_logger(__name__)
SESSIONS = []
for ua_string in UA_STRINGS:
    SESSIONS.append(requests.session())
    SESSIONS[-1].headers.update({'User-Agent': ua_string})


def scrape_legislator(netloc, terms): #pylint: disable=too-many-locals,too-many-branches,too-many-statements
    '''
    Scrape a single legislators website, for each of the terms
    (should be a list).

    Yield URLs from search.
    '''
    blacklist = 'www.epw.senate.gov'
    if netloc in blacklist:
        return

    session = random.choice(SESSIONS)
    base_url = 'http://' + netloc
    base_response = session.get(base_url)
    base_response.raise_for_status()
    base_soup = BeautifulSoup(base_response.text)

    # Handle idiotic meta-refresh redirects
    # There can be many of them!
    while True:
        redirect = None
        for meta_tag in base_soup.select('meta'):
            if meta_tag.get('http-equiv') == 'refresh':
                redirect = meta_tag.get('content').split('URL=')[1]
                break
        if redirect:
            LOGGER.info("Meta-refresh redirect (wow!) %s -> %s", base_url, redirect)
            base_url = redirect
            base_response = session.get(base_url)
            base_response.raise_for_status()
            base_soup = BeautifulSoup(base_response.text)
        else:
            break

    # Identify the element where user would enter their search input
    query_input = base_soup.select('input[name=q]')
    if not query_input:
        for input_el in base_soup.select('input'):
            if input_el.get('name', '').lower().startswith('search'):
                query_input = input_el
                break
            elif input_el.get('name', '').lower().startswith('keywords'):
                query_input = input_el
                break
    else:
        query_input = query_input[0]

    if not query_input:
        raise Exception("Could not find query input on {}".format(netloc))

    for parent in query_input.parents:
        if parent.name == 'form':
            enclosing_form = parent
            break

    if not enclosing_form:
        raise Exception("Could not find enclosing search form on {}".format(netloc))

    form_action = urlparse.urljoin(base_url, enclosing_form.get('action', base_url))
    form_action = form_action.split('?')[0]  # horrible form code, when a query
                                             # param was embedded in an action.
                                             # Thanks Rod Frelinghuysen!
    form_method = enclosing_form.get('method', 'get')

    form_data = {}
    for extra_input in enclosing_form.findAll('input'):
        if extra_input != query_input and extra_input.get('name'):
            form_data[extra_input.get('name')] = extra_input.get('value', '')

    for term in terms:
        form_data[query_input.get('name')] = '"{}"'.format(term)

        LOGGER.info('Requesting %s via %s with %s', form_action, form_method,
                    form_data)
        if form_method == 'post':
            list_response = session.request(form_method, form_action, data=form_data)
        else:
            list_response = session.request(form_method, form_action, params=form_data)
        list_response.raise_for_status()
        list_soup = BeautifulSoup(list_response.text)

        # Yield each link we find, break out if there aren't any -- keep looping
        # while there are more pages
        prior_links = []
        while True:
            time.sleep(1)
            links = list_soup.select('.search-result a')
            links.extend(list_soup.select('.search-results a'))
            links.extend(list_soup.select('#search-result a'))
            links.extend(list_soup.select('#search-results a'))
            links.extend(list_soup.select('.gsMainTable a'))

            # Filter out links that are actually page numbers/next/previous
            links = [link for link in links if not re.search(
                r'^\W*(next|previous|\d+)\W*$', link.get_text(), re.IGNORECASE)]

            if not links:
                if re.search(r'did\s+not\s+match|'
                             r'no\s+(search\s+)?(results|documents|records)|'
                             r'results\s+-\s+of\s+\.|'
                             r'not be found',
                             list_response.text, re.IGNORECASE):
                    break
                elif re.search(r'googleSearchIframeName|'
                               r'/www.google.com/cse/cse.js',
                               list_response.text, re.IGNORECASE):
                    LOGGER.info('Skipping %s, they use Google search', netloc)
                    return
                else:
                    #print base_url
                    #import pdb
                    #pdb.set_trace()
                    break

            # Sometimes the "next" button gives us a page with a next button
            # and the same links.
            if prior_links == links:
                break

            for link in links:
                yield term, urlparse.urljoin(base_url, link.get('href'))

            next_text = list_soup.find(text=re.compile(r'^\W*next\W*$', re.IGNORECASE))
            if not next_text:
                break

            next_link = None
            for parent in next_text.parents:
                if parent.name == 'a':
                    next_link = parent
                    break
            if next_link == None:
                break

            next_url = urlparse.urljoin(base_url, next_link.get('href'))
            LOGGER.info('Requesting %s', next_url)

            list_response = session.get(next_url)
            list_response.raise_for_status()
            list_soup = BeautifulSoup(list_response.text)
            prior_links = links


#def scrape_google(query, site, start=0):
#    '''
#    Scrape a query from google for a specific site.
#
#    Returns a list of results and a bool of whether this is the last page.
#    '''
#    entity = urllib.quote(query)
#    site_restrict = urllib.quote('site:%s' % site)
#    url = "https://www.google.com/search?q=%s+%s&start=%d" % (entity, site_restrict, start)
#    LOGGER.info("Processing %s", url)
#    results = []
#    response = random.choice(SESSIONS).get(url)
#    if 'Our systems have detected unusual traffic from your computer network.' in response.text:
#        LOGGER.warn("Rate-limited by Google, doing something else")
#        return [], False
#    if "No results found for" in response.text:
#        return results, True
#    soup = BeautifulSoup(response.text)
#    results.extend(e(t.a['href']) for t in soup.findAll('h3', attrs={'class': 'r'})])
#    is_last_page_ = 'Next</span' not in response.text
#    return results, is_last_page_


#def process_url_from_google(url):
#    '''
#    Extract actual URL from the google forwarding link
#    '''
#    #return urllib.unquote(url[7:].split('&')[0])
#    # If we use https, google gives us real links
#    return url


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

            strip_script_from_soup(enclosing_el)
            return unicode(enclosing_el.parent)

    raise Exception("Cannot identify letter in text")


def download_url(term, url, elastic):
    '''
    Download raw content for URL
    '''
    resp = random.choice(SESSIONS).get(url)
    scrape_time = datetime.datetime.now()
    if 'html' in resp.headers['content-type']:
        original_html = extract_text_from_letter(resp.text)
        add_raw_doc(elastic, {
            'url': url,
            'html': original_html,
            'identifier': term,
            'scrapeTime': scrape_time
        }, LOGGER)
    elif 'pdf' in resp.headers['content-type']:
        encoded = base64.encodestring(resp.content)
        add_raw_doc(elastic, {
            'url': url,
            'pdf': {
                '_content': encoded,
                '_language': 'en',
                '_content_type': 'application/pdf'
            },
            'scrapeTime': scrape_time
        }, LOGGER)
    else:
        raise Exception("Not PDF or HTML (content type {})".format(
            resp.headers['content-type']))


if __name__ == '__main__':

    #SESSION.get('https://www.google.com/foo')  # get some cookies in the session
    ES = get_index(ES_INDEX_NAME, LOGGER)
    ES.indices.put_mapping(index=ES_INDEX_NAME, doc_type=ES_RAW_DOC_TYPE,
                           body=json.load(open('mappings/raw_letter_mapping.json', 'r')))

    for site_ in LEGISLATORS_BY_URL.keys():
        try:
            for t, u in scrape_legislator(site_, LETTER_IDENTIFIERS):
                if 'searchresults' in u.lower():  # skip search pages
                    continue
                if have_raw_url(ES, u):
                    LOGGER.info("Already downloaded %s", u)
                else:
                    download_url(t, u, ES)
                LOGGER.info("++OK: %s", u)
        except Exception as err:  #pylint: disable=broad-except
            traceback.print_exc(err)
            LOGGER.error("--ERR: %s (%s)", u, err)

                #urls, is_last_page = scrape_google(
                #    '"{}"'.format(letter_identifier), site_, int(10*i))
                #for u in urls:
                #    try:
                #        if 'searchresults' in u.lower():  # skip search pages
                #            continue
                #        download_url(u, ES)
                #        LOGGER.info("++OK: %s", u)
                #    except Exception as err:  #pylint: disable=broad-except
                #        traceback.print_exc(err)
                #        LOGGER.error("--ERR: %s (%s)", u, err)

                #sleeptime = random.randint(30, 60)
                #LOGGER.info('Sleeping for %s seconds', sleeptime)
                #time.sleep(sleeptime)
                #if is_last_page:
                #    LOGGER.info('Finishing "%s" after %s pages', letter_identifier, i)
                #    break
