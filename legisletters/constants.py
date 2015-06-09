'''
legisletters: collect, archive, and make searchable legislators' letters
'''

import re
import urlparse
import yaml

from dateutil import parser

ES_INDEX_NAME = 'legisletters'
ES_LETTER_DOC_TYPE = 'letter'
ES_RAW_DOC_TYPE = 'raw_letter'

LETTER_IDENTIFIERS = [
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
    'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko)'
    'Chrome/41.0.2228.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko)'
    'Chrome/41.0.2224.3 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML,'
    'like Gecko) Chrome/37.0.2062.124 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like'
    'Gecko) Chrome/37.0.2049.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 4.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko)'
    'Chrome/37.0.2049.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko)'
    'Chrome/36.0.1985.67 Safari/537.36',
    'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko)'
    'Chrome/36.0.1985.67 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; AS; rv:11.0) like Gecko'
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
    data = yaml.load(open('congress-legislators/legislators-current.yaml', 'r'),
                     Loader=yaml.CLoader)
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
    committees = yaml.load(open('congress-legislators/committees-current.yaml', 'r'),
                           Loader=yaml.CLoader)
    membership = yaml.load(open('congress-legislators/committee-membership-current.yaml', 'r'),
                           Loader=yaml.CLoader)
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
