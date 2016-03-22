from HTMLParser import HTMLParser

class RSC(HTMLParser):
  '''
  Scraper for RSC publications
  '''

  download_link = None

  #RSC scraping implementation
  def handle_starttag(self, tag, attrs):
    '''
    PDF link handler; never gets explicity called by user
    '''
    if tag == 'a' and ('title', 'PDF') in attrs:
      for attr in attrs:
        if attr[0] == 'href':
          self.download_link = attr[1]

class ECS(HTMLParser):
  '''
  Scraper for ECS publications
  '''

  download_link = None

  #ECS scraping implementation
  def handle_starttag(self, tag, attrs):
    '''
    PDF link handler; never gets explicity called by user
    '''
    if tag == 'a' and ('rel', 'view-full-text.pdf') in attrs:
      for attr in attrs:
        if attr[0] == 'href':
          self.download_link = 'http://jes.ecsdl.org' + attr[1][:-5]
