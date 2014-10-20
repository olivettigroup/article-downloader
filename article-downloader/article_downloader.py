import os
import requests
import re
import json
import csv
import time
from HTMLParser import HTMLParser

class MyHTMLParser(HTMLParser):

    def handle_starttag(self, tag, attrs):
      if tag == 'a' and ('id', 'pdfLink') in attrs:
        for attr in attrs:
          if attr[0] == 'href':
            self.download_link = attr[1]

class ArticleDownloader:

  def __init__(self,  article_path='/default_path', headers=None):
    self.article_path = article_path
    self.headers = headers
    self.piis = []
    self.dois = []
    self.xmls = []
    self.queries = []

  def get_piis_dois_from_search(self, query, mode='elsevier'):
    self.piis = []
    self.dois = []
    self.xmls = []
    if mode == 'elsevier':
      url = 'http://api.elsevier.com/content/search/scidir?query=' + query
    elif mode == 'rsc':
      url = 'http://search.crossref.org/dois?q=' + query
    else:
      print 'Valid mode required!'
      return -1
    try:
      response = requests.get(url, headers=self.headers).content
      json_response = json.loads(response)

      if mode == 'elsevier':
        for article in json_response['search-results']['entry']:
          self.piis.append(article['pii'])
        return len(self.piis)
      elif mode == 'rsc':
        for article in json_response:
          doi = article['doi']
          if doi.find('10.1039') > 0: #RSC DOI code
            doi = doi.replace('http://dx.doi.org/10.1039/', '')
            self.dois.append(doi)
        return len(self.dois)

    except requests.exceptions.ConnectionError:
      print '***API search limit exceeded!***'
      print 'Waiting 1000 seconds before trying again'
      time.sleep(1000) #API request limit exceeeded; wait and try again
      return -1
    except KeyError:
      print 'Failed search query!'
      return -1


  def get_piis_from_file(self, file):
    with open(file) as f:
      for pii in f:
        pii = re.sub('[\-\(\)]', '', pii)
        self.piis.append(pii)

  def get_xml_from_pii(self, pii):
    try:
      xml_url='http://api.elsevier.com/content/article/PII:' + pii + '?view=FULL'
      xml_response = requests.get(xml_url, headers=self.headers).content
      self.xmls.append(xml_response)
    except requests.exceptions.ConnectionError:
      print '***API download limit exceeded!***'
      print 'Waiting 1000 seconds before trying again'
      time.sleep(1000) #API request limit exceeeded; wait and try again

  def get_pdf_from_pii(self, pii, directory=os.path.dirname(__file__)+'/pdfs/'):
    try:
      name = re.sub('[\(\)]', '', pii)
      self.article_path = directory + name
      self.article_path += '.pdf'

      pdf_url='http://api.elsevier.com/content/article/PII:' + pii + '?view=FULL'
      self.headers['Accept'] = 'application/pdf'

      r = requests.get(pdf_url, stream=True, headers=self.headers)
      if r.status_code == 200:
        with open(self.article_path, 'wb') as f:
          for chunk in r.iter_content(2048):
              f.write(chunk)
          print 'Downloaded file successfully!'
    except requests.exceptions.ConnectionError:
      print '***API download limit exceeded!***'
      print 'Waiting 1000 seconds before trying again'
      time.sleep(1000) #API request limit exceeeded; wait and try again

  def download_article(self, pii=None, doi=None, regex=True, mode='elsevier', article_dir='/articles/'):
    try:
      if mode == 'elsevier':
        url = 'http://www.sciencedirect.com/science/article/pii/' + pii + '/'
      elif mode == 'rsc':
        url = 'http://pubs.rsc.org/en/content/articlepdf/1/cc/' + doi
      resp = requests.get(url, headers=self.headers)
      html = resp.content
    except:
      print "Couldn't locate download URL!"
      return

    print
    print
    print 'Downloading from: ' + url

    if doi is None:
      name = re.sub('[\(\)]', '', pii)
    else:
      name = doi

    self.article_path = os.path.dirname(__file__) + article_dir + name
    self.article_path += '.pdf'

    if regex:
      htmlparse = MyHTMLParser()
      htmlparse.download_link = None
      htmlparse.feed(html)

      if htmlparse.download_link is not None:
        download_url = htmlparse.download_link
    else:
      download_url = url

    r = requests.get(download_url, stream=True, headers=self.headers)
    if r.status_code == 200:
      with open(self.article_path, 'wb') as f:
        for chunk in r.iter_content(2048):
            f.write(chunk)
        print 'Downloaded file successfully!'

  def save_xml_data(self, xml, path):
    print 'Saved XML to: ' + path
    with open(path, 'wb') as f:
      f.write(xml)

  def load_queries_from_csv(self, csvf, limit=3, start=0, count=1):
    with open(csvf, 'rU') as f:
      reader = csv.reader(f, delimiter=',')
      for i, line in enumerate(reader):
        if i > limit:
          break

        if i < start:
          pass

        else:

          #Build search query (assume 1st column is article titles)
          title = re.sub('\[\]\=\,\.0-9\>\<\:]', '', line[0])
          title = re.sub('\(.*?\)', '', title)
          title = re.sub('\/', '\s', title)
          title = title.split()

          #filter out short words and long words
          title = [word for word in title if 3 < len(word) < 15]
          title = '+'.join(title)

          query = title

          if not count == 0:
            query += '&count=' + str(count)

          self.queries.append(query)



if __name__ == '__main__':

  downloader = ArticleDownloader(headers={'X-ELS-APIKEY': os.environ.get('API_KEY')})

  '''Use this to download PDFs from a file containing a list of PIIs'''
  #downloader.get_piis_from_file(os.path.dirname(__file__) + '/piis.txt')
  # for pii in downloader.piis:
  #   downloader.get_pdf_from_pii(pii)

  '''Use this to load search queries from a CSV'''
  downloader.load_queries_from_csv(os.path.dirname(__file__) + '/custom_search.csv', limit=1000, start=2, count=500)
  for i, query in enumerate(downloader.queries):
    print 'Search #' + str(i+1) + ': ' + query

    if downloader.get_piis_dois_from_search(query, mode='elsevier') > 0:
      # for xml, pii in zip(downloader.xmls, downloader.piis):
      #   downloader.save_xml_data(xml, os.path.dirname(__file__) + "/xmls/" + pii + '.xml')
      for pii in downloader.piis:
        downloader.get_pdf_from_pii(pii)
        #downloader.download_article(pii=pii, regex=False, mode='els', article_dir='/custom_search_pdfs/')
    else:
      print 'No PIIs or DOIs retrieved!'
