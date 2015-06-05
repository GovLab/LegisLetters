'''
legisletters: collect, archive, and make searchable legislators' letters
'''

import re
import json
import urlparse

from dateutil import parser

ES_INDEX_NAME = 'legisletters'
ES_LETTER_DOC_TYPE = 'letter'
ES_RAW_DOC_TYPE = 'raw_letter'
REQUEST_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:35.0) Gecko/20100101 Firefox/35.0'
}
LETTER_IDENTIFIERS = [
    'full text of the letter',
    'full text is below',
    'text of the full letter',
    'text of the letter',
    'click here to view the letter',
]
UA_STRINGS = (
    'Mozilla/5.0 (Windows NT 6.3; rv:36.0) Gecko/20100101 Firefox/36.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10; rv:33.0) Gecko/20100101 Firefox/33.0',
    'Mozilla/5.0 (X11; Linux i586; rv:31.0) Gecko/20100101 Firefox/31.0',
    'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:31.0) Gecko/20130401 Firefox/31.0',
    'Mozilla/5.0 (Windows NT 5.1; rv:31.0) Gecko/20100101 Firefox/31.0',
    'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:29.0) Gecko/20120101 Firefox/29.0',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:25.0) Gecko/20100101 Firefox/29.0',
    'Mozilla/5.0 (X11; OpenBSD amd64; rv:28.0) Gecko/20100101 Firefox/28.0',
    'Mozilla/5.0 (X11; Linux x86_64; rv:28.0) Gecko/20100101 Firefox/28.0',
    'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2224.3 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.124 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2049.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 4.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2049.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.67 Safari/537.36',
    'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.67 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; AS; rv:11.0) like Gecko',
    'Mozilla/5.0 (compatible, MSIE 11, Windows NT 6.3; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (compatible; MSIE 10.6; Windows NT 6.1; Trident/5.0; InfoPath.2; SLCC1; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729; .NET CLR 2.0.50727) 3gpp-gba UNTRUSTED/1.0',
    'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0)',
    'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)',
    'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/5.0)',
    'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/4.0; InfoPath.2; SV1; .NET CLR 2.0.50727; WOW64)',
    'Mozilla/5.0 (compatible; MSIE 10.0; Macintosh; Intel Mac OS X 10_7_3; Trident/6.0)',
    'Mozilla/4.0 (Compatible; MSIE 8.0; Windows NT 5.2; Trident/6.0)',
    'Mozilla/4.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/5.0)',
    'Mozilla/1.22 (compatible; MSIE 10.0; Windows 3.1)',
    'Opera/9.80 (X11; Linux i686; Ubuntu/14.10) Presto/2.12.388 Version/12.16',
    'Opera/9.80 (Windows NT 6.0) Presto/2.12.388 Version/12.14',
    'Mozilla/5.0 (Windows NT 6.0; rv:2.0) Gecko/20100101 Firefox/4.0 Opera 12.14',
    'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.0) Opera 12.14',
    'Opera/12.80 (Windows NT 5.1; U; en) Presto/2.10.289 Version/12.02',
)

END_RECIPIENTS_RE = re.compile(r'(>\W*dear[^:,<]+[^:<]|>\W*to the[^:,<]+[^:<]|'
                               r'>\W*mrs?\.[^:,]+[:,]\s*<)', re.IGNORECASE)
END_TEXT_RE = re.compile(r'(we appreciate|sincerely|thank you|look forward to|'
                         r'we hope|respectfully yours|we ask that you|urge you|'
                         r'best wish|we all share|we are committed|keep us informed|'
                         r'for these reasons|we urge'
                         r')([^<]*)', re.IGNORECASE)
#END_TEXT_SECONDARY_RE = re.compile(r'(###)([^:,<]*)', re.IGNORECASE)
END_SIGNATURES_RE = re.compile(r'cc:|###|<footer|<script|-\d+-', re.IGNORECASE)


def _generate_legislator_data():
    '''
    Generate legislator data, a dict with the legislators bioguide ID as a key.
    '''
    data = json.load(open('legisletters/legislators-current.json', 'r'))
    output = {}
    for legislator in data:
        entry = {
            'name': legislator['name'],
            'bio': legislator['bio'],
            'id': legislator['id'],
            'terms': []
        }
        for term in legislator['terms']:
            start = parser.parse(term['start'])
            end = parser.parse(term['end'])
            entry['terms'].append((start, end, term))
        output[legislator['id']['bioguide']] = entry

    return output


def _generate_legislators_for_urls():
    '''
    Generate a hash we can use quickly to look up which legislator applies for
    a URL.
    '''
    legislators = _generate_legislator_data()
    committees = json.load(open('legisletters/committees-current.json', 'r'))
    membership = json.load(open('legisletters/committee-membership-current.json', 'r'))
    output = {}

    # generate a dict with the bioguide of every current chair by thomas_id
    for committee in committees:
        thomas_id = committee['thomas_id']
        majority_netloc = urlparse.urlparse(committee['url']).netloc
        if 'minority_url' in committee:
            minority_netloc = urlparse.urlparse(committee['minority_url']).netloc
        else:
            minority_netloc = None
        for member in membership[thomas_id]:
            if 'title' in member and member['title'].lower().startswith('chair'):
                output[majority_netloc] = legislators[member['bioguide']]
            elif 'title' in member and member['title'].lower().startswith('ranking member'):
                if minority_netloc:
                    output[minority_netloc] = legislators[member['bioguide']]

    for bioguide, legislator in legislators.iteritems():
        for _, _, term in legislator['terms']:
            if 'url' in term:
                parsed = urlparse.urlparse(term['url'])
                netloc = parsed.netloc
                if netloc == 'www.house.gov':
                    continue

                output[netloc] = legislators[bioguide]

    return output

LEGISLATORS_BY_URL = _generate_legislators_for_urls()
