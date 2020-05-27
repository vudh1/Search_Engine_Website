import os, sys, re, math, json, pickle, bs4, shutil, warnings

from nltk.stem.porter import *
from pickle import UnpicklingError
from collections import OrderedDict
from collections import defaultdict

from helper import get_terms_from_query
from helper import generate_permutations_for_sim_hash
from entry import Entry

# disable showing warning when reading using bs4
warnings.filterwarnings("ignore", category=UserWarning, module='bs4')

html_elements = ['head', 'title', 'meta', 'style', 'script', '[document]']

num_documents = 0

num_terms = 0

doc_ids = dict()

doc_urls = defaultdict(lambda : False)

document_lengths = defaultdict(lambda : False)

total_tokens = defaultdict(lambda : False)

strong_index = dict()

term_ids = defaultdict(lambda : False)

term_line_relationship = OrderedDict()

exact_duplicate_hash = defaultdict(lambda : False)

term_hash_bits = defaultdict(lambda : False)

tables = [None] * 64


#############################################################################################


# generate sim hash for document
def sim_hash(terms):
	global term_hash_bits
	global sim_hash_size
	sim_hash_result = [0]*64

	for term in terms:
		# print("new simhash:",sim_hash_result)
		# print(term,term_hash_bits[term])
		# input()
		for i in range(64):
			value = term_hash_bits[term][i] * 2 - 1
			sim_hash_result[i] += value

	for i in range(64):
		if sim_hash_result[i] != 0:
			sim_hash_result[i] = int((sim_hash_result[i] / abs(sim_hash_result[i]) + 1)/2)

	return sim_hash_result


# check similarity according to threshold
def check_similarity(config,right_bits_1,right_bits_2):
	count_diff = 0

	for i in range(len(right_bits_1)):
		if right_bits_1[i] != right_bits_2[i]:
			count_diff += 1
			if count_diff > config.threshold_sim_hash_value:
				return False

	return True


# using hamming distance to compare simhash
def hamming_distance(config,permutations):
	global tables

	count_left_bits = 0

	for i in range(len(permutations)):
		# table list does not fist 20 bits sumhash so create an empty list
		left_bits = ''.join([str(i) for i in permutations[i][0]])

		if tables[i] is None:
			tables[i] = defaultdict(lambda : False)

		if tables[i][left_bits] == False:
			tables[i][left_bits] = []
			count_left_bits += 1

	find_near_duplicate = False

	for i in range(len(permutations)):
		left_bits = ''.join([str(i) for i in permutations[i][0]])
		right_bits  = permutations[i][1]

		is_exist = False
		# check if simhash only if there is no near duplicate
		if find_near_duplicate == False:
			for table_right_bits in tables[i][left_bits]:
				if right_bits == table_right_bits:
					find_near_duplicate = True
					is_exist = True
				else:
					find_near_duplicate = check_similarity(config,right_bits, table_right_bits)

		if is_exist == False:
			tables[i][left_bits].append(right_bits)

	return find_near_duplicate


# check near duplicate algorithm
def check_near_duplicate(config, terms):
	global tables

	sim_hash_result = sim_hash(terms)

	permutations = generate_permutations_for_sim_hash(config, sim_hash_result)

	is_near_duplicate = hamming_distance(config, permutations)

	return is_near_duplicate


#############################################################################################

# analyze text for duplicate and get terms
def analyze_text(config, text,doc_id):
	global term_hash_bits
	global exact_duplicate_hash

	regex = re.compile('[^a-z0-9A-Z]')
	text = regex.sub(' ', text).lower()
	stemmer = PorterStemmer()

	terms = []

	total_bytes = 0
	total_chars = 0

	for i in text.split():
		if len(i) >= 2:
			stem_term = stemmer.stem(i)
			terms.append(stem_term)

			# check for exact duplicate
			total_chars += len(stem_term)
			total_bytes += sum(bytearray(stem_term, 'ascii'))

			#assign a hash number for term
			if term_hash_bits[stem_term] == False:
				term_hash_bits[stem_term] = [int(i) for i in '{:064b}'.format(hash(stem_term) + sys.maxsize + 1)]

	hash_value = 0

	if total_bytes > 0 and total_chars > 0:
		hash_value = (total_bytes%total_chars) + total_chars/total_bytes


	# check for exact duplicate
	if exact_duplicate_hash[hash_value] == False:
		exact_duplicate_hash[hash_value] = doc_id
	else:
		return []


	# # check for near duplicate
	find_near_duplicate = check_near_duplicate(config, terms)

	if find_near_duplicate == True:
		return []

	return terms


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
def add_to_list(config,text,doc_id):
	global num_documents
	global total_tokens
	global exact_duplicate_hash

	terms = analyze_text(config, text, doc_id)

	if terms is None:
		return False

	if len(terms) == 0:
		return False

	positions, frequencies, tf_scores = compute_posting_value(terms)

	for token in positions:
		if total_tokens[token] == False:
			total_tokens[token] = dict()

		entry = Entry(frequencies[token], tf_scores[token], 0, positions[token])
		total_tokens[token][doc_id] = entry

	num_documents += 1

	return True


# merge all entries in a term file
# sort entries in posting by frequency

def get_merge_entries_of_a_term(config,term):
	global term_ids
	global document_lengths

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

	# get tf_idf scores

	for doc_id,entry in posting.items():
		if document_lengths[doc_id] == False:
			document_lengths[doc_id] = 0
		document_lengths[doc_id] += (entry.get_tf_idf()**2)

	os.remove(term_file_name)

	return posting


