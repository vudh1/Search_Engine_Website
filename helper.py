import os
from nltk.stem.porter import *

import pickle
from pickle import UnpicklingError

import re
from config import read_config_file

from collections import OrderedDict
from collections import defaultdict

# read the configurations (file names, values, etc.)
# used by: console_launch, web_launch
def get_configurations():
	# read the configurations (file names, values, etc.)
	config = read_config_file("config.ini")
	return config


# tokenize and stemming the query
# used by: console_launch, web_launch
def get_terms_from_query(query):
	regex = re.compile('[^a-z0-9A-Z]')
	query = regex.sub(' ', query).lower()
	stemmer = PorterStemmer()

	query_terms = [stemmer.stem(i) for i in query.split() if len(i) >= 2]
	return query_terms


# read doc_id.json for doc_id and name of the files
# used by: helper, console_launch, web_launch
def read_doc_ids_file(config):
	if(os.path.exists(config.doc_id_file_name) is True):
		with open(config.doc_id_file_name, 'rb') as f:
			doc_ids = pickle.load(f)

			return doc_ids
	return dict()


# read term_line_relationships.bin for the line number of each term in index.bin for faster retrieval
# used by: helper, console_launch, web_launch
def read_term_line_relationship_file(config):
	if(os.path.exists(config.term_line_relationship_file_name) is True):
		with open(config.term_line_relationship_file_name, 'rb') as f:
			try:
				term_line_relationship = pickle.load(f)
				return term_line_relationship

			except (EOFError, UnpicklingError):
			 	return None

	return None


#print query result to console output
#used by: console_launch
def print_query_doc_name(config,query,doc_ids,query_result,time):
	time = round(time,2)

	if query_result is not None:
		print("Retrieved a total of " + str(len(query_result)) +  " documents of '" + str(query)+"' in "+str(time)+"ms.")

		query_ids = list(query_result.keys())

		for i in range(len(query_ids)):
			if i < int(config.max_num_urls_per_query):
				print(doc_ids[query_ids[i]])
			else:
				break
	else:
		print("Retrieved a total of " + "0" +  " documents of '" + str(query)+"' in "+str(time)+"ms.")

	print("")


#directly read at a specific line in terms_to_postings.json for term_posting information without storing large data in memory
#used by: helper
def search_term_posting_at_specific_line(config,line_offset):
	resource_term_posting = defaultdict(lambda : False)

	if(os.path.exists(config.index_file_name) is True):
		with open(config.index_file_name, 'rb') as f:
			f.seek(line_offset,0)
			try:
				data = pickle.load(f)
				term = list(data.keys())[0]
				resource_term_posting[term] = data[term]

			except (EOFError, UnpicklingError):
			 		return resource_term_posting
	return resource_term_posting


# get term - posting
# used by: search, helper
def search_term_posting_in_index(config, term, term_line_relationship):
	line_offset = term_line_relationship.get(term,False)

	if line_offset == False:
		return None

	resource_term_posting = search_term_posting_at_specific_line(config,line_offset)

	return resource_term_posting

#read cache file
#used by: helper, search
def read_cache_file(config):
	cache = defaultdict(lambda : False)

	if os.path.exists(config.query_cache_file_name) is True:
		with open(config.query_cache_file_name, 'rb') as f:
				try:
					data = pickle.load(f)
					for term, posting_and_count in data.items():
						cache[term] = tuple([posting_and_count[0],posting_and_count[1]])
				except (EOFError, UnpicklingError):
					return cache
	return cache

# update query_cache
# use by console_launch, web_launch
def update_query_cache(config,query_terms,term_line_relationship):
	cache = read_cache_file(config)

	for term in query_terms:
		# term not exist in cache
		if cache[term] == False:
			resource_term_posting = search_term_posting_in_index(config, term,term_line_relationship)

			if resource_term_posting is not None:
				cache[term] = tuple([resource_term_posting[term],1])
			else:
				return

		#term exist in cache
		else:
			cache[term] = tuple([cache[term][0],cache[term][1] + 1])

	if len(cache) > 1:
		sorted_cache = sorted(cache.items(), key=lambda kv: kv[1][1])

	while len(sorted_cache) > config.max_num_query_cache_entries:
		sorted_cache.pop(0)

	sorted_cache_result = dict(sorted_cache)

	with open(config.query_cache_file_name, 'wb') as f:
		pickle.dump(sorted_cache_result,f)


