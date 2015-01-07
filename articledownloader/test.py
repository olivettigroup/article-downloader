from articledownloader import ArticleDownloader
from os import environ

downloader = ArticleDownloader(environ.get('ELS_API_KEY'))

#Single download test
downloader.get_pdf_from_pii('S0019995869905385', '')


#PII list test
downloader.get_piis_from_file('test_piis.txt')
for pii in downloader.piis:
  downloader.get_pdf_from_pii(pii, '')

#Clear stored piis
downloader.piis = []

#Search test
downloader.load_queries_from_csv('test_searches.csv', count=200)

for query in downloader.queries:
  downloader.get_piis_dois_from_search(query, mode='elsevier')

for pii in downloader.piis:
  downloader.get_pdf_from_pii(pii, '')
