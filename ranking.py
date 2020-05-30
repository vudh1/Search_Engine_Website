import os, sys,math
from collections import defaultdict, OrderedDict
from threading import Thread,Lock
from helper import stem_stop_words

mutex = Lock()

total_scores = defaultdict(lambda : [0,0,0]) # first element : cosine ;  second : strong terms + anchor text ; third : pageRank

# remove other low-idf terms
def get_high_idf_terms(config, num_documents, unique_query_terms, query_postings):

	high_idf_terms = list()

	threshod = config.threshold_high_idf_terms

	# keep increase threshold until at least one high_idf term is found, or stop until threshold is 1
	while len(high_idf_terms) == 0 or threshod > 1:
		for term in unique_query_terms:
			if len(query_postings[term])/num_documents <= threshod:
				high_idf_terms.append(term)

		# increase threshold
		threshod *= (1+config.threshold_increase_percent)

	return high_idf_terms


# get all docs that has majority of the query terms combining with (boolean OR, boolean AND)
def get_docs_to_consider(config, doc_ids, unique_query_terms, query_postings):

	num_documents = len(doc_ids)

	# get unique and more important terms
	unique_query_terms = get_high_idf_terms(config, num_documents, unique_query_terms, query_postings)

	docs_to_consider = defaultdict(bool)

	docs_has_all_terms = defaultdict(bool)

	# safe case if all terms are too common, this should not exist if threshold is keeping increasing
	if len(unique_query_terms) == 0:
		return unique_query_terms,docs_to_consider, docs_has_all_terms

	# if there is only one term, return all of its doc_ids
	if len(unique_query_terms) == 1:
		docs_to_consider = defaultdict(bool,{i : True for i in query_postings[unique_query_terms[0]].keys()})
		return unique_query_terms,docs_to_consider, docs_has_all_terms

	# determine threshold to determine what should be the number as majority of terms
	min_query_terms_length = math.floor(config.threshold_percent_of_terms_in_docs * len(unique_query_terms))

	# remove doc_ids below threshold
	all_doc_ids = set()

	for term in unique_query_terms:
		all_doc_ids.update(set(query_postings[term].keys()))

	docs_to_terms = defaultdict(int)

	# count the number of terms in docs
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
			# boolean_or: getting all doc_ids that qualifies the threshold
			docs_to_consider[doc_id] = True

			if num_terms >= len(unique_query_terms):
				# boolean_and: getting only the doc_ids that has all the terms
				docs_has_all_terms[doc_id] = True

			num_doc_ids += 1

	return unique_query_terms, docs_to_consider, docs_has_all_terms


############################################################################################################

# get w(term,query)
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

# get all w(term,document)
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

	update_total_scores(cosine_scores,0)


############################################################################################################

# match position values for boolean AND
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

	update_total_scores(positional_scores,0)


############################################################################################################

# calculate strong_terms scores (title, bold, etc)
def calculate_strong_terms_scores(config, strong_terms, docs_has_all_terms, high_idf_terms):
	strong_terms_scores = defaultdict(int)

	for term in high_idf_terms:
		if strong_terms[term] != False:
			for doc_id in strong_terms[term]:
				if docs_has_all_terms[doc_id] != False:
					strong_terms_scores[doc_id] += config.default_score_strong_terms

	update_total_scores(strong_terms_scores,1)

############################################################################################################

# calculate anchor text scores
def calculate_anchor_terms_scores(config, anchor_terms, docs_has_all_terms, high_idf_terms):
	anchor_text_scores = defaultdict(int)

	for term in high_idf_terms:
		if anchor_terms[term] != False:
			for doc_id in anchor_terms[term]:
				if docs_has_all_terms[doc_id] != False:
					anchor_text_scores[doc_id] += config.default_score_anchor_text

	update_total_scores(anchor_text_scores,1)


############################################################################################################


# calculate pageRank scores
def calculate_page_ranking_scores(config, doc_ids, docs_has_all_terms):
	page_rank_scores = defaultdict(int)

	for doc_id in docs_has_all_terms:
		page_rank_scores[doc_id] = doc_ids[doc_id][3]

	update_total_scores(page_rank_scores,2)


############################################################################################################

# update total scores for ranking
def update_total_scores(scores, index):
	global total_scores
	global mutex


	for doc_id, score in scores.items():
		mutex.acquire()
		if index == 0:
			total_scores[doc_id][0] += score
		else:
			total_scores[doc_id][0] += score
			total_scores[doc_id][1] += score
		mutex.release()

# calculate all the scores function
def calculate_scores(config, doc_ids, total_query_terms, strong_terms, anchor_terms,query_postings):
	global total_scores

	unique_query_terms = list(query_postings.keys())

	total_scores = defaultdict(lambda : [0,0,0])

	if len(query_postings) == 1:
		posting = query_postings[unique_query_terms[0]]

		for doc_id in posting.keys():
			total_scores[doc_id][0] = posting[doc_id].get_freq()

		calculate_page_ranking_scores(config, doc_ids, list(posting.keys()))

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

		threads.append(Thread(target = calculate_page_ranking_scores, args = (config, doc_ids, docs_has_all_terms)))

		for thread in threads:
			thread.start()

		for thread in threads:
			thread.join()

	# after sorting, the more important documents will be showed fist
	sorted_total_scores = OrderedDict(sorted(total_scores.items(), key = lambda kv:(kv[1][0], kv[1][2]),reverse = True))


	# sort the first 2 page that has the most importance with more priority for page that has strong terms and anchor texts
	if len(sorted_total_scores) > config.max_num_urls_per_page*2:
		sorted_total_scores_1 = OrderedDict(list(sorted_total_scores.items())[:config.max_num_urls_per_page*2])
		sorted_total_scores_2 = OrderedDict(list(sorted_total_scores.items())[config.max_num_urls_per_page*2:])

		# for top results, sort with strong important words
		sorted_total_scores_1 = OrderedDict(sorted(sorted_total_scores_1.items(), key = lambda kv:(kv[1][1] * kv[1][0]),reverse = True))

		# combine first 2 pages with the rest
		sorted_total_scores = OrderedDict(list(sorted_total_scores_1.items()) + list(sorted_total_scores_2.items()))

	else:
		# for top results, sort with strong important words
		sorted_total_scores = OrderedDict(sorted(total_scores.items(), key = lambda kv:(kv[1][1] * kv[1][0]),reverse = True))

	return sorted_total_scores


# main ranking function
def ranking(config, doc_ids,total_query_terms,strong_terms, anchor_terms,query_postings):
	query_doc_ids = []

	# no information found in inverted index
	if len(query_postings) == 0:
		return None

	else:

		# get scores
		scores = calculate_scores(config, doc_ids, total_query_terms, strong_terms, anchor_terms,query_postings)

		# convert to list of doc_ids
		query_result = list(scores.keys())

		return query_result


