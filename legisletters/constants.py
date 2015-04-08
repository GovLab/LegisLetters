'''
legisletters: collect, archive, and make searchable legislators' letters
'''

ES_INDEX_NAME = 'legisletters'
ES_LETTER_DOC_TYPE = 'letter'
REQUEST_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.1.19) '
                  'Gecko/20081202 Firefox (Debian-2.0.0.19-0etch1)'
}
LETTER_IDENTIFIERS = [
    'full text of the letter',
    'full text is below',
    'text of the full letter'
]

