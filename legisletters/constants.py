'''
legisletters: collect, archive, and make searchable legislators' letters
'''

import re
import json
import urlparse

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

LEGISLATORS_DATA = json.load(open('legisletters/legislators-current.json', 'r'))

def _generate_legislators_for_urls(data):
    '''
    Generate a hash we can use quickly to look up which legislator applies for
    a URL.
    '''
    output = {}
    for legislator in data:
        if 'terms' in legislator:
            for term in legislator['terms']:
                if 'url' in term:
                    parsed = urlparse.urlparse(term['url'])
                    full_name = legislator['name']['official_full']
                    id_path = parsed.netloc
                    if id_path in output and full_name not in output[id_path]:
                        output[id_path].append(full_name)
                    output[id_path] = [full_name]
    return output

LEGISLATORS_BY_URL = _generate_legislators_for_urls(LEGISLATORS_DATA)
