import requests
import re
import json
import scrapers
from autologging import logged, traced
from csv import reader
from time import sleep

@logged
class ArticleDownloader:

  def __init__(self, els_api_key=None, crf_api_key=None):
    '''
    Initialize and set up API keys

    :param els_api_key: API key for Elsevier
    :type els_api_key: str
    :param crf_api_key: API key for CrossRef
    :type crf_api_key: str
    '''
    self.els_api_key = els_api_key
    self.crf_api_key = crf_api_key

  @traced
  def check_els_entitlement(self, doi):
    '''
    Checks entitlement for fulltext downloads on Elsevier's API

    :param doi: Document Object Identifier (DOI) for the paper we are checking
    :type doi: str

    :rtype: bool
    :returns: Whether or not we can download the article (True = Yes, No = False)
    '''
    url = 'http://api.elsevier.com/content/article/entitlement/doi/' + doi
    headers = {
      'X-ELS-APIKEY': self.els_api_key,
      'Accept': 'application/json'
    }

    response = requests.get(url, headers=headers).json()

    try:
      if response['entitlement-response']['document-entitlement']['entitled'] == True:
        return True
      else:
        return False
    except:
      return False

  @traced
  def get_dois_from_search(self, query, rows=500):
    '''
    Grabs a set of unique DOIs based on a search query using the CrossRef API

    :param query: the search string
    :type query: str

    :param rows: the maximum number of DOIs to find
    :type rows: int

    :returns: the unique set of DOIs as a list
    :rtype: list
    '''

    dois = []
    base_url = 'http://api.crossref.org/works?filter=has-license:true,has-full-text:true&query='
    max_rows = 1000 #Defined by CrossRef API

    headers = {
      'Accept': 'application/json'
    }

    if rows <= max_rows: #No multi-query needed
      search_url = base_url + query + '&rows=' + str(rows)
      response = requests.get(search_url, headers=headers).json()

      for item in response["message"]["items"]:
        dois.append(item["DOI"])

    else: #Need to split queries
      stop_query = False
      offset = 0

      while not stop_query:
        search_url = base_url + query + '&rows=' + str(max_rows) + '&offset=' + str(offset)
        response = requests.get(search_url, headers=headers)
        try:
          j_response = response.json()
          offset += max_rows
          if len(dois) >= rows: stop_query = True
          for item in j_response["message"]["items"]: dois.append(item["DOI"])
        except Exception, e:
          self.__logger.warning(str(e) + str(response.text))
          stop_query = True

    return list(set(dois))

  @traced
  def get_dois_from_journal_issn(self, issn, rows=500, pub_after=2000):
    '''
    Grabs a set of unique DOIs based on a journal ISSN using the CrossRef API

    :param issn: The ISSN of the journal
    :type issn: str

    :param rows: the maximum number of DOIs to find
    :type rows: int

    :param pub_after: the minimum publication year for DOIs returned
    :type pub_after: int

    :returns: the unique set of DOIs as a list
    :rtype: list
    '''

    dois = []
    base_url = 'http://api.crossref.org/journals/' + issn + '/works?filter=has-license:true,has-full-text:true,from-pub-date:' + str(pub_after)
    max_rows = 1000 #Defined by CrossRef API

    headers = {
      'Accept': 'application/json'
    }

    if rows <= max_rows: #No multi-query needed
      search_url = str(base_url) + '&rows=' + str(rows)
      response = requests.get(search_url, headers=headers).json()

      for item in response["message"]["items"]:
        dois.append(item["DOI"])

    else: #Need to split queries
      stop_query = False
      offset = 0

      while not stop_query:
        search_url = base_url + '&rows=' + str(max_rows) + '&offset=' + str(offset)
        response = requests.get(search_url, headers=headers)
        try:
          j_response = response.json()
          offset += max_rows
          if len(dois) >= rows: stop_query = True
          for item in j_response["message"]["items"]: dois.append(item["DOI"])
        except Exception, e:
          self.__logger.warning(str(e) + str(response.text))
          stop_query = True

    return list(set(dois))


  @traced
  def get_pdf_from_doi(self, doi, writefile, mode):
    '''
    Downloads and writes a PDF article to a file, given a DOI and operating mode

    :param doi: DOI string for the article we want to download
    :type doi: str

    :param writefile: file object to write to
    :type writefile: file

    :param mode: either 'crossref' | 'elsevier' | 'rsc' | 'springer', depending on how we wish to access the file
    :type mode: str

    :returns: True on successful write, False otherwise
    :rtype: bool
    '''

    if mode == 'crossref':
      base_url = 'http://api.crossref.org/works/'
      api_url = base_url + doi

      headers = {
        'CR-Clickthrough-Client-Token': self.crf_api_key,
        'Accept': 'application/json'
      }

      try:
        response = json.loads(requests.get(api_url, headers=headers).text)
        pdf_url = response['message']['link'][0]['URL']
        app_type = str(response['message']['link'][0]['content-type'])

        if app_type in ['application/pdf', 'unspecified']:
          headers['Accept'] = 'application/pdf'
          r = requests.get(pdf_url, stream=True, headers=headers)
          if r.status_code == 200:
            for chunk in r.iter_content(2048):
              writefile.write(chunk)
            return True
      except:
        return False
      return False

    if mode == 'elsevier':
      if self.check_els_entitlement(doi):
        try:
          pdf_url='http://api.elsevier.com/content/article/doi:' + doi + '?view=FULL'
          headers = {
            'X-ELS-APIKEY': self.els_api_key,
            'Accept': 'application/pdf'
          }

          r = requests.get(pdf_url, stream=True, headers=headers)
          if r.status_code == 200:
            for chunk in r.iter_content(2048):
              writefile.write(chunk)
            return True
        except:
          # API download limit exceeded
          return False
      return False

    if mode == 'rsc':
      scraper = scrapers.RSC()
      scrape_url = 'http://dx.doi.org/' + doi
      download_url = None

      r = requests.get(scrape_url)
      if r.status_code == 200:
        scraper.feed(r.content)

        if scraper.download_link is not None:
          download_url = scraper.download_link

      if download_url is not None:
        headers = {
          'Accept': 'application/pdf'
        }
        r = requests.get(download_url, stream=True, headers=headers)
        if r.status_code == 200:
          try:
            for chunk in r.iter_content(2048):
              writefile.write(chunk)
            return True
          except:
            return False

      return False

    if mode == 'ecs':
      scraper = scrapers.ECS()
      scrape_url = 'http://dx.doi.org/' + doi
      download_url = None

      r = requests.get(scrape_url)
      if r.status_code == 200:
        scraper.feed(r.content)

        if scraper.download_link is not None:
          download_url = scraper.download_link

      if download_url is not None:
        headers = {
          'Accept': 'application/pdf'
        }
        r = requests.get(download_url, stream=True, headers=headers)
        if r.status_code == 200:
          try:
            for chunk in r.iter_content(2048):
              writefile.write(chunk)
            return True
          except:
            return False

      return False

    if mode == 'springer':
      base_url = 'http://link.springer.com/'
      api_url = base_url + doi + '.pdf'

      try:
        headers = {
          'Accept': 'application/pdf'
        }
        r = requests.get(api_url, stream=True, headers=headers)
        if r.status_code == 200:
          for chunk in r.iter_content(2048):
            writefile.write(chunk)
            return True
      except:
        return False
      return False

    return False

  @traced
  def get_abstract_from_doi(self, doi, mode):
    '''
    Returns abstract as a unicode string given a DOI

    :param doi: DOI string for the article we want to grab metadata for
    :type doi: str

    :param mode: Only supports 'elsevier' for now
    :type mode: str

    :returns: An abstract (or None on failure)
    :rtype: unicode
    '''

    if mode == 'elsevier':
      if self.check_els_entitlement(doi):
        try:
          url='http://api.elsevier.com/content/article/doi:' + doi + '?view=FULL'

          headers = {
            'X-ELS-APIKEY': self.els_api_key,
            'Accept': 'application/json'
          }

          r = requests.get(url, headers=headers)
          if r.status_code == 200:
            abstract = unicode(json.loads(r.text)['full-text-retrieval-response']['coredata']['dc:description'])
            return abstract
        except:
          # API download limit exceeded or no abstract exists
          return None

        return None

  @traced
  def get_title_from_doi(self, doi, mode):
    '''
    Returns title of an article as a unicode string given a DOI

    :param doi: DOI string for the article we want to grab metadata for
    :type doi: str

    :param mode: Only supports 'crossref' for now
    :type mode: str

    :returns: An abstract (or None on failure)
    :rtype: unicode
    '''

    if mode == 'crossref':
      try:
        url='http://api.crossref.org/works/' + doi
        headers = {
          'X-ELS-APIKEY': self.els_api_key,
          'Accept': 'application/json'
        }

        r = requests.get(url, headers=headers)
        if r.status_code == 200:
          title = unicode(r.json()['message']['title'][0])
          return title
      except:
        # API download limit exceeded or no title exists
        return None

    return None

  @traced
  def load_queries_from_csv(self, csvf):
    '''
    Loads a list of queries from a CSV file

    :param csvf: file object containing a CSV file with one query per line
    :type csvf: file

    :returns: a list of queries, processed to be insertable into REST API (GET) calls
    :rtype: list
    '''

    csvf.seek(0)
    csvreader = reader(csvf, delimiter=',')
    queries = []
    for line in csvreader:
      #Build search query (assume 1st column is queries)
      query = re.sub('\[\]\=\,\.0-9\>\<\:]', '', line[0])
      query = re.sub('\(.*?\)', '', query)
      query = re.sub('\/', '\s', query)
      query = query.split()

      #filter out short words and long words
      query = [word for word in query if 3 < len(word) < 15]
      query = '+'.join(query)

      final_query = query
      queries.append(final_query)
    return queries
