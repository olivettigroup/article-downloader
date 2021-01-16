article-downloader
==================
[![Circle CI](https://circleci.com/gh/olivettigroup/article-downloader.svg?style=svg&circle-token=c5aed981b2738abfba780c85e74c89a11c8debe6)](https://circleci.com/gh/olivettigroup/article-downloader) [![Documentation Status](https://readthedocs.org/projects/article-downloader/badge/?version=latest)](https://readthedocs.org/projects/article-downloader/?badge=latest) [![DOI](https://zenodo.org/badge/19479/eddotman/article-downloader.svg)](https://zenodo.org/badge/latestdoi/19479/eddotman/article-downloader)


Uses publisher-approved APIs to programmatically retrieve large amounts of scientific journal articles for text mining.
Exposes a top-level `ArticleDownloader` class which provides methods for retrieving lists of DOIs (== unique article IDs) from text search queries, downloading HTML and PDF articles given DOIs, and programmatically sweeping through search parameters for large scale downloading.

**Important Note**: This package is only intended to be used for publisher-approved text-mining activities! The code in this repository only provides an interface to existing publisher APIs and web routes; *you need your own set of API keys / permissions to download articles from any source that isn't open-access*.

## Full API Documentation
You can read the documentation for this repository [here](https://article-downloader.readthedocs.io/en/latest/articledownloader.articledownloader/).

## Installation
Use `pip install articledownloader`. If you don't have `pip` installed, you could also download the ZIP containing all the files in this repo and manually import the `ArticleDownloader` class into your own Python code.

## Usage
Use the `ArticleDownloader` class to download articles. You'll need an API key, and please respect each publisher's terms of use.

It's usually best to add your API key to your environment variables with something like `export API_KEY=xxxxx`.

You can find DOIs using a CSV where the first column corresponds to search queries, and these queries will be used to find articles and retrieve their DOIs.

## Examples

### Downloading a single PDF article

```python
from articledownloader.articledownloader import ArticleDownloader
downloader = ArticleDownloader(els_api_key='your_elsevier_API_key')
my_file = open('my_path/something.pdf', 'w')  # Need to use 'wb' on Windows

downloader.get_pdf_from_doi('my_doi', my_file, 'crossref')
```

### Downloading a single HTML article

```python
from articledownloader.articledownloader import ArticleDownloader
downloader = ArticleDownloader(els_api_key='your_elsevier_API_key')
my_file = open('my_path/something.html', 'w')

downloader.get_html_from_doi('my_doi', my_file, 'elsevier')
```

### Getting metadata

```python
from articledownloader.articledownloader import ArticleDownloader
downloader = ArticleDownloader(els_api_key='your_elsevier_API_key')

#Get 500 DOIs from articles published after the year 2000 from a single journal
downloader.get_dois_from_journal_issn('journal_issn', rows=500, pub_after=2000)

#Get the title for a single article (only works with CrossRef for now)
downloader.get_title_from_doi('my_doi', 'crossref')

#Get the abstract for a single article (only works with Elsevier for now)
downloader.get_abstract_from_doi('my_doi', 'elsevier')
```

### Using search queries to find DOIs
CSV file:

    search query 001,
    search query 002,
    search query 003,
    .
    .
    .

Python:
```python
from articledownloader.articledownloader import ArticleDownloader
downloader = ArticleDownloader('your_API_key')

#grab up to 5 articles per search
queries = downloader.load_queries_from_csv(open('path_to_csv_file', 'r'))

dois = []
for query in queries:
  dois.append(downloader.get_dois_from_search(query))

for i, doi in enumerate(dois):
    my_file = open(str(i) + '.pdf', 'w')
    downloader.get_pdf_from_doi(doi, my_file, 'crossref') #or 'elsevier'
    my_file.close()
```
