# Search Engine Website

## Run Program

- Add DEV folder in the folder containing all files


- Type this line in terminal for running in virtual environment from venv folder.

```python
$ source my_virtual_environment/venv/bin/activate
```

*The program should use Python3 since some functions are not in Python 2 versions*


### Option 1: Console Launch
```python
(venv) $ python3 console_launch.py
```

- You can have option to update inverted_index.

- If yes, you have to wait for inverted_index file is created under **output** folder. It should take a while (20-30mins) to read all documents

- After output folder is created, there will be a input prompt request on terminal console. Enter query term for searching

- Enter **'quit'** for terminate the program.


### Option 2: Web UI Launch

- If you want to create output folder with the inverted index list, use this line or you can skip this and update directly on the web UI

```python
(venv) $ python3 web_launch.py
```

- Set Flask environment variables and running the WebUI by running these lines.

```python
(venv) $ export FLASK_APP=web_launch.py
(venv) $ export FLASK_ENV=development
(venv) $ export FLASK_RUN_HOST=localhost
(venv) $ export FLASK_RUN_PORT=8000
(venv) $ python3 -m flask run
```

- Or you can use Makefile instead (it will automatically run all 5 lines above)

```python
(venv) $ make
```
- Using  web browser to access *http://localhost:8000/*  (if you set different host name, port number, use the link shown on console output)


- To exit the virtual environment, use this line:

```python
(venv) $ deactivate
```

## File Descriptions

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
- some helpers functions for launch.py, indexer.py, search.py and ranking.py
- some functions are useful to read the inverted index file (at specific line), doc_ids file, term_line_relation file

### console_launch.py
- main program for console launch
- create inverted index
- read doc_ids and term_line_relationship files
- search query

### forms.py
- query search form in WebUI

### web_launch.py
- main program for web launch using Flask
- using HTML and CSS files in static & templates folders to build a webUI

*You can find more specific function descriptions in each file. Check the output files after running to confirm the format if you need to read again or use some functions in helper.py file*

## Virtual Environment Tutorial

*If the virtual environment attached is not working, you can create your own*

```python
(venv) $ mkdir my_virtual_environment
(venv) $ cd my_virtual_environment
(venv) $ python3 -m venv venv
(venv) $ cd ..
(venv) $ source my_virtual_environment/venv/bin/activate
(venv) $ pip install --upgrade pip
(venv) $ pip install flask
(venv) $ pip install flask-wtf
(venv) $ pip install nltk
(venv) $ pip install BeautifulSoup4
```

## Demo

![](web_ui.gif)
