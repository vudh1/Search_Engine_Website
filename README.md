# Asssignment 3

## Run Program

- Add DEV folder in the folder containing all files

- Using terminal, run this line:

```python
$ python3 launch.py
```

- You can have option to update inverted_index.

- If yes, you have to wait for inverted_index file is created under **output** folder. It should take a while (20-30mins) to read all documents

- After output folder is created, there will be a input prompt request on terminal console. Enter query term for searching

- Enter **'quit'** for terminate the program.



## File Descriptions

### config.ini

- configurations for file names, variables, etc.

### config.py
- read config.ini for the program

### launch.py
- main function to create inverted index
- read doc_ids and term_line_relationship files
- search query

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

*You can find more specific function descriptions in each file. Check the output files after running to confirm the format if you need to read again or use some functions in helper.py file*

## To Do List

*https://docs.google.com/spreadsheets/d/1gk-oogamFdAdLNH0Lg587O3Gf3ghufvjnjptBBcBZtA/edit#gid=0*
