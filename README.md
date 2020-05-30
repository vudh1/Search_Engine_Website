# About

This is a search engine created from the ground up that is capable of handling tens of thousands of documents or Web pages, under harsh operational constraints and having a query response time under 300 milliseconds.


# Install Dependencies

*Doing Install Dependencies step only if the virtual environment attached is not working. Skip this section if you want.*

### Install Python3

If you do not have Python 3.6+:

*The program should use Python 3.6+ since some functions are not in Python 2+ versions*

Windows: https://www.python.org/downloads/windows/

Linux: https://docs.python-guide.org/starting/install3/linux/

MAC: https://docs.python-guide.org/starting/install3/osx/

Check if pip is installed by opening up a terminal/command prompt and typing
the commands `python3 -m pip`. This should show the help menu for all the
commands possible with pip. If it does not, then get pip by following the
instructions at https://pip.pypa.io/en/stable/installing/

To install the dependencies for this project run the following two commands
after ensuring pip is installed for the version of python you are using.
Admin privileges might be required to execute the commands. Also make sure
that the terminal is at the root folder of this project.


### Virtual Environment Tutorial

```python
(venv) $ mkdir my_virtual_environment
(venv) $ cd my_virtual_environment
(venv) $ python3 -m venv venv
(venv) $ cd ..
(venv) $ source my_virtual_environment/venv/bin/activate
(venv) $ pip install --upgrade pip
(venv) $ pip install flask
(venv) $ pip install flask-wtf
(venv) $ pip install flask-sqlalchemy
(venv) $ pip install nltk
(venv) $ pip install BeautifulSoup4
```

- Type this line in terminal for running in virtual environment from venv folder.

```python
$ source my_virtual_environment/venv/bin/activate
```

# Resource Requirements

- Option 1: Using crawler program at https://github.com/danielvu2810/Python_Crawler to crawler the pages. Store the page results in **DEV** folder inside the folder containing all files.

- Option 2: Download and decompress the zip folder at https://drive.google.com/file/d/1vBJof00Hl4F8bi7Nu236BLBuZE7T0zD7/view?usp=sharing. Add **DEV** folder inside the folder containing all files.


# Web Browser Launch

- If the output folder with inverted index already exists, you can skip this and update directly on the web UI. Otherwise, if you want to create output folder with the inverted index list:

```python
(venv) $ python3 web_launch.py
```

- Use Makefile to running WebUI (it will automatically run all 5 lines below):

```python
(venv) $ make
```

- Instead of **make** command line, you can set Flask environment variables and running the WebUI:.

```python
(venv) $ export FLASK_APP=web_launch.py
(venv) $ export FLASK_ENV=development
(venv) $ export FLASK_RUN_HOST=localhost
(venv) $ export FLASK_RUN_PORT=8000
(venv) $ python3 -m flask run
```
- Using web browser to access http://localhost:8000/  (if you set different host name, port number, use the link shown on console output)

- To exit the virtual environment:

```python
(venv) $ deactivate
```

# Program File Descriptions

### config.ini

- configurations for file names, variables, etc.

### config.py
- read config.ini for the program

### indexer.py
- M1 part for creating inverted index

### search.py
- M2 part for search query

### ranking.py
- M3 part for ranking

### posting.py
- class Entry_Posting
```python
Entry_Posting(doc_id,freq,tf_idf, positions)
```

### helper.py
- some helpers functions for web_launch.py, indexer.py, search.py and ranking.py
- some functions are useful to read the inverted index file (at specific line), doc_ids file, term_line_relation file

### forms.py
- query search form in WebUI

### web_launch.py
- main program for web launch using Flask
- using HTML and CSS files in static & templates folders to build a webUI

*You can find more specific function descriptions in each file. Check the output files after running to confirm the format if you need to read again or use some functions in helper.py file*

# Output File Descriptions

*Since the output files are binary files, this gives you a look at the data structures of each files*

- output/doc_ids.bin
```python
# dictionary with key is doc_id, value is doc_name
{ doc_id : doc_name }
```

- output/index.bin
```python
# Each line is a dictionary with the key is the term, and the posting is a dictionary of doc_id and its entry.
# Use line offset to read the posting of each term
# posting = { doc_id : entry }
{ term1 : posting1 }
{ term2 : posting2 }
{ term3 : posting3 }

```

- output/strong_terms.bin
```python
# a dictionary with key as strong terms (title, bold) and value is a list of doc_ids
{term : [doc_id]}
```

- output/anchor_terms.bin
```python
# a dictionary with key as anchor terms and value is a list of doc_ids
{term : [doc_id]}
```

- output/term_line_relationships.bin
```python
# a dictionary with key is term, value is the line_offset of that term and its posting in index.bin
{ term : line_offset}
```

- output/query_cache.bin
```python
# a dictionary with maximum MAX_QUERY_CACHE_ENTRIES elements;
# key is term, value is the list/pair of 2 elements, posting and the count as the times that term is queried
{ term : [posting, count]}
```

- output/partial_index/[0-N]

*All the partial index files and folder will be auto deleted after merging*
```python
# Each line is a partial_posting which is dictionary
# key is the doc_id, and the value is entry of that doc_id of a term
# partial_posting = { doc_id : entry }
{ partial_posting1 }
{ partial_posting2 }
{ partial_posting3 }

```

# Demo

![](web_ui.gif)
