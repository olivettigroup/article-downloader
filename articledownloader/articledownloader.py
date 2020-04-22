import requests
from requests.utils import quote
import re
import json
from articledownloader import scrapers
from autologging import logged, traced
from csv import reader
from time import sleep

@logged
class ArticleDownloader:

  def __init__(self, els_api_key=None, sleep_sec=1, timeout_sec=30):
    '''
    Initialize and set up API keys

    :param els_api_key: API key for Elsevier (for Elsevier's API)
    :type els_api_key: str
    :param sleep_sec: Sleep time between API calls (default = 1s)
    :type sleep_sec: int
    :param timeout_sec: Max time before timeout (default = 30s)
    :type timeout_sec: int
    '''
    self.els_api_key = els_api_key
    self.sleep_sec = sleep_sec
    self.timeout_sec = timeout_sec

  @traced
  def get_dois_from_search(self, query, rows=500, mailto="null@null.com"):
    '''
    Grabs a set of unique DOIs based on a search query using the CrossRef API

    :param query: the search string
    :type query: str

    :param rows: the maximum number of DOIs to find
    :type rows: int

    :param mailto: mailto address for API
    :type rows: str

    :returns: the unique set of DOIs as a list
    :rtype: list
    '''

    dois = []
    base_url = 'https://api.crossref.org/works?query='
    max_rows = 1000 #Defined by CrossRef API

    headers = {
      'Accept': 'application/json',
      'User-agent': 'mailto:' + mailto
    }

    if rows <= max_rows: #No multi-query needed
      search_url = base_url + query + '&rows=' + str(rows)
      response = requests.get(search_url, headers=headers, timeout=self.timeout_sec).json()

      for item in response["message"]["items"]:
        dois.append(item["DOI"])

    else: #Need to split queries
      cursor = "*"
      keep_paging = True
      while (keep_paging):
        sleep(self.sleep_sec)
        r = requests.get(base_url + query + "&rows=" + str(max_rows) + "&cursor=" + cursor,
                         headers=headers, timeout=self.timeout_sec)
        cursor = quote(r.json()['message']['next-cursor'], safe='')
        if len(r.json()['message']['items']) == 0:
          keep_paging = False

        for item in r.json()['message']['items']:
          dois.append(item['DOI'])

    return list(set(dois))

  @traced
  def get_dois_from_journal_issn(self, issn, rows=500, pub_after=2000, mailto="null@null.com"):
    '''
    Grabs a set of unique DOIs based on a journal ISSN using the CrossRef API

    :param issn: The ISSN of the journal
    :type issn: str

    :param rows: the maximum number of DOIs to find
    :type rows: int

    :param pub_after: the minimum publication year for DOIs returned
    :type pub_after: int

    :param mailto: mailto address for API
    :type rows: str

    :returns: the unique set of DOIs as a list
    :rtype: list
    '''

    dois = []
    base_url = 'https://api.crossref.org/journals/' + issn + '/works?filter=from-pub-date:' + str(pub_after)
    max_rows = 1000 #Defined by CrossRef API

    headers = {
      'Accept': 'application/json',
      'User-agent': 'mailto:' + mailto
    }

    if rows <= max_rows: #No multi-query needed
      search_url = str(base_url) + '&rows=' + str(rows)
      response = requests.get(search_url, headers=headers, timeout=self.timeout_sec).json()

      for item in response["message"]["items"]:
        dois.append(item["DOI"])

    else: #Need to split queries
      cursor = "*"
      keep_paging = True
      while (keep_paging):
        sleep(self.sleep_sec)
        r = requests.get(base_url + "&rows=" + str(max_rows) + "&cursor=" + cursor,
                         headers=headers, timeout=self.timeout_sec)
        cursor = quote(r.json()['message']['next-cursor'], safe='')
        if len(r.json()['message']['items']) == 0:
          keep_paging = False

        for item in r.json()['message']['items']:
          dois.append(item['DOI'])

    return list(set(dois))

  @traced
  def get_metadata_from_doi(self, doi, mailto="null@null.com"):
    base_url = 'https://api.crossref.org/works/' + str(doi)

    headers = {
      'Accept': 'application/json',
      'User-agent': 'mailto:' + mailto
    }

    search_url = str(base_url)
    response = requests.get(search_url, headers=headers, timeout=self.timeout_sec).json()

    item = response["message"]
    metadata_record = None
    try:
      if "volume" in item: 
        volume = item["volume"]
      else:
        volume = None

      if "published-print" in item: 
        year = item['published-print']['date-parts'][0][0] 
      else:
        year = None

      if "issue" in item: 
        issue = item["issue"]
      else:
        issue = None

      if "page" in item: 
        page = item["page"]
      else:
        page = None

      metadata_record = {
        "doi": item["DOI"],
        "issn": item["ISSN"][0],
        "title": item["title"][0],
        "prefix": item["prefix"],
        "journal": item["container-title"][0],
        "publisher": item["publisher"],
        "volume": volume,
        "issue": issue,
        "page": page,
        "year": year,
        "num_references": item['references-count'],
        "times_cited": item['is-referenced-by-count']
      }
    except:
      pass

    return metadata_record

  @traced
  def get_metadata_from_journal_issn(self, issn, rows=500, pub_after=2000, mailto="null@null.com"):
    '''
    Grabs metadata based on a journal ISSN using the CrossRef API

    :param issn: The ISSN of the journal
    :type issn: str

    :param rows: the maximum number of DOIs to find
    :type rows: int

    :param pub_after: the minimum publication year for DOIs returned
    :type pub_after: int

    :param mailto: mailto address for API
    :type rows: str

    :returns: the metadata for the articles according to this ISSN
    :rtype: list
    '''

    metadata_records = []
    base_url = 'https://api.crossref.org/journals/' + issn + '/works?filter=from-pub-date:' + str(pub_after)
    max_rows = 1000 #Defined by CrossRef API

    headers = {
      'Accept': 'application/json',
      'User-agent': 'mailto:' + mailto
    }

    if rows <= max_rows: #No multi-query needed
      search_url = str(base_url) + '&rows=' + str(rows)
      response = requests.get(search_url, headers=headers, timeout=self.timeout_sec).json()

      for item in response["message"]["items"]:
        try:
          if "volume" in item: 
            volume = item["volume"]
          else:
            volume = None

          if "published-print" in item: 
            year = item['published-print']['date-parts'][0][0] 
          else:
            year = None

          if "issue" in item: 
            issue = item["issue"]
          else:
            issue = None

          if "page" in item: 
            page = item["page"]
          else:
            page = None

          metadata_records.append({
            "doi": item["DOI"],
            "issn": item["ISSN"][0],
            "title": item["title"][0],
            "prefix": item["prefix"],
            "journal": item["container-title"][0],
            "publisher": item["publisher"],
            "volume": volume,
            "issue": issue,
            "page": page,
            "year": year,
            "num_references": item['references-count'],
            "times_cited": item['is-referenced-by-count']
          })
        except:
          pass
    else: #Need to split queries
      cursor = "*"
      keep_paging = True
      while (keep_paging):
        sleep(self.sleep_sec)
        r = requests.get(base_url + "&rows=" + str(max_rows) + "&cursor=" + cursor,
                         headers=headers, timeout=self.timeout_sec)
        cursor = quote(r.json()['message']['next-cursor'], safe='')
        if len(r.json()['message']['items']) == 0:
          keep_paging = False

        for item in r.json()['message']['items']:
          try:
            if "volume" in item: 
              volume = item["volume"]
            else:
              volume = None

            if "published-print" in item: 
              year = item['published-print']['date-parts'][0][0] 
            else:
              year = None

            if "issue" in item: 
              issue = item["issue"]
            else:
              issue = None

            if "page" in item: 
              page = item["page"]
            else:
              page = None

            metadata_records.append({
              "doi": item["DOI"],
              "issn": item["ISSN"][0],
              "title": item["title"][0],
              "prefix": item["prefix"],
              "journal": item["container-title"][0],
              "publisher": item["publisher"],
              "volume": volume,
              "issue": issue,
              "page": page,
              "year": year,
              "num_references": item['references-count'],
              "times_cited": item['is-referenced-by-count']
            })
          except:
            pass

    return metadata_records

  @traced
  def get_xml_from_doi(self, doi, writefile, mode):
    '''
    Downloads and writes an HTML article to a file, given a DOI and operating mode

    :param doi: DOI string for the article we want to download
    :type doi: str

    :param writefile: file object to write to
    :type writefile: file

    :param mode: choose from {'elsevier' | 'aps'}, depending on how we wish to access the file
    :type mode: str

    :returns: True on successful write, False otherwise
    :rtype: bool
    '''

    if mode == 'elsevier':
      try:
        xml_url='https://api.elsevier.com/content/article/doi/' + doi + '?view=FULL'
        headers = {
          'X-ELS-APIKEY': self.els_api_key,
          'Accept': 'text/xml'
        }

        r = requests.get(xml_url, stream=True, headers=headers, timeout=self.timeout_sec)
        if r.status_code == 200:
          for chunk in r.iter_content(2048):
            writefile.write(chunk)
          return True
      except:
        # API download limit exceeded
        return False
      return False

    if mode == 'aps':
      try:
        xml_url='http://harvest.aps.org/v2/journals/articles/' + doi
        headers = {
          'Accept': 'text/xml'
        }

        r = requests.get(xml_url, stream=True, headers=headers, timeout=self.timeout_sec)
        if r.status_code == 200:
          for chunk in r.iter_content(2048):
            writefile.write(chunk)
          return True
      except:
        # API download limit exceeded
        return False
      return False

    return False

  @traced
  def get_html_from_doi(self, doi, writefile, mode):
    '''
    Downloads and writes an HTML article to a file, given a DOI and operating mode

    :param doi: DOI string for the article we want to download
    :type doi: str

    :param writefile: file object to write to
    :type writefile: file

    :param mode: choose from {'elsevier' | 'springer' | 'acs' | 'ecs' | 'rsc' | 'nature' | 'wiley' | 'aaas' | 'emerald'}, depending on how we wish to access the file
    :type mode: str

    :returns: True on successful write, False otherwise
    :rtype: bool
    '''

    if mode == 'springer':
      base_url = 'http://link.springer.com/'
      api_url = base_url + doi + '.html'

      try:
        headers = {
          'Accept': 'text/html',
          'User-agent': 'Mozilla/5.0'
        }
        r = requests.get(api_url, stream=True, headers=headers, timeout=self.timeout_sec)
        if r.status_code == 200:
          for chunk in r.iter_content(2048):
            writefile.write(chunk)
          return True
      except:
        return False
      return False

    if mode == 'wiley':
      base_url = 'http://onlinelibrary.wiley.com/doi/'
      api_url = base_url + doi + '/full'

      try:
        headers = {
          'Accept': 'text/html',
          'User-agent': 'Mozilla/5.0'
        }
        r = requests.get(api_url, stream=True, headers=headers, timeout=self.timeout_sec)
        if r.status_code == 200:
          for chunk in r.iter_content(2048):
            writefile.write(chunk)
          return True
      except:
        return False
      return False

    if mode == 'acs':
      base_url = 'http://pubs.acs.org/doi/full/'
      api_url = base_url + doi

      try:
        headers = {
          'Accept': 'text/html',
          'User-agent': 'Mozilla/5.0'
        }
        r = requests.get(api_url, stream=True, headers=headers, timeout=self.timeout_sec)
        if r.status_code == 200:
          for chunk in r.iter_content(2048):
            writefile.write(chunk)
          return True
      except:
        return False
      return False

    if mode == 'emerald':
      base_url = 'http://www.emeraldinsight.com/doi/full/'
      api_url = base_url + doi

      try:
        headers = {
          'Accept': 'text/html',
          'User-agent': 'Mozilla/5.0'
        }
        r = requests.get(api_url, stream=True, headers=headers, timeout=self.timeout_sec)
        if r.status_code == 200:
          for chunk in r.iter_content(2048):
            writefile.write(chunk)
          return True
      except:
        return False
      return False

    if mode == 'rsc':
      html_string = 'articlehtml'
      download_url = 'https://doi.org/' + doi
      headers = {
      'Accept': 'text/html',
      'User-agent': 'Mozilla/5.0'
      }
      r = requests.get(download_url, headers=headers, timeout=self.timeout_sec)
      url = r.url
      url = url.encode('ascii')
      url = url.split('/')
      url = url[0] + '//' + url[2] + '/' + url[3] + '/' + url[4] + '/' + html_string + '/' + url[6] + '/' + url[7] + '/' + url[8]

      r = requests.get(url, stream=True, headers=headers, timeout=self.timeout_sec)

      if r.status_code == 200:
        try:
          for chunk in r.iter_content(2048):
            writefile.write(chunk)
          return True
        except:
          return False

      return False

    if mode == 'nature':
      download_url = 'https://doi.org/' + doi

      headers = {
        'Accept': 'text/html',
        'User-agent': 'Mozilla/5.0'
      }
      r = requests.get(download_url, stream=True, headers=headers, timeout=self.timeout_sec)
      if r.status_code == 200:
        try:
          for chunk in r.iter_content(2048):
            writefile.write(chunk)
          return True
        except:
          return False
      return False

    if mode == 'aaas':

      headers = {
        'Accept': 'text/html',
        'User-agent': 'Mozilla/5.0'
      }

      article_url = 'https://doi.org/' + doi
      resp = requests.get(article_url, headers=headers, timeout=self.timeout_sec)

      download_url = resp.url + '.full'  #Capture fulltext from redirect

      r = requests.get(download_url, stream=True, headers=headers, timeout=self.timeout_sec)
      if r.status_code == 200:
        try:
          for chunk in r.iter_content(2048):
            writefile.write(chunk)
          return True
        except:
          return False
      return False

    if mode == 'ecs':
      headers = {
        'Accept': 'text/html',
        'User-agent': 'Mozilla/5.0'
      }

      article_url = 'https://doi.org/' + doi
      resp = requests.get(article_url, headers=headers, timeout=self.timeout_sec)

      download_url = resp.url + '.full'  #Capture fulltext from redirect

      r = requests.get(download_url, stream=True, headers=headers, timeout=self.timeout_sec)
      if r.status_code == 200:
        try:
          for chunk in r.iter_content(2048):
            writefile.write(chunk)
          return True
        except:
          return False
      return False

    return False

  @traced
  def get_pdf_from_doi(self, doi, writefile, mode):
    '''
    Downloads and writes a PDF article to a file, given a DOI and operating mode

    :param doi: DOI string for the article we want to download
    :type doi: str

    :param writefile: file object to write to
    :type writefile: file

    :param mode: choose from {'crossref' | 'elsevier' | 'rsc' | 'springer' | 'ecs' | 'nature' | 'acs'}, depending on how we wish to access the file
    :type mode: str

    :returns: True on successful write, False otherwise
    :rtype: bool
    '''

    if mode == 'crossref':
      base_url = 'http://api.crossref.org/works/'
      api_url = base_url + doi

      headers = {
        'Accept': 'application/json'
      }

      try:
        response = json.loads(requests.get(api_url, headers=headers, timeout=self.timeout_sec).text)
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
      try:
        pdf_url='http://api.elsevier.com/content/article/doi:' + doi + '?view=FULL'
        headers = {
          'X-ELS-APIKEY': self.els_api_key,
          'Accept': 'application/pdf'
        }

        r = requests.get(pdf_url, stream=True, headers=headers, timeout=self.timeout_sec)
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
      scrape_url = 'https://doi.org/' + doi
      download_url = None

      r = requests.get(scrape_url, timeout=self.timeout_sec)
      if r.status_code == 200:
        scraper.feed(r.content)

        if scraper.download_link is not None:
          download_url = scraper.download_link

      if download_url is not None:
        headers = {
          'Accept': 'application/pdf'
        }
        r = requests.get(download_url, stream=True, headers=headers, timeout=self.timeout_sec)
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
      scrape_url = 'https://doi.org/' + doi
      download_url = None

      r = requests.get(scrape_url, timeout=self.timeout_sec)
      if r.status_code == 200:
        scraper.feed(r.content)

        if scraper.download_link is not None:
          download_url = scraper.download_link

      if download_url is not None:
        headers = {
          'Accept': 'application/pdf'
        }
        r = requests.get(download_url, stream=True, headers=headers, timeout=self.timeout_sec)
        if r.status_code == 200:
          try:
            for chunk in r.iter_content(2048):
              writefile.write(chunk)
            return True
          except:
            return False

      return False

    if mode == 'nature':
      scraper = scrapers.Nature()
      scrape_url = 'https://doi.org/' + doi
      download_url = None

      r = requests.get(scrape_url, timeout=self.timeout_sec)
      if r.status_code == 200:
        scraper.feed(r.content)

        if scraper.download_link is not None:
          download_url = scraper.download_link

      if download_url is not None:
        headers = {
          'Accept': 'application/pdf'
        }
        r = requests.get(download_url, stream=True, headers=headers, timeout=self.timeout_sec)
        if r.status_code == 200:
          try:
            for chunk in r.iter_content(2048):
              writefile.write(chunk)
            return True
          except:
            return False

      return False

    if mode == 'acs':
      base_url = 'http://pubs.acs.org/doi/pdf/'
      api_url = base_url + doi

      try:
        headers = {
          'Accept': 'application/pdf',
          'User-agent': 'Mozilla/5.0'
        }
        r = requests.get(api_url, stream=True, headers=headers, timeout=self.timeout_sec)
        if r.status_code == 200:
          for chunk in r.iter_content(2048):
            writefile.write(chunk)
          return True
      except:
        return False
      return False

    if mode == 'springer':
      base_url = 'http://link.springer.com/content/pdf/'
      api_url = base_url + doi

      try:
        headers = {
          'Accept': 'application/pdf',
          'User-agent': 'Mozilla/5.0'
        }
        r = requests.get(api_url, stream=True, headers=headers, timeout=self.timeout_sec)
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
      try:
        url='http://api.elsevier.com/content/article/doi/' + doi + '?view=FULL'

        headers = {
          'X-ELS-APIKEY': self.els_api_key,
          'Accept': 'application/json'
        }

        r = requests.get(url, headers=headers, timeout=self.timeout_sec)
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

    :returns: A title (or None on failure)
    :rtype: unicode
    '''

    if mode == 'crossref':
      try:
        url='http://api.crossref.org/works/' + doi
        headers = {
          'X-ELS-APIKEY': self.els_api_key,
          'Accept': 'application/json'
        }

        r = requests.get(url, headers=headers, timeout=self.timeout_sec)
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
      query = quote(line[0])
      query = query.split()
      query = '+'.join(query)

      final_query = query
      queries.append(final_query)
    return queries
