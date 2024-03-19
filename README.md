<div align="center">

# [winzig](https://pypi.org/project/winzig/)

winzig is a tiny search engine designed for personal use that enables users to download and search for posts from their favourite feeds.

This project was heavily inspired by the [microsearch](https://github.com/alexmolas/microsearch) project and this [article](https://www.alexmolas.com/2024/02/05/a-search-engine-in-80-lines.html) about it.

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![SQLite](https://img.shields.io/badge/sqlite-%2307405e.svg?style=for-the-badge&logo=sqlite&logoColor=white)
![Poetry](https://img.shields.io/badge/Poetry-%233B82F6.svg?style=for-the-badge&logo=poetry&logoColor=0B3D8D)
</div>


## Motivation

For quite some time, I've been contemplating the idea of creating my own personal search engine. I wanted a tool that could facilitate searching through my personal notes, books, articles, podcast transcripts, and anything else I wished to include. However, I was unsure of how or where to begin until I discovered the microsearch project, which reignited the momentum for the idea in my mind.  

This project started as a clone of the `microsearch` project to be able to better understand how some things worked. Later, I decided to start implementing some changes like keeping all the data in a SQLite database or building a sort-of inverted index after crawling.  

## Features

- **Fetch only what you need**: winzig optimizes data retrieval by excluding content that has been already fetched, making sure that only new content is downloaded each time.  
- **Async, Async, Async**: Crawling as well as the posterior data processing operates asynchronously, resulting in lightning-fast performance.  
- **Efficient data management with SQLite**: Everything is kept in a SQLite database in your home directory.  
- **Easy to use**: The CLI provides simple commands for crawling and searching effortlessly.  
- **Enhanced search speed**: The post-crawling processing ensures near-instantaneous search results.  

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

Then, create a `virtualvenv` inside the winzig directory:

```bash
python -m venv venv
```

Activate the `virtualvenv`:

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

The first time you initiate a crawl, you'll need a file containing a list of feeds to fetch. These feeds will be stored in the SQLite database. Therefore, there is no need to provide this file again unless you're adding new feeds. This repository contains a `urls` file that you can use.  

> Currently, there is no way to manage the feeds or posts added to the database. So if you want to remove some of them you will need to do it manually. However, it may be more efficient to delete the database and crawl again.  
### Crawling

The following command starts the crawler. Initially, it extracts the URLs from the specified file and saves them to the database. Then, it proceeds to fetch all the posts listed on each of these feeds. The `--verbose` flag signals that the command will provide detailed output, including HTTP errors.  
After finishing the crawling process, the frequencies of all terms within the saved posts will be calculated. Additionally, the inverted index will also be built at this stage.

```bash
winzig crawl --file="./urls" --verbose
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

### TUI

If you prefer you can use the TUI to interact with the search engine. The TUI is its early stage but it offers basic functionality and faster search experiences compared to the `search` command since the content is indexed once and not each time you want to search something.

```bash
winzig tui
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

## Roadmap

- [x] Add a TUI using [`textual`](https://textual.textualize.io/).  
- [x] Build inverted index after crawling.  
- [ ] Improve TUI.
- [ ] Add tests.  
- [ ] Add support for documents like markdown or plain text files.  
- [ ] Add support for PDFs and other formats.  
- [ ] Add support for crawling individual posts.
- [ ] Make the CLI nicer.  
- [ ] Improve logging.
- [ ] Improve error handling.
- [ ] Add commands to manage the SQLite database.  
- [ ] Add support for advanced queries.  

## Contributing

If you are interested in contributing, please open an issue first. I will try to answer as soon as possible.  

