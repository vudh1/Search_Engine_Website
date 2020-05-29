import os, sys, re, pickle

from nltk.stem.porter import *
from pickle import UnpicklingError
from collections import OrderedDict, defaultdict

from config import read_config_file

stem_stop_words = defaultdict(bool, {'about': True, 'abov': True, 'after': True, 'again': True, 'against': True, 'all': True, 'am': True, 'an': True, 'and': True, 'ani': True, 'are': True, 'aren': True, 'as': True, 'at': True, 'be': True, 'becaus': True, 'been': True, 'befor': True, 'below': True, 'between': True, 'both': True, 'but': True, 'by': True, 'can': True, 'cannot': True, 'could': True, 'couldn': True, 'did': True, 'didn': True, 'do': True, 'doe': True, 'doesn': True, 'don': True, 'down': True, 'dure': True, 'each': True, 'few': True, 'for': True, 'from': True, 'further': True, 'had': True, 'hadn': True, 'ha': True, 'hasn': True, 'have': True, 'haven': True, 'he': True, 'll': True, 'her': True, 'here': True, 'herself': True, 'him': True, 'himself': True, 'hi': True, 'how': True, 've': True, 'if': True, 'in': True, 'into': True, 'is': True, 'isn': True, 'it': True, 'itself': True, 'let': True, 'me': True, 'more': True, 'most': True, 'mustn': True, 'my': True, 'myself': True, 'no': True, 'nor': True, 'not': True, 'of': True, 'off': True, 'on': True, 'onc': True, 'onli': True, 'or': True, 'other': True, 'ought': True, 'our': True, 'ourselv': True, 'out': True, 'over': True, 'own': True, 'same': True, 'shan': True, 'she': True, 'should': True, 'shouldn': True, 'so': True, 'some': True, 'such': True, 'than': True, 'that': True, 'the': True, 'their': True, 'them': True, 'themselv': True, 'then': True, 'there': True, 'these': True, 'they': True, 're': True, 'thi': True, 'those': True, 'through': True, 'to': True, 'too': True, 'under': True, 'until': True, 'up': True, 'veri': True, 'wa': True, 'wasn': True, 'we': True, 'were': True, 'weren': True, 'what': True, 'when': True, 'where': True, 'which': True, 'while': True, 'who': True, 'whom': True, 'whi': True, 'with': True, 'won': True, 'would': True, 'wouldn': True, 'you': True, 'your': True, 'yourself': True, 'yourselv': True})


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


# read doc_id.bin for doc_id and name of the files
# used by: helper, console_launch, web_launch
def read_anchor_terms_file(config):
	if(os.path.exists(config.anchor_terms_file_name) is True):
		with open(config.anchor_terms_file_name, 'rb') as f:
			anchor_terms = defaultdict(bool,dict(pickle.load(f)))

			return anchor_terms
	return defaultdict(bool)

# read doc_id.bin for doc_id and name of the files
# used by: helper, console_launch, web_launch
def read_doc_ids_file(config):
	if(os.path.exists(config.doc_id_file_name) is True):
		with open(config.doc_id_file_name, 'rb') as f:
			doc_ids = defaultdict(bool,dict(pickle.load(f)))

			return doc_ids
	return defaultdict(bool)

# read strong_terms.bin for strong index and its doc_id of the files
# used by: helper, console_launch, web_launch
def read_strong_terms_file(config):
	if(os.path.exists(config.strong_terms_file_name) is True):
		with open(config.strong_terms_file_name, 'rb') as f:
			strong_terms = defaultdict(bool,pickle.load(f))

			return strong_terms
	return defaultdict(bool)

# read term_line_relationships.bin for the line number of each term in index.bin for faster retrieval
# used by: helper, console_launch, web_launch
def read_term_line_relationship_file(config):
	if(os.path.exists(config.term_line_relationship_file_name) is True):
		with open(config.term_line_relationship_file_name, 'rb') as f:
			try:
				term_line_relationship = defaultdict(bool,pickle.load(f))
				return term_line_relationship

			except (EOFError, UnpicklingError):
			 	return defaultdict(bool)
	return defaultdict(bool)


#print query result to console output
#used by: console_launch
def print_query_doc_name(config,query,doc_ids,query_result,time):
	time = round(time,2)

	if query_result is not None:
		print("Retrieved a total of " + str(len(query_result)) +  " documents of '" + str(query)+"' in "+str(time)+"ms.")

		for i in range(len(query_result)):
			if i < int(config.max_num_urls_per_page):
				print(doc_ids[query_result[i]][0], ": ",doc_ids[query_result[i]][1])
			else:
				break
	else:
		print("Retrieved a total of " + "0" +  " documents of '" + str(query)+"' in "+str(time)+"ms.")

	print("")


#directly read at a specific line in terms_to_postings.json for term_posting information without storing large data in memory
#used by: helper
def search_term_posting_at_specific_line(config,line_offset):
	resource_term_posting = defaultdict(bool)

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
	line_offset = term_line_relationship[term]

	if line_offset == False:
		return None

	resource_term_posting = search_term_posting_at_specific_line(config,line_offset)

	return resource_term_posting

#read cache file
#used by: helper, search
def read_cache_file(config):
	cache = defaultdict(bool)

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

	sorted_cache = dict()

	if len(cache) > 1:
		sorted_cache = sorted(cache.items(), key=lambda kv: kv[1][1])

	while len(sorted_cache) > config.max_num_query_cache_terms:
		sorted_cache.pop(0)

	sorted_cache_result = dict(sorted_cache)

	with open(config.query_cache_file_name, 'wb') as f:
		pickle.dump(sorted_cache_result,f)


# generate permutations for near duplicate check
# used by: indexer
def generate_permutations_for_sim_hash(config, sim_hash_result):
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

