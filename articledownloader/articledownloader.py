import requests
import re
import json
import settings
from csv import reader
from time import sleep

class ArticleDownloader:

  def __init__(self, api_key):
    self.headers = {'X-ELS-APIKEY': api_key}

  def get_piis_from_search(self, query):
    url = 'http://api.elsevier.com/content/search/scidir?query=' + query
    piis = []

    try:
      self.headers['Accept'] = 'application/json'
      response = requests.get(url, headers=self.headers).content
      json_response = json.loads(response)

      for article in json_response['search-results']['entry']:
        if article['pii'] not in self.piis:
          piis.append(article['pii'])

      piis = set(piis) #Guarantee uniqueness of IDs
      return piis

    except requests.exceptions.ConnectionError:
      # API search limit exceeded!
      return []
    except KeyError:
      # Failed search query
      return []

  def check_els_entitlement(self, pii):
    url = 'http://api.elsevier.com/content/article/entitlement/pii/' + pii
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
    dois = []

    for item in response["message"]["items"]:
      dois.append(item["DOI"])

    return dois

  def get_pdf_from_doi(self, doi, writefile):
    base_url = 'http://api.crossref.org/works/'
    api_url = base_url + doi

    response = json.loads(requests.get(api_url, headers=self.headers).text)
    print response
    pdf_url = response['message']['link'][0]['URL']
    app_type = response['message']['link'][0]['content-type']

    if app_type == 'application/pdf':
      r = requests.get(pdf_url, stream=True, headers=self.headers)
      if r.status_code == 200:
        for chunk in r.iter_content(2048):
          writefile.write(chunk)
      return True

    return False


  def get_pdf_from_pii(self, pii, writefile):
    if self.check_els_entitlement(pii):
      try:
        name = re.sub('[\(\)]', '', pii)
        name = re.sub('\s+', '', name)

        pdf_url='http://api.elsevier.com/content/article/PII:' + pii + '?view=FULL'
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



  def load_queries_from_csv(self, csvf, limit=500, start=0, count=1):
    csvf.seek(0)
    csvreader = reader(csvf, delimiter=',')
    queries = []
    for i, line in enumerate(csvreader):
      if i > limit:
        break

      if i >= start:
        #Build search query (assume 1st column is article titles)
        title = re.sub('\[\]\=\,\.0-9\>\<\:]', '', line[0])
        title = re.sub('\(.*?\)', '', title)
        title = re.sub('\/', '\s', title)
        title = title.split()

        #filter out short words and long words
        title = [word for word in title if 3 < len(word) < 15]
        title = '+'.join(title)

        query = title

        if 0 < count < 100:
          query += '&count=' + str(count)
          queries.append(query)
        elif count > 100:
          for j in range(0, count, 100):
            split_query = query + '&count=100&start=' + str(j)
            queries.append(split_query)

    return queries
