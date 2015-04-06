import urllib2
import urllib
from BeautifulSoup import BeautifulSoup
import simplejson
import logging
import sys

def fetchPage(url):
    request = urllib2.Request(url)
    request.add_header('User-Agent', 
                       'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.1.19) '
                       'Gecko/20081202 Firefox (Debian-2.0.0.19-0etch1)')
    opener = urllib2.build_opener(urllib2.HTTPRedirectHandler())
    return opener.open(request)

def scrapeGoogle(query, site, start=0):
    entity = urllib.quote(query)
    site_restrict = urllib.quote('site:%s' % site)
    URL = "http://www.google.com/search?q=%s+%s&start=%d" % (entity, site_restrict, start)
    print URL
    logging.info("Processing %s" % URL)
    results = []
    response = fetchPage(URL)
    soup = BeautifulSoup(response)
    results.extend([ processUrlFromGoogle(t.a['href']) for t in soup.findAll('h3', attrs={'class': 'r'}) ])
    return results

def processUrlFromGoogle(str):
    return str[7:].split('&')[0]

query = "\"the full text of the letter is below\""
site = "senate.gov"
start = 0
data = []
for i in range(0, 10):
    data.extend(scrapeGoogle(query, site, int(10*i)))

def processLetter(url):
    letterPage = fetchPage(url).read()
    letterSoup = BeautifulSoup(letterPage)
    t = [k for k in letterSoup.findAll(text='The full text of the letter is below:')][0]
    acc = []
    for item in t.findAllNext():
        if item.name ==  "footer" or (item.name == 'div' and 'class' in item and item['class'] == 'footer'):
            break
        acc.append(item.text)
    acc = map(lambda x: x.replace('&nbsp;', ' ').strip(), acc)
    acc = [k for k in acc if k != '']
    return "\n".join(acc)

import os
import codecs
for p in data:
    try:
        f = codecs.open('%s/letters/%s.txt' % ('/Users/sahuguet/Documents/Notebooks', p.split('/')[-1]), 'w+', 'utf-8')
        f.write(p)
        f.write('\n')
        f.write(processLetter(p))
        f.close()
        print "++OK: %s" % p
    except Exception, e:
        print "--ERR: %s" % p
        print >> sys.stderr, e
    sys.stdout.flush()