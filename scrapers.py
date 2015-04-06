'''
docstring
'''

import urllib2
import urllib
from bs4 import BeautifulSoup
import logging
import sys

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)
LOGGER.addHandler(logging.StreamHandler(sys.stderr))

def fetch_page(url):
    '''
    get page with urllib2, return text response
    '''
    request = urllib2.Request(url)
    request.add_header('User-Agent',
                       'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.1.19) '
                       'Gecko/20081202 Firefox (Debian-2.0.0.19-0etch1)')
    opener = urllib2.build_opener(urllib2.HTTPRedirectHandler())
    return opener.open(request)


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
    ?
    '''
    return url[7:].split('&')[0]

QUERY = "\"the full text of the letter is below\""
SITE = "senate.gov"
START = 0
DATA = []


def process_letter(url):
    '''
    load and process a letter from its url
    '''
    letter_page = fetch_page(url).read()
    letter_soup = BeautifulSoup(letter_page)
    text = [k for k in letter_soup.findAll(text='The full text of the letter is below:')][0]
    acc = []
    for item in text.findAllNext():
        if item.name == "footer" or \
           (item.name == 'div' and 'class' in item and item['class'] == 'footer'):
            break
        acc.append(item.text)
    #acc = map(lambda x: x.replace('&nbsp;', ' ').strip(), acc)  #pylint: disable=bad-builtin
    acc = [x.replace('&nbsp;', ' ').strip() for x in acc]
    acc = [k for k in acc if k != '']
    return "\n".join(acc)


if __name__ == '__main__':

    import codecs
    for i in range(0, 10):
        DATA.extend(scrape_google(QUERY, SITE, int(10*i)))

    for p in DATA:
        try:
            #f = codecs.open('%s/letters/%s.txt'
            #% ('/Users/sahuguet/Documents/Notebooks', p.split('/')[-1]), 'w+',
            #'utf-8')
            f = codecs.open('out.txt', 'w+', 'utf-8')
            f.write(p)
            f.write('\n')
            f.write(process_letter(p))
            f.close()
            LOGGER.info("++OK: %s", p)
        except Exception as err:  #pylint: disable=broad-except
            LOGGER.error("--ERR: %s (%s)", p, err)
        sys.stdout.flush()
