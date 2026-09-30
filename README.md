# Search Engine Website

A from-scratch search engine that indexes a local web corpus, ranks matching documents, and serves results through a Flask web interface.

The project was built as an information-retrieval exercise with a focus on **disk-backed indexing, duplicate detection, query ranking, and fast lookup over tens of thousands of pages**.

> **Portfolio note:** this is a historical academic project built against Python 3.6-era libraries. The architecture and algorithms are the focus; newer dependency versions may require small compatibility updates.

## Demo

![Search engine demo](web_ui.gif)

## What it demonstrates

- HTML parsing and text extraction with Beautiful Soup
- tokenization and Porter stemming
- exact-duplicate and near-duplicate filtering
- SimHash-style fingerprints with Hamming-distance checks
- partial indexes that are merged into a disk-backed inverted index
- term positions for phrase/proximity-aware scoring
- TF-IDF document weighting and cosine similarity
- Boolean AND/OR candidate selection
- boosts for strong terms such as titles/bold text
- anchor-text signals
- a Flask UI for searching, pagination, and rebuilding the index

## High-level flow

```text
HTML corpus (DEV/)
        |
        v
  Parse + normalize
        |
        v
Duplicate filtering
        |
        v
 Partial indexes
        |
        v
Merged inverted index
        |
        +-----------------------------+
        |                             |
        v                             v
 query parsing                 metadata / boosts
        |                             |
        +-------------> ranking <-----+
                        |
                        v
                  Flask results UI
```

## Ranking

The ranking pipeline combines several signals rather than relying on a single score:

1. keep the most useful query terms using document-frequency thresholds;
2. select candidate documents with Boolean-style term coverage;
3. calculate TF-IDF/cosine relevance;
4. add positional bonuses when query terms occur together;
5. apply strong-term and anchor-text boosts;
6. return the highest-scoring documents to the web UI.

The thresholds and weights are configurable in `config.ini`.

## Repository layout

| File / directory | Purpose |
| --- | --- |
| `indexer.py` | Parses documents, removes duplicates, and builds the inverted index |
| `search.py` | Query-time lookup and result retrieval |
| `ranking.py` | Ranking and scoring logic |
| `helper.py` | Shared parsing, serialization, and query helpers |
| `config.py` / `config.ini` | Runtime and ranking configuration |
| `web_launch.py` | Flask application and index-update entry point |
| `templates/` / `static/` | Web UI |
| `web_ui.gif` | Project demo |

## Running locally

### 1. Create an environment

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

On Windows, activate with:

```powershell
.venv\Scripts\activate
```

### 2. Install the project dependencies

The original project used Python 3.6-compatible releases of:

```bash
pip install flask flask-wtf flask-sqlalchemy nltk beautifulsoup4
```

If reproducing the original environment exactly, use package versions that still support Python 3.6.

### 3. Add a document corpus

Place the crawled HTML documents in:

```text
DEV/
```

A companion crawler is available in [Python_Crawler](https://github.com/vudh1/Python_Crawler).

### 4. Build or refresh the index

```bash
python3 web_launch.py
```

Answer `Y` when prompted to rebuild the inverted index.

### 5. Start the web app

```bash
make
```

or:

```bash
export FLASK_APP=web_launch.py
export FLASK_ENV=development
export FLASK_RUN_HOST=localhost
export FLASK_RUN_PORT=8000
python3 -m flask run
```

Then open `http://localhost:8000/`.

## Generated index data

The `output/` directory is generated at runtime and contains serialized lookup structures such as:

- document metadata;
- the merged inverted index;
- strong-term and anchor-term maps;
- term-to-file-offset mappings;
- temporary partial indexes during index construction.

These files are intentionally ignored by Git because they can be regenerated from the corpus.

## Why this project is useful

The project goes beyond a simple keyword filter: it implements the core pieces of a small search system—**index construction, duplicate suppression, persistent postings, relevance ranking, query execution, and a usable front end**—without relying on a hosted search product such as Elasticsearch.
