import os
import sys
import re
import math
import json
import pickle
import bs4
import shutil
import warnings

from pickle import UnpicklingError
from collections import OrderedDict
from collections import defaultdict

from helper import analyze_text
from helper import read_existing_files

from entry import Entry
# disable showing warning when reading using bs4
warnings.filterwarnings("ignore", category=UserWarning, module='bs4')

html_elements = ['head', 'title', 'meta', 'style', 'script', '[document]']

num_documents = 0
num_terms = 0

doc_ids = dict()
doc_names = defaultdict(lambda : False)

total_tokens = OrderedDict()

term_ids = defaultdict(lambda : False)

term_line_relationship = OrderedDict()

# reading text from html with tag filter

def tag(element):
	if element.parent.name in html_elements:
		return False
	if isinstance(element, bs4.element.Comment):
		return False
	return True


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


# compute tf_idf_scores of each term after reading all documents

def compute_tf_idf_scores_for_a_posting(posting):
	global num_documents

	df = len(posting)

	if df > 0:
		for doc_id,entry in posting.items():
			tf = entry.get_tf()

			if tf != 0 and num_documents != 0:
				tf_idf = tf * math.log10(num_documents / df)
			else:
				tf_idf = 0

			entry.set_tf_idf(tf_idf)
	return posting


# compute entry posting from the text and add to new list

def add_to_list(text,doc_id):
	global num_documents
	global total_tokens

	terms = analyze_text(text)

	positions, frequencies, tf_scores = compute_posting_value(terms)

	for token in positions:
		token_in_total_tokens = total_tokens.get(token,False)

		if token_in_total_tokens == False:
			total_tokens[token] = dict()

		entry = Entry(frequencies[token], tf_scores[token], 0, positions[token])
		total_tokens[token][doc_id] = entry

	num_documents += 1


# update doc_names by doc_ids

def update_doc_names():
	global doc_ids
	global doc_names

	if doc_ids is None:
		return

	for index,name in doc_ids.items():
		doc_names[name] = index

def update_term_line_relationship():
	global term_ids
	global term_line_relationship

	for term, partial_index_id in term_ids.items():
		term_line_relationship[term] = -1

# merge all entries in a term file
# sort entries in posting by frequency

def get_merge_entries_of_a_term(config,term):
	global term_ids

	term_file_name = config.output_folder_name + config.partial_index_folder_name + str(term_ids[term])

	posting = dict()

	with open(term_file_name,'rb') as f:
		while True:
			try:
				sub_posting = pickle.load(f)
				posting.update(sub_posting)
			except (EOFError, UnpicklingError):
				break

	posting = compute_tf_idf_scores_for_a_posting(posting)

	#sort entries in posting by frequency
	# posting = dict(sorted(posting.items(), key=lambda x: x[1].get_freq(), reverse=True))

	os.remove(term_file_name)

	return posting


# merge all files in alphabetic order

def merge_partial_index(config):
	global term_line_relationship

	term_line_relationship = OrderedDict(sorted(term_line_relationship.items()))

	f = open(config.index_file_name,'wb+')

	for term in term_line_relationship:
		posting = get_merge_entries_of_a_term(config,term)

		data = { term : posting}

		line_offset = f.tell()

		pickle.dump(data,f)

		term_line_relationship[term] = line_offset

	f.close()

	try:
		shutil.rmtree(config.output_folder_name + config.partial_index_folder_name)
	except OSError as e:
		print("Error Delete: %s : %s" % (dir_path, e.strerror))

# write doc ids file

def write_doc_ids_file(config):
	with open(config.doc_id_file_name, 'wb') as f:
		pickle.dump(doc_ids, f)


# write term line relationship file

def write_term_line_relationship_file(config):
	global term_line_relationship

	if(os.path.exists(config.index_file_name) is True):
		with open(config.term_line_relationship_file_name, 'wb') as f:
			pickle.dump(term_line_relationship, f)


# write to partial index

def partial_indexer(config):
	global total_tokens
	global term_line_relationship
	global term_ids
	global num_terms

	for token,posting in total_tokens.items():
		if term_ids[token] == False:
			term_ids[token] = num_terms
			term_line_relationship[token] = -1
			num_terms +=1

		with open(config.output_folder_name + config.partial_index_folder_name+str(term_ids[token]),'ab') as f:
			pickle.dump(posting,f)

	total_tokens.clear()


# print total_tokens

def print_total_tokens():
	global total_tokens
	print("\n\n\n")
	num = 0
	for term,posting in total_tokens.items():
		print(num,".",term,end = ": ")
		for doc_id,entry in posting.items():
			# print("   ",doc_id,entry.get_freq(),entry.get_tf(),entry.get_tf_idf(),entry.get_positions())
			print(doc_id, end = ", ")
		print("")
		num += 1

	print("Num_total_tokens: ",len(total_tokens))


# create index in partial files

def indexer(config):
	global num_documents
	global total_tokens
	global doc_ids
	global doc_names

	doc_id = num_documents

	for root, directories, files in os.walk(config.input_folder_name):
		for dir in directories:
			files = os.listdir(root + '/' + dir)
			for f in files:
				data = dict()
				with open(root + '/' + dir + '/' + f) as jf:
					try:
						data = json.load(jf)
						soup = bs4.BeautifulSoup(data["content"], 'html.parser')
						doc_name = str(data["url"]).split("#",1)[0]

						# avoid duplicate file names
						if doc_names[doc_name] == False:
							doc_ids[doc_id] = doc_name
							doc_names[doc_name] = doc_id

							text = ' '.join(filter(tag, soup.find_all(text=True)))

							add_to_list(text,doc_id)

							doc_id += 1

							# print(num_documents)

							# offload to partial index per batch
							if num_documents % config.max_documents_per_batch == 0:
								print("----> Complete Reading " + str(num_documents)+" files...")
								# write to disk partial indexes
								partial_indexer(config)

					except Exception:
						continue
				# break

	# write to disk the last time
	if len(total_tokens) > 0:
		partial_indexer(config)
		print("----> Complete Reading Last " + str(num_documents % config.max_documents_per_batch)+" files...")


# main inverted index function

def inverted_index(config):
	global num_documents
	global num_terms
	global doc_ids
	global term_ids

	print("----> Running read_existing_files()....")

	# read previous file
	doc_ids,num_documents, term_ids, num_terms = read_existing_files(config)

	# update doc_names
	update_doc_names()

	update_term_line_relationship()

	# create folder
	if(os.path.exists(config.output_folder_name) is False):
		os.mkdir(config.output_folder_name)

	partial_folder_dir = config.output_folder_name + config.partial_index_folder_name

	if(os.path.exists(partial_folder_dir) is False):
		os.mkdir(partial_folder_dir)

	print("----> Running indexer(config)....")
	# create partial index in files with file_name is term
	indexer(config)

	print("----> Running merge_partial_index(config)....")
	# merge all partial index
	merge_partial_index(config)

	print("----> Running write_doc_ids_file(config)....")
	# write doc_ids dicionary to file
	write_doc_ids_file(config)

	print("----> Running write_term_line_relationship_file(config)....")
	# write term_line_relationship file
	write_term_line_relationship_file(config)

	return num_documents, num_terms

# doc_ids,num_documents, total_tokens = read_existing_files(config)

# print_total_tokens()