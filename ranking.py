import os, sys,math
from collections import defaultdict
from collections import OrderedDict
from threading import Thread,Lock

total_scores = defaultdict(lambda : 0)

# sort terms - postings (helper function) by increasing frequency
def sort_query_order(query_postings):
	tot_freqs = dict()

	for term, posting in query_postings.items():
		tot_freq = 0

		for doc_id, entry in posting.items():
			tot_freq += entry.get_freq()

		tot_freqs[term] = tot_freq

	sorted_tot_freqs = sorted(tot_freqs.items(), key=lambda kv: kv[1])

	sorted_query_terms = list(OrderedDict(sorted_tot_freqs).keys())

	return sorted_query_terms


# match position values
def get_intersections_from_positions(config, unique_query_terms,query_postings,query_doc_ids):
	positional_scores = defaultdict(lambda : False)

	for i in range(0,len(query_doc_ids)):
		doc_id = query_doc_ids[i]

		gap = 0

		intersection_positions = set()

		for j in range(len(unique_query_terms)):
			posting = query_postings[unique_query_terms[j]]

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

	for doc_id in query_doc_ids:
		positional_scores[doc_id] *= config.default_score_boolean_and_position
		positional_scores[doc_id] += config.default_score_boolean_and

	return positional_scores


# return the intersection list using boolean retrieval AND without positions
def boolean_and_retrieval(query_postings):

	if len(query_postings) == 0:
		return None

	sorted_query_terms = sort_query_order(query_postings)

	intersection_docs = set((query_postings[sorted_query_terms[0]]).keys())

	for i in range(1,len(sorted_query_terms)):
		intersection_docs = intersection_docs.intersection(set((query_postings[sorted_query_terms[i]]).keys()))
		if intersection_docs is None:
			return None
		if len(intersection_docs) == 0:
			return None

	return list(intersection_docs)


# calculate position scores
def calculate_positional_scores(config,unique_query_terms,query_postings):
	global total_scores

	query_doc_ids = boolean_and_retrieval(query_postings)

	if query_doc_ids is None:
		return None

	positional_scores = get_intersections_from_positions(config,unique_query_terms,query_postings,query_doc_ids)

	for doc_id, positional_score in positional_scores.items():
		total_scores[doc_id] += positional_score

	# return positional_scores

# return the intersection list using boolean retrieval AND without positions
def boolean_or_retrieval(unique_query_terms, query_postings):
	union_docs = set()

	if len(query_postings) == 0:
		return None

	for term in unique_query_terms:
		union_docs = union_docs.union(set((query_postings[term]).keys()))

	return list(union_docs)


def get_wtq(total_query_terms):
	wtq = defaultdict(lambda : 0)

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


def get_wtds(total_query_terms, unique_query_terms, query_postings):

	union_docs = boolean_or_retrieval(unique_query_terms, query_postings)

	wtds = defaultdict(lambda : False)

	for doc_id in union_docs:
		wtds[doc_id] = defaultdict(lambda : 0)

	for doc_id in union_docs:
		for term in unique_query_terms:
			if query_postings[term].get(doc_id,False) != False:
				wtds[doc_id][term] = query_postings[term][doc_id].get_tf_idf()
			else:
				wtds[doc_id][term] = 0

	return wtds


def calculate_cosine_scores(doc_ids,total_query_terms,unique_query_terms,query_postings):
	global total_scores

	cosine_scores = defaultdict(lambda : 0)

	wtq, normalized_wtq = get_wtq(total_query_terms)

	wtds = get_wtds(total_query_terms, unique_query_terms, query_postings)

	for doc_id,wtd in wtds.items():

		normalized_wtd = doc_ids[doc_id][2]
		dot_product = 0
		cosine_value = 0

		for term in unique_query_terms:
			dot_product += wtq[term] * wtd[term]

		if normalized_wtd != 0 and normalized_wtq != 0:
			cosine_value = dot_product / (normalized_wtd * normalized_wtq)

		cosine_scores[doc_id] = cosine_value

	for doc_id, cosine_score in cosine_scores.items():
		total_scores[doc_id] += cosine_score

def calculate_strong_index_scores(config, strong_index, unique_query_terms):
	global total_scores

	strong_index_scores = defaultdict(lambda : 0)

	for term in unique_query_terms:
		if strong_index.get(term,False) != False:
			for doc_id,_ in strong_index[term].items():
				strong_index_scores[doc_id] += config.default_score_strong_index

	for doc_id, strong_index_score in strong_index_scores.items():
		total_scores[doc_id] += strong_index_score

# ranking function

def calculate_scores(config, doc_ids, total_query_terms, strong_index, query_postings):
	global total_scores

	total_scores = defaultdict(lambda : 0)

	unique_query_terms = list(query_postings.keys())

	threads = []

	threads.append(Thread(target = calculate_cosine_scores, args = (doc_ids,total_query_terms,unique_query_terms,query_postings)))

	threads.append(Thread(target = calculate_positional_scores, args = (config, unique_query_terms,query_postings)))

	threads.append(Thread(target = calculate_strong_index_scores, args = (config, strong_index, unique_query_terms)))

	for thread in threads:
		thread.start()

	for thread in threads:
		thread.join()

	sorted_total_scores = sorted(total_scores.items(), key = lambda kv:(kv[1], kv[0]),reverse = True)

	return dict(sorted_total_scores)

def ranking(config, doc_ids, total_query_terms, strong_index, query_postings):

	query_doc_ids = []

	# difference from total query terms that the user input,
	# all terms in query terms exist in inverted index
	unique_query_terms = list(query_postings.keys())

	if len(unique_query_terms) == 0:
		return None

	elif len(unique_query_terms) == 1:
		posting = query_postings[unique_query_terms[0]]

		query_doc_ids = list(posting.keys())

		query_doc_scores = dict()

		query_doc_scores = {doc_id : posting[doc_id].get_freq() for doc_id in query_doc_ids}

		sorted_query_doc_scores = sorted(query_doc_scores.items(), key = lambda kv:(kv[1], kv[0]),reverse = True)

		query_result = list(dict(sorted_query_doc_scores).keys())

		return query_result

	else:

		scores = calculate_scores(config, doc_ids, total_query_terms, strong_index, query_postings)

		query_result = list(scores.keys())

		return query_result