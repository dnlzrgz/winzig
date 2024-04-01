<div align="center">

# [winzig](https://pypi.org/project/winzig/)

winzig is a tiny search engine designed for personal use that enables users to download and search for posts from their favourite feeds.  

This project was heavily inspired by the [microsearch](https://github.com/alexmolas/microsearch) project and this [article](https://www.alexmolas.com/2024/02/05/a-search-engine-in-80-lines.html) about it.  

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![SQLite](https://img.shields.io/badge/sqlite-%2307405e.svg?style=for-the-badge&logo=sqlite&logoColor=white)
![Poetry](https://img.shields.io/badge/Poetry-%233B82F6.svg?style=for-the-badge&logo=poetry&logoColor=0B3D8D)
</div>


## Motivation

For quite some time, I've been contemplating the idea of creating my own personal search engine. I wanted a tool that could facilitate searching through my personal notes, books, articles, podcast transcripts, and anything else I wished to include. However, I was unsure of how or where to begin until I discovered the microsearch project, which reignited the momentum for the idea in my mind. I also though about it as an opportunity to delve deeper into asynchronous Python.  

This project started as a clone of the `microsearch` project to be able to better understand how some things worked. Later, I decided to start implementing some changes like keeping all the data in a SQLite database or building a sort-of inverted index after crawling.  

## Features

- **Fetch only what you need**: winzig optimizes data retrieval by excluding previously fetched content, making sure that only new content is downloaded each time.  
- **Async, Async, Async**: Both crawling and the subsequent data processing operate asynchronously, resulting in lightning-fast performance.  
- **Efficient data management**: All the data is stored in a SQLite database in your home directory making it easy to retrieve and update.  
- **Easy to use CLI**: The CLI provides simple commands for crawling and searching effortlessly, as well as clear feedback.  
- **Enhanced search speed**: With the heavy lifting part done after fetching the content, search yields near-instant results.  
- **TUI**: winzig also provides a basic TUI that facilitates an interactive search experience.  

## Installation

> You'll need Python >= 3.12 to be able to run winzig.

### pip

```bash
pip install winzig
```

### pipx

```bash
pipx install winzig
```

### Cloning this repository

Clone this repo with `git clone`:

```bash
git clone https://github.com/dnlzrgz/winzig winzig
```

Or use `gh` if you prefer it instead:

```bash
gh repo clone dnlzrgz/winzig
```

Then, create a `virtualenv` inside the winzig directory:

```bash
python -m venv venv
```

Activate the `virtualenv`:

```bash
source venv/bin/activate
```

And run:

```bash
pip install .
```

Instead of using `pip` you can also use `poetry`:

```bash
poetry install
```

And now you should be able to run:

```bash
winzig --help
```

## Usage

To begin using Winzig, the first step is to crawl some content. The easiest method for this is to utilize the feeds file located in this repository along with the `winzig crawl feeds` command. These feeds will be stored in a SQLite database in your home directory, eliminating the need to provide this file again unless you're adding new feeds. If instead what you want is to crawl specific posts directly, you can use `winzig crawl posts` and specify a file containing the URLs you want to fetch.  

> Currently, there is no way to manage the feeds or posts added to the database. So if you want to remove some of them you will need to do it manually. However, it may be more efficient to delete the database and crawl again.  

### Crawl

The `crawl` command serves as a convenient and efficient method to update your database with new content. When used without any subcommands, it automatically checks for new content using the feeds stored in the database and tries to retrieves it. Basically, running:  

```bash
winzig crawl
```

Is equivalent to:

```bash
winzig crawl feeds
```

#### Feeds

The `feeds` subcommand allows you to fetch and extract content from the posts of the specified feeds provided. The feeds are stored in the database so there is no need to provide a file every time.

```bash
winzig crawl feeds --file feeds.txt
```

```bash
winzig crawl feeds
```

You can also provide feed URLs directly as arguments. This feeds, if valid, will also be saved to the database.  

```bash
winzig crawl feeds https://chriscoyier.net/feed/
```

#### Posts

By using the `posts` subcommand, you can extract content directly from the posts listed in the provided file.  

```bash
winzig crawl posts --file="posts"
```

Or, if you prefer it, you can pass the URLs as arguments:  

```bash
winzig crawl posts https://textual.textualize.io/blog/2024/02/11/file-magic-with-the-python-standard-library/
```

### Searching

The following command starts a search for content matching the provided query and after a few seconds will return a list of relevant links.  

```bash
winzig search --query="async databases with sqlalchemy"
```

By default the number of results is `5` but you can change this by using the `-n` flag.  

```bash
winzig search --query="async databases with sqlalchemy" -n 10
```

You can add filters to your search results by using the `--filter` flag. Currently, the only filter supported is `domain`, which allows you to specify one or more domains to filter the search results.

```bash
winzig search --query "read large files" --filter domain='motherduck, textualize'
```

### TUI

If you prefer you can use the TUI to interact with the search engine. The TUI is its early stage but it offers basic functionality and faster search experiences compared to the `search` command since the content is indexed once and not each time you want to search something.  

```bash
winzig tui
```

### Export

You can export your feeds and your posts to plain text or CSV format using the `export` command and the `feeds` and `posts` subcommands.  

```bash
winzig export feeds --format csv --output feeds.csv
```

```bash
winzig export posts
```

## More feeds, please

If you're looking to expand your feed collection significantly, you can get a curated list of feeds from the [blogs.hn](https://github.com/surprisetalk/blogs.hn) repository with just a couple of commands.  

1. Download the JSON file containing the relevant information from the `blogs.hn` repository.

```bash
curl -sL https://raw.githubusercontent.com/surprisetalk/blogs.hn/main/blogs.json -o hn.json
```

2. Extract the feeds using `jq`. Make sure you have it installed in your system.

```bash
jq -r '.[] | select(.feed != null) | .feed' hn.json >> urls
```

> Incorporating feeds from the resultant file will significantly increase the number of requests made. Based on my experience, fetching posts from each feed, extracting content, and performing other operations may take approximately 20 to 30 minutes, depending on your Internet connection speed. The search speed will still be pretty fast.

## About the ranking function

Like the `microsearch` project, the ranking function used in winzig is the [Okapi BM25](https://en.wikipedia.org/wiki/Okapi_BM25). However, I am planning to add support for other variants of BM25, such as BM25+.

### BM11 and BM15 variants

If you're using the CLI for search, you have the flexibility to adjust the `k1` and `b` parameters. By manipulating the later to `0` or `1`, you can transform the BM25 ranking function into BM15 and BM11 variants, respectively:  

```bash
winzig search --query="build search engine" --b 0 # BM15
winzig search --query="build search engine" --b 1 # BM11
```

## Roadmap

- [ ] Improve TUI.
- [ ] Add tests.  
- [ ] Add multiple ranking functions.
- [ ] Add support for documents like markdown or plain text files.  
- [ ] Add support for PDFs and other formats.  
- [ ] Add commands to manage the SQLite database.  
- [ ] Add support for advanced queries.  

## Contributing

If you are interested in contributing, please open an issue first. I will try to answer as soon as possible.  

