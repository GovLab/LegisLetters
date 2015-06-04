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
]
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
