article-downloader
==================
[![Build Status](https://travis-ci.org/eddotman/article-downloader.svg?branch=master)](https://travis-ci.org/eddotman/article-downloader)

Uses publisher APIs (and sometime direct download) to programmatically retrieve large amounts of scientific journal articles for text mining.
Primarily built for Elsevier's text mining API; support for other APIs is gradually being added.

##Installation
Use `pip install articledownloader`.

##Usage
Use the `ArticleDownloader` class to download articles en masse. Currently supported publishers are Elsevier and CrossRef. You'll need an API key, and please respect each publisher's terms of use.

It's usually best to add your API key to your environment variables with something like `export API_KEY=xxxxx`.

You can find articles in two ways: You can load in a text file with a list of DOIs. Or, you can have a CSV where the first column corresponds to search queries, and these queries will be used to find articles and retrieve their DOIs.

##Examples

###Downloading a single article
    from articledownloader.articledownloader import ArticleDownloader
    downloader = ArticleDownloader('your_API_key')
    my_file = open('my_path/something.pdf')

    downloader.get_pdf_from_doi('target_doi', my_file, 'crossref')
    downloader.get_pdf_from_doi('target_doi', my_file, 'elsevier')

###Using search queries to find DOIs
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
    queries = downloader.load_queries_from_csv('path_to_csv_file')

    piis = []
    for query in queries:
      piis.append(downloader.get_dois_from_search(query))

    dois = set(dois) #Get rid of duplicates

    for i, doi in enumerate(dois):
        file = open(str(i) + '.pdf')
        downloader.get_pdf_from_doi(doi, file, 'crossref') #or 'elsevier'
        file.close()