def update_normalized_document_lengths_after_merge():
	global document_lengths
	global doc_ids

	for doc_id,length in document_lengths.items():
		doc_ids[doc_id][2] = math.sqrt(length)

	document_lengths.clear()

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
		print("Error Delete Folder.")


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


# write doc ids file
def write_doc_ids_file(config):
	update_normalized_document_lengths_after_merge()

	with open(config.doc_id_file_name, 'wb') as f:
		pickle.dump(doc_ids, f)

	doc_ids.clear()

def write_strong_index_file(config):
	global strong_index
	with open(config.strong_index_file_name, 'wb') as f:
		pickle.dump(strong_index, f)

	strong_index.clear()


# write term line relationship file
def write_term_line_relationship_file(config):
	global term_line_relationship

	if(os.path.exists(config.index_file_name) is True):
		with open(config.term_line_relationship_file_name, 'wb') as f:
			pickle.dump(term_line_relationship, f)

	term_line_relationship.clear()

# print total_tokens
def print_total_tokens():
	global total_tokens
	print("\n\n\n")
	num = 0
	for term,posting in total_tokens.items():
		print(num,".",term,end = ": ")
		for doc_id,entry in posting.items():
			print("   ",doc_id,entry.get_freq(),entry.get_tf(),entry.get_tf_idf(),entry.get_positions())
		print("")
		num += 1

	print("Num_total_tokens: ",len(total_tokens))


def smart_truncate(config, content):
	suffix = '...'
	length = config.max_length_for_title
	new_title = ''

	if len(content) <= length:
		new_title = content
	else:
		new_title = ' '.join(content[:length+1].split(' ')[0:-1]) + suffix

	title_terms = get_terms_from_query(new_title)

	return new_title,title_terms

# get doc_title
def set_doc_title(config,soup,doc_id,doc_url):
	global strong_index

	if soup.find('title') is None:
		return doc_url
	else:
		doc_title = ''

		if soup.title.string is not None:
			doc_title = soup.title.string.strip().lstrip()

		if len(doc_title) == 0:
			return doc_url

		new_title, title_terms = smart_truncate(config, doc_title)

		for title_term in title_terms:
			if strong_index.get(title_term,False) == False:
				strong_index[title_term] = dict()

			strong_index[title_term][doc_id] = True

		return new_title


# create index in partial files
def indexer(config):
	global num_documents
	global total_tokens
	global doc_ids
	global doc_urls
	global exact_duplicate_hash
	global term_hash_bits
	global tables

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
						doc_url = str(data["url"]).split("#",1)[0]

						# avoid duplicate file url
						if doc_urls[doc_url] == False:
							doc_title = set_doc_title(config,soup,doc_id,doc_url)

							doc_ids[doc_id] = [doc_title,doc_url,0]
							doc_urls[doc_url] = doc_id

							text = ' '.join(filter(tag, soup.find_all(text=True)))

							is_sucess = add_to_list(config,text,doc_id)

							if is_sucess == True: # no duplicate
								doc_id += 1
							else:
								continue

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
		print("----> Complete Reading " + str(num_documents)+" files...")


	# clear from memory after done
	exact_duplicate_hash.clear()
	term_hash_bits.clear()
	tables.clear()

# clear all previous output
def clean_previous_data(config):
	global num_documents
	global num_terms
	global doc_ids
	global doc_urls
	global document_lengths
	global total_tokens
	global strong_index
	global term_ids
	global term_line_relationship
	global exact_duplicate_hash
	global term_hash_bits
	global tables

	if(os.path.exists(config.output_folder_name) is True):
		try:
			shutil.rmtree(config.output_folder_name)
		except OSError as e:
			print("Error Delete Folder.")

	# create folder
	if(os.path.exists(config.output_folder_name) is False):
		os.mkdir(config.output_folder_name)

	partial_folder_dir = config.output_folder_name + config.partial_index_folder_name

	if(os.path.exists(partial_folder_dir) is False):
		os.mkdir(partial_folder_dir)

	num_documents = 0
	num_terms = 0
	doc_ids = dict()
	doc_urls = defaultdict(lambda : False)
	document_lengths = defaultdict(lambda : False)
	total_tokens = defaultdict(lambda : False)
	strong_index = dict()
	term_ids = defaultdict(lambda : False)
	term_line_relationship = OrderedDict()
	exact_duplicate_hash = defaultdict(lambda : False)
	term_hash_bits = defaultdict(lambda : False)
	tables = [None] * 64


# main inverted index function
def inverted_index(config):
	global num_documents
	global num_terms
	global term_ids
	global doc_urls

	clean_previous_data(config)

	print("\n----> Running indexer(config)....")
	# create partial index in files with file_name is term
	indexer(config)

	print("----> Running merge_partial_index(config)....")
	# merge all partial index
	merge_partial_index(config)

	print("----> Running write_doc_ids_file(config)....")
	# write doc_ids dicionary to file
	write_doc_ids_file(config)

	print("----> Running write_strong_index_file(config)....")
	# write strong_index dicionary to file
	write_strong_index_file(config)

	print("----> Running write_term_line_relationship_file(config)....")
	# write term_line_relationship file
	write_term_line_relationship_file(config)

	print("----> Complete Running Indexer. Ready to Search....\n")

	term_ids.clear()
	doc_urls.clear()
	return num_documents, num_terms