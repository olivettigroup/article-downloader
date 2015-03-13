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
      search_url = 'http://api.crossref.org/works?filter=has-license:true,has-full-text:true&query=' + query + '&rows=' + str(rows)
      response = json.loads(requests.get(search_url, headers=self.headers).text)
      print response
      dois = []

      for item in response["message"]["items"]:
        dois.append(item["DOI"])

      return set(dois)

  def get_pdf_from_doi(self, doi, writefile, mode):
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