# generate permutations for near duplicate check
# used by: indexer
def generate_permutations_for_sim_hash(sim_hash_result):
	block_1 = sim_hash_result[:11]
	block_2 = sim_hash_result[11:22]
	block_3 = sim_hash_result[22:33]
	block_4 = sim_hash_result[33:44]
	block_5 = sim_hash_result[44:54]
	block_6 = sim_hash_result[54:]

	p = []

	p.append([block_4 + block_5 + block_6 , block_1 + block_2 + block_3 ])
	p.append([block_3 + block_4 + block_6 , block_1 + block_2 + block_5 ])
	p.append([block_1 + block_3 + block_6 , block_2 + block_4 + block_5 ])
	p.append([block_1 + block_4 + block_5 , block_2 + block_3 + block_6 ])
	p.append([block_2 + block_3 + block_4 , block_1 + block_5 + block_6 ])
	p.append([block_3 + block_5 + block_6 , block_1 + block_2 + block_4 ])
	p.append([block_2 + block_4 + block_6 , block_1 + block_3 + block_5 ])
	p.append([block_1 + block_2 + block_6 , block_3 + block_4 + block_5 ])
	p.append([block_2 + block_3 + block_5 , block_1 + block_4 + block_6 ])
	p.append([block_1 + block_3 + block_4 , block_2 + block_5 + block_6 ])
	p.append([block_2 + block_5 + block_6 , block_1 + block_3 + block_4 ])
	p.append([block_1 + block_4 + block_6 , block_2 + block_3 + block_5 ])
	p.append([block_3 + block_4 + block_5 , block_1 + block_2 + block_6 ])
	p.append([block_1 + block_3 + block_5 , block_2 + block_4 + block_6 ])
	p.append([block_1 + block_2 + block_4 , block_3 + block_5 + block_6 ])
	p.append([block_1 + block_5 + block_6 , block_2 + block_3 + block_4 ])
	p.append([block_2 + block_3 + block_6 , block_1 + block_4 + block_5 ])
	p.append([block_2 + block_4 + block_5 , block_1 + block_3 + block_6 ])
	p.append([block_1 + block_2 + block_5 , block_3 + block_4 + block_6 ])
	p.append([block_1 + block_2 + block_3 , block_4 + block_5 + block_6 ])

	return p



# # read previous index file
# # used by: helper
# def read_previous_index_file(config):
# 	total_tokens = OrderedDict()
# 	partial_folder_dir = config.output_folder_name + config.partial_index_folder_name

# 	term_ids = defaultdict(lambda : False)

# 	num_terms = 0

# 	if(os.path.exists(config.index_file_name) is True):
# 		term_line_relationship = read_term_line_relationship_file(config)

# 		if term_line_relationship is not None:

# 			with open(config.index_file_name, 'rb') as f:

# 				for term, offset in term_line_relationship.items():
# 					try:

# 						if(os.path.exists(partial_folder_dir) is False):
# 							os.mkdir(partial_folder_dir)

# 						f.seek(offset,0)
# 						data = pickle.load(f)

# 						term_ids[term] = num_terms
# 						num_terms += 1

# 						with open(partial_folder_dir+str(term_ids[term]),'ab') as sub_f:
# 							pickle.dump(data[term],sub_f)

# 					except (KeyError,EOFError, UnpicklingError):
# 						continue
# 			return term_ids, num_terms

# 	return term_ids, 0


# # read existing files to avoid re-read same documents
# # used by: indexer
# def read_existing_files(config):
# 	# store doc_ids in memory for fast retrieval (since doc_ids_file is supposed to need small memory space)

# 	doc_ids = dict()
# 	num_documents = 0
# 	num_terms = 0
# 	term_ids = defaultdict(lambda : False)

# 	if(os.path.exists(config.output_folder_name) is False):
# 		return doc_ids,num_documents,term_ids,num_terms

# 	doc_ids = read_doc_ids_file(config)

# 	if doc_ids is None:
# 		return dict(),num_documents,term_ids,num_terms

# 	num_documents = len(doc_ids)

# 	term_ids, num_terms = read_previous_index_file(config)

# 	return doc_ids,num_documents,term_ids,num_terms

