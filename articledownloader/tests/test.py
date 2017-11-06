from articledownloader.articledownloader import ArticleDownloader
from os import environ
from unittest import TestCase
from tempfile import TemporaryFile

class Tester(TestCase):
  def setUp(self):
    self.downloader = ArticleDownloader(environ.get('ELS_API_KEY'))
    self.doi = '10.1016/j.nantod.2008.10.014'
    self.pdf_file = TemporaryFile(mode='wb')

    self.txt_file = TemporaryFile(mode='rb+')
    self.txt_file.write('10.1016/j.nantod.2008.10.014')

    self.csv_file = TemporaryFile(mode='rb+')
    self.csv_file.write('nanomaterial+synthesis,')
    self.csv_file.write('battery+electrode,')

  def test_download(self):
    #Single download test
    self.downloader.get_pdf_from_doi(self.doi, self.pdf_file, 'elsevier')

  def test_abstract_download(self):
    self.downloader.get_abstract_from_doi(self.doi, 'elsevier')

  def test_search(self):
    #Search test
    queries = self.downloader.load_queries_from_csv(self.csv_file)
    for query in queries:
      self.downloader.get_dois_from_search(query, rows=10)

  def tearDown(self):
    pass
