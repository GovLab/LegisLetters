'''
legisletters: collect, archive, and make searchable legislators' letters
'''

ES_INDEX_NAME = 'legisletters'
ES_LETTER_DOC_TYPE = 'letter'
REQUEST_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:35.0) Gecko/20100101 Firefox/35.0'
}
LETTER_IDENTIFIERS = [
    'full text of the letter',
    'full text is below',
    'text of the full letter'
]

