article-downloader
==================
[![Circle CI](https://circleci.com/gh/olivettigroup/article-downloader.svg?style=svg&circle-token=c5aed981b2738abfba780c85e74c89a11c8debe6)](https://circleci.com/gh/olivettigroup/article-downloader) [![Documentation Status](https://readthedocs.org/projects/article-downloader/badge/?version=latest)](https://readthedocs.org/projects/article-downloader/?badge=latest) [![DOI](https://zenodo.org/badge/19479/eddotman/article-downloader.svg)](https://zenodo.org/badge/latestdoi/19479/eddotman/article-downloader)


Uses publisher APIs to programmatically retrieve large amounts of scientific journal articles for text mining.
Primarily built for Elsevier's text mining API; support for other APIs is gradually being added.

## Installation
Use `pip install articledownloader`.

## Usage
Use the `ArticleDownloader` class to download articles. You'll need an API key, and please respect each publisher's terms of use.

It's usually best to add your API key to your environment variables with something like `export API_KEY=xxxxx`.

You can find DOIs using a CSV where the first column corresponds to search queries, and these queries will be used to find articles and retrieve their DOIs.

## Documentation
You can read the documentation for this repository [here](http://article-downloader.readthedocs.org/en/latest/).

## Examples

### Downloading a single article
    from articledownloader.articledownloader import ArticleDownloader
    downloader = ArticleDownloader('your_API_key', 'your_other_API_key')
    my_file = open('my_path/something.pdf', 'r')

    downloader.get_pdf_from_doi('target_doi', my_file, 'crossref')
    downloader.get_pdf_from_doi('target_doi', my_file, 'elsevier')

### Using search queries to find DOIs
CSV file:

    search query 001,
    search query 002,
    search query 003,
    .
    .
    .

Python:

    from articledownloader.articledownloader import ArticleDownloader
    downloader = ArticleDownloader('your_API_key', 'your_other_API_key')

    #grab up to 5 articles per search
    queries = downloader.load_queries_from_csv(open('path_to_csv_file', 'r'))

    dois = []
    for query in queries:
      dois.append(downloader.get_dois_from_search(query))

    for i, doi in enumerate(dois):
        file = open(str(i) + '.pdf', 'w')
        downloader.get_pdf_from_doi(doi, file, 'crossref') #or 'elsevier'
        file.close()
