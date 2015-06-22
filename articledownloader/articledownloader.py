import requests
import re
import json
import settings
from csv import reader
from time import sleep

class ArticleDownloader:

  def __init__(self, api_key):
    self.headers = {'X-ELS-APIKEY': api_key}

  def check_els_entitlement(self, doi):
    '''
    Checks entitlement for fulltext downloads on Elsevier's API 

    :param doi: Document Object Identifier (DOI) for the paper we are checking 
    :type doi: str

    :returns: Whether or not we can download the article (True = Yes, No = False)
    :rtype: bool
    '''
    url = 'http://api.elsevier.com/content/article/entitlement/doi/' + doi
    self.headers['Accept'] = 'application/json'

    response = json.loads(requests.get(url, headers=self.headers).content)

    try:
      if response['entitlement-response']['document-entitlement']['entitled'] == True:
        return True
      else:
        return False
    except:
      return False

  def get_dois_from_search(self, query, rows=500):
    '''
    Grabs a set of unique DOIs based on a search query using the CrossRef API

    :param query: the search string 
    :type query: str 

    :param rows: the maximum number of DOIs to find 
    :type rows: int 

    :returns: the unique set of DOIs 
    :rtype: set 
    '''
    
    dois = []
    base_url = 'http://api.crossref.org/works?filter=has-license:true,has-full-text:true&query='

    if rows < 1000: #No multi-query needed
      search_url = base_url + query + '&rows=' + str(rows)
      response = json.loads(requests.get(search_url, headers=self.headers).text)
      
      for item in response["message"]["items"]:
        dois.append(item["DOI"])
      
    else: #Need to split queries
      for i in range(0,1000,rows):
        search_url = base_url + query + '&rows=' + str(min(rows - i, 1000)) + '&offset=' + str(i)
        response = json.loads(requests.get(search_url, headers=self.headers).text)

        for item in response["message"]["items"]:
          dois.append(item["DOI"])

    return set(dois)


  def get_pdf_from_doi(self, doi, writefile, mode):
    '''
    Downloads and writes a PDF article to a file, given a DOI and operating mode 

    :param doi: DOI string for the article we want to download 
    :type doi: str 

    :param writefile: file object to write to 
    :type writefile: file 

    :param mode: either 'crossref' or 'elsevier', depending on how we wish to access the file 
    :type mode: str 

    :returns: True on succesful write, False otherwise
    :rtype: bool
    '''

    if mode == 'crossref':
      base_url = 'http://api.crossref.org/works/'
      api_url = base_url + doi

      try:
        response = json.loads(requests.get(api_url, headers=self.headers).text)
        pdf_url = response['message']['link'][0]['URL']
        app_type = response['message']['link'][0]['content-type']

        if app_type == 'application/pdf':
          r = requests.get(pdf_url, stream=True, headers=self.headers)
          if r.status_code == 200:
            for chunk in r.iter_content(2048):
              writefile.write(chunk)
          return True
      except:
        return False
    if mode == 'elsevier':
      if self.check_els_entitlement(doi):
        try:
          name = re.sub('[\(\)]', '', doi)
          name = re.sub('\s+', '', name)

          pdf_url='http://api.elsevier.com/content/article/doi:' + doi + '?view=FULL'
          self.headers['Accept'] = 'application/pdf'

          r = requests.get(pdf_url, stream=True, headers=self.headers)
          if r.status_code == 200:
            for chunk in r.iter_content(2048):
              writefile.write(chunk)
            return True
        except requests.exceptions.ConnectionError:
          # API download limit exceeded
          return False

        return False

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
