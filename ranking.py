import os, sys,math
from collections import defaultdict, OrderedDict
from threading import Thread,Lock
from helper import stem_stop_words

mutex = Lock()

total_scores = defaultdict(int)


def get_high_idf_terms(config, num_documents, unique_query_terms, query_postings):
	# remove other low-idf terms

	high_idf_terms = list()

	threshod = config.threshold_high_idf_terms

	# keep increase threshold if no high_idf terms found
	while len(high_idf_terms) == 0:
		for term in unique_query_terms:
			if len(query_postings[term])/num_documents <= threshod:
				high_idf_terms.append(term)

		# increase threshold by 10%
		threshod *= (1+config.threshold_increase_percent)

	return high_idf_terms

# runs if multi-term query
def get_docs_to_consider(config, doc_ids, unique_query_terms, query_postings):

	num_documents = len(doc_ids)

	unique_query_terms = get_high_idf_terms(config, num_documents, unique_query_terms, query_postings)

	docs_to_consider = defaultdict(bool)

	docs_has_all_terms = defaultdict(bool)

	if len(unique_query_terms) == 0:
		return unique_query_terms,docs_to_consider, docs_has_all_terms

	if len(unique_query_terms) == 1:
		docs_to_consider = defaultdict(bool,{i : True for i in query_postings[unique_query_terms[0]].keys()})
		return unique_query_terms,docs_to_consider, docs_has_all_terms

	# determine threshold count (~85% query terms)
	min_query_terms_length = math.floor(config.threshold_percent_of_terms_in_docs * len(unique_query_terms))

	# remove doc_ids below threshold
	all_doc_ids = set()

	for term in unique_query_terms:
		all_doc_ids.update(set(query_postings[term].keys()))

	docs_to_terms = defaultdict(int)

	# count the number of terms in doc
	for term in unique_query_terms:
		for doc_id in all_doc_ids:
			if query_postings[term][doc_id] != False:
				docs_to_terms[doc_id] += 1

	docs_to_terms = OrderedDict(sorted(docs_to_terms.items(), key = lambda kv: doc_ids[kv[0]][2],reverse = True))

	num_doc_ids = 0

	for doc_id,num_terms in docs_to_terms.items():
		if num_doc_ids >= config.max_num_urls_per_query:
			break

		if num_terms >= min_query_terms_length:
			# boolean_or
			docs_to_consider[doc_id] = True

			if num_terms >= len(unique_query_terms):
				# boolean_and
				docs_has_all_terms[doc_id] = True

			num_doc_ids += 1

	return unique_query_terms, docs_to_consider, docs_has_all_terms


############################################################################################################


def get_wtq(total_query_terms):
	wtq = defaultdict(int)

	for term in total_query_terms:
		wtq[term] += 1

	for term, freq in wtq.items():
		if freq != 0:
			wtq[term] = 1 + math.log10(freq)

	normalized_wtq = 0

	for term, value in wtq.items():
		normalized_wtq += value**2

	normalized_wtq = math.sqrt(normalized_wtq)

	return wtq, normalized_wtq


def get_wtds(high_idf_terms, query_postings, docs_to_consider):

	wtds = defaultdict(bool)

	docs = list(docs_to_consider.keys())

	for doc_id in docs:
		wtds[doc_id] = defaultdict(int)

	for doc_id in docs:
		for term in high_idf_terms:
			if query_postings[term][doc_id] != False:
				wtds[doc_id][term] = query_postings[term][doc_id].get_tf_idf()
			else:
				wtds[doc_id][term] = 0

	return wtds

# calculate cosine scores

def calculate_cosine_scores(config, docs_to_consider, doc_ids, total_query_terms, high_idf_terms, query_postings):
	cosine_scores = defaultdict(int)

	wtq, normalized_wtq = get_wtq(total_query_terms)

	wtds = get_wtds(high_idf_terms, query_postings, docs_to_consider)

	for doc_id, wtd in wtds.items():
		normalized_wtd = doc_ids[doc_id][2]
		dot_product = 0
		cosine_value = 0

		for term in high_idf_terms:
			dot_product += wtq[term] * wtd[term]

		if normalized_wtd != 0 and normalized_wtq != 0:
			cosine_value = dot_product / (normalized_wtd * normalized_wtq)

		cosine_scores[doc_id] = cosine_value

	update_total_scores(cosine_scores)


############################################################################################################

