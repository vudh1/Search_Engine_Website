import os
import sys
import re
import warnings
import math
import json
import bs4

from posting import Entry_Posting

from helper import analyze_text
from helper import write_postings_file
from helper import write_term_line_relationship


html_elements = ['head', 'title', 'meta', 'style', 'script', '[document]']

doc_ids = dict() # id - name lists of documents

total_tokens = dict() # inverted_index list

warnings.filterwarnings("ignore", category=UserWarning, module='bs4') # unable printing warning when reading using bs4

# compute positions, frequencies, tf_scores of the terms

def compute_posting_value(terms):
	positions = {i: [] for i in terms}
	frequencies = {i: 0 for i in terms}

	for i in range(len(terms)):
		positions[terms[i]].append(i)
		frequencies[terms[i]] += 1

	tf_scores = {i: 0.0 for i in frequencies.keys()}

	for token, freq in frequencies.items():
		if freq > 0:
			tf_scores[token] = 1 + math.log10(frequencies[token])

	return positions, frequencies, tf_scores


# compute entry posting from the text and add to new list

def add_to_list(text,doc_id):
	terms = analyze_text(text)

	positions, frequencies, tf_scores = compute_posting_value(terms)

	for token in positions:
		if token not in total_tokens:
			total_tokens[token] = []

		entry = Entry_Posting(doc_id, frequencies[token], tf_scores[token],positions[token])
		total_tokens[token].append(entry)


# compute tf_idf_scores of all terms after reading all documents

def compute_tf_idf_scores(num_documents):
	for token, posting in total_tokens.items():
		df = len(posting)
		if df > 0:
			for entry in posting:
				tf = entry.get_tf_idf()
				if tf != 0 and num_documents != 0:
					tf_idf = tf * math.log10(num_documents / df)
				else:
					tf_idf = 0
				entry.set_tf_idf(tf_idf)


# reading text from html with tag filter

def tag(element):
	if element.parent.name in html_elements:
		return False
	if isinstance(element, bs4.element.Comment):
		return False
	return True


# read all documents and create the inverted index list
# for now: all documents are reading into memory first before write to disk
# need to read a batch of documents at a time, write partial index to disk, and after reading all documents, merging all partial index files into one

def indexer_input(config):
	num_documents = 0

	for root, directories, files in os.walk(config.input_folder_name):
		for dir in directories:
			files = os.listdir(root + '/' + dir)
			for f in files:
				data = dict()
				with open(root + '/' + dir + '/' + f) as jf:

					try:
						data = json.load(jf)
						html = bs4.BeautifulSoup(data["content"], 'html.parser')
						doc_name = str(data["url"]).split("#",1)[0]
						if doc_name not in doc_ids.values(): # avoid duplicate file names
							doc_ids[num_documents] = doc_name
							text = ' '.join(filter(tag, html.find_all(text=True)))
							add_to_list(text,num_documents)
							num_documents += 1

							if num_documents % 1000 == 0:
								print("----> Complete Reading " + str(num_documents)+" files...")
					except Exception:
						continue
	return num_documents

# write all inverted index file to disk

def write_indexer_output(config):
	if(os.path.exists(config.output_folder_name) is False):
		os.mkdir(config.output_folder_name)

	with open(config.doc_id_file_name, 'w') as outfile:
		json.dump(doc_ids, outfile)

	write_postings_file(config,total_tokens)


# main indexer function

def indexer(config):

	print("----> Running indexer_input()....")
	num_documents = indexer_input(config)

	print("----> Running compute_tf_idf_scores()....")
	compute_tf_idf_scores(num_documents)

	print("----> Running write_indexer_output()....")
	write_indexer_output(config)

	print("----> Running write_term_line_relationship()....")
	write_term_line_relationship(config)

	return num_documents


