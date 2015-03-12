from articledownloader.articledownloader import ArticleDownloader
from os import environ
from unittest import TestCase
from tempfile import TemporaryFile

class Tester(TestCase):
  def setUp(self):
    self.downloader = ArticleDownloader('NO_API_KEY')
    self.pii = 'S0019995869905385'
    self.pdf_file = TemporaryFile(mode='wb')

    self.txt_file = TemporaryFile(mode='rb+')
    self.txt_file.write('S0019995869905385')

    self.csv_file = TemporaryFile(mode='rb+')
    self.csv_file.write('nanomaterial+synthesis,')
    self.csv_file.write('battery+electrode,')

  def test_download(self):
    #Single download test
    self.downloader.get_pdf_from_pii(self.pii, self.pdf_file)

  def test_entitlement(self):
    #Test entitlement
    self.assertFalse(self.downloader.check_els_entitlement(self.pii))

  def test_search(self):
    #Search test
    queries = self.downloader.load_queries_from_csv(self.csv_file, count=5)

    for query in queries:
      self.downloader.get_piis_from_search(query)

  def tearDown(self):
    pass
