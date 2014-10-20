article-downloader
==================

Uses publisher APIs (and sometime direct download) to programmatically retrieve large amounts of scientific journal articles for text mining.

##Installation
Use `pip install article-downloader` in bash.

##Usage
Use the `ArticleDownloader` class to download articles en masse. Currently supported publishers are Elsevier and RSC. You'll need an API key, and please respect each publisher's terms of use.

Add your API key to your environment variables with `export API_KEY=xxxxx`.

You can find articles in two ways: You can load in a text file with a list of DOIs (or PIIs, which are Elsevier's proprietary equivalent). Or, you can have a CSV where the first column correspond to search queries, and these queries will be used to find articles and retrieve their DOIs/PIIs.

##Examples

###Downloading a single article
    from article_downloader import ArticleDownloader
    downloader = ArticleDownloader()

    downloader.get_pdf_from_pii('xxxxxxx')

###Downloading many articles from a list of DOIs/PIIs
    from article_downloader import ArticleDownloader
    downloader = ArticleDownloader()

    downloader.get_piis_from_file('path_to_file')
    for pii in downloader.piis:
      downloader.get_pdf_from_pii(pii)

###Using search queries to find DOIs/PIIs
    from article_downloader import ArticleDownloader
    downloader = ArticleDownloader()

    #grab up to 5 articles per search
    downloader.downloader.load_queries_from_csv('path_to_csv_file', count=5)

    for query in downloader.queries:
      if downloader.get_piis_dois_from_search(query, mode='elsevier') > 0:
        for pii in downloader.piis: #DOIs and PIIs cleared before every search
          downloader.get_pdf_from_pii(pii)
