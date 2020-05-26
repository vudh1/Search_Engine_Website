import os, sys
from collections import defaultdict
from collections import OrderedDict

# sort terms - postings (helper function) by increasing frequency
def sort_query_order(query_postings):
	tot_freqs = dict()

	for term, posting in query_postings.items():
		tot_freq = 0

		for doc_id, entry in posting.items():
			tot_freq += entry.get_freq()

		# tot_freq = sum([entry.get_freq() for entry in list(query_postings.values())])

		tot_freqs[term] = tot_freq

	sorted_tot_freqs = sorted(tot_freqs.items(), key=lambda kv: kv[1])

	sorted_query_terms = list(OrderedDict(sorted_tot_freqs).keys())

	return sorted_query_terms


# return the intersection list using boolean retrieval AND without positions
def boolean_retrieval_without_positions(query_postings):
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


# ranking function

def ranking(config,query_terms,query_postings):
	query_doc_ids = []

	if len(query_terms) == 1:
		posting = query_postings[query_terms[0]]
		query_doc_ids = list(posting.keys())
	else:
		intersection_docs = boolean_retrieval_without_positions(query_postings)

		if intersection_docs is None:
			return None

		query_doc_ids = list(intersection_docs)


	if len(query_doc_ids) == 0:
		return None

	query_doc_score = dict()

	for doc_id in query_doc_ids:
		score = 0

		for term,query_posting in query_postings.items():
			score += query_posting[doc_id].get_tf_idf()

		query_doc_score[doc_id] = score

	reverse_sorted_query_doc_score = sorted(query_doc_score.items(), key = lambda kv:(kv[1], kv[0]),reverse = True)

	query_result = dict(reverse_sorted_query_doc_score)

	return query_result