# match position values
def get_intersections_from_positions(config, high_idf_terms, query_postings, docs_has_all_terms):
	positional_scores = defaultdict(bool)

	docs = list(docs_has_all_terms.keys())
	for i in range(0,len(docs_has_all_terms)):
		doc_id = docs[i]

		gap = 0

		intersection_positions = set()

		for j in range(len(high_idf_terms)):
			posting = query_postings[high_idf_terms[j]]

			if j == 0:
				intersection_positions = set([p for p in posting[doc_id].get_positions()])

			else:
				intersection_positions = intersection_positions.intersection(set([p-gap for p in posting[doc_id].get_positions()]))

			if intersection_positions is None:
				break

			elif len(intersection_positions)  == 0:
				break

			gap += 1

		if intersection_positions is not None:
			if len(intersection_positions) != 0:
				positional_scores[doc_id] = len(intersection_positions)

	for doc_id in docs:
		positional_scores[doc_id] *= config.default_score_boolean_and_position
		positional_scores[doc_id] += config.default_score_boolean_and

	return positional_scores


# calculate position scores
def calculate_positional_scores(config, docs_has_all_terms, high_idf_terms,query_postings):
	if docs_has_all_terms is None:
		return None

	positional_scores = get_intersections_from_positions(config,high_idf_terms,query_postings, docs_has_all_terms)

	update_total_scores(positional_scores)


############################################################################################################

# calculate strong_terms scores like title

def calculate_strong_terms_scores(config, strong_terms, docs_has_all_terms, high_idf_terms):
	strong_terms_scores = defaultdict(int)

	for term in high_idf_terms:
		if strong_terms[term] != False:
			for doc_id in strong_terms[term]:
				if docs_has_all_terms[doc_id] != False:
					strong_terms_scores[doc_id] += config.default_score_strong_terms

	update_total_scores(strong_terms_scores)

############################################################################################################

# calculate anchor text scores like title

def calculate_anchor_terms_scores(config, anchor_terms, docs_has_all_terms, high_idf_terms):
	anchor_text_scores = defaultdict(int)

	for term in high_idf_terms:
		if anchor_terms[term] != False:
			for doc_id in anchor_terms[term]:
				if docs_has_all_terms[doc_id] != False:
					anchor_text_scores[doc_id] += config.default_score_anchor_text

	update_total_scores(anchor_text_scores)


############################################################################################################

def update_total_scores(scores):
	global total_scores
	global mutex


	for doc_id, score in scores.items():
		mutex.acquire()
		total_scores[doc_id] += score
		mutex.release()

# calculate all the scores function
def calculate_scores(config, doc_ids, total_query_terms, strong_terms, anchor_terms,query_postings):
	global total_scores

	unique_query_terms = list(query_postings.keys())

	total_scores = defaultdict(int)

	if len(query_postings) == 1:
		posting = query_postings[unique_query_terms[0]]

		for doc_id in posting.keys():
			total_scores[doc_id] = posting[doc_id].get_freq()

		calculate_anchor_terms_scores(config, anchor_terms, posting, unique_query_terms)

		calculate_strong_terms_scores(config, strong_terms, posting, unique_query_terms)

	else:
		high_idf_terms, docs_to_consider, docs_has_all_terms = get_docs_to_consider(config, doc_ids, unique_query_terms, query_postings)

		if len(high_idf_terms) == 0:
			high_idf_terms = list(set(unique_query_terms))

		threads = []

		if docs_to_consider is not None:
			threads.append(Thread(target = calculate_cosine_scores, args = (config, docs_to_consider, doc_ids, total_query_terms, high_idf_terms, query_postings)))

		if docs_has_all_terms is not None:
			threads.append(Thread(target = calculate_positional_scores, args = (config, docs_has_all_terms, high_idf_terms,query_postings)))

		threads.append(Thread(target = calculate_anchor_terms_scores, args =(config, anchor_terms, docs_has_all_terms, high_idf_terms)))

		threads.append(Thread(target = calculate_strong_terms_scores, args = (config, strong_terms, docs_has_all_terms, high_idf_terms)))

		for thread in threads:
			thread.start()

		for thread in threads:
			thread.join()

		# calculate_cosine_scores(config, docs_to_consider, doc_ids, total_query_terms, high_idf_terms, query_postings)
		# calculate_positional_scores(config, docs_has_all_terms, high_idf_terms,query_postings)
		# calculate_anchor_terms_scores(config, anchor_terms, docs_has_all_terms, high_idf_terms)
		# calculate_strong_terms_scores(config, strong_terms, docs_has_all_terms, high_idf_terms)

	sorted_total_scores = OrderedDict(sorted(total_scores.items(), key = lambda kv:(kv[1], kv[0]),reverse = True))

	return sorted_total_scores

# main ranking function
def ranking(config, doc_ids,total_query_terms,strong_terms, anchor_terms,query_postings):
	query_doc_ids = []

	if len(query_postings) == 0:
		return None

	else:
		scores = calculate_scores(config, doc_ids, total_query_terms, strong_terms, anchor_terms,query_postings)

		query_result = list(scores.keys())

		return query_result