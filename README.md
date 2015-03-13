article-downloader
==================
[![Build Status](https://travis-ci.org/eddotman/article-downloader.svg?branch=master)](https://travis-ci.org/eddotman/article-downloader)

Uses publisher APIs (and sometime direct download) to programmatically retrieve large amounts of scientific journal articles for text mining.
Primarily built for Elsevier's text mining API; support for other APIs is gradually being added.

##Installation
Use `pip install articledownloader`.

##Usage
Use the `ArticleDownloader` class to download articles en masse. Currently supported publishers are Elsevier, CrossRef and RSC. You'll need an API key, and please respect each publisher's terms of use.

It's usually best to add your API key to your environment variables with something like `export API_KEY=xxxxx`.

You can find articles in two ways: You can load in a text file with a list of DOIs (or PIIs, which are Elsevier's proprietary equivalent). Or, you can have a CSV where the first column corresponds to search queries, and these queries will be used to find articles and retrieve their DOIs/PIIs.

##Examples

###Downloading a single article
    from articledownloader.articledownloader import ArticleDownloader
    downloader = ArticleDownloader('your_API_key')
    my_file = open('my_path/something.pdf')

    downloader.get_pdf_from_pii('target_pii', my_file)

###Using search queries to find DOIs/PIIs
CSV file:

    search query 001,
    search query 002,
    search query 003,
    .
    .
    .

Python:

    from articledownloader.articledownloader import ArticleDownloader
    downloader = ArticleDownloader('your_API_key')

    #grab up to 5 articles per search
    queries = downloader.load_queries_from_csv('path_to_csv_file', count=5)

    piis = []
    for query in queries:
      piis.append(downloader.get_piis_from_search(query, mode='elsevier'))

    piis = set(piis) #Get rid of duplicates

    for pii in piis:
        file = open(str(pii) + '.pdf')
        downloader.get_pdf_from_pii(pii, file)
        file.close()
