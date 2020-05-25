import os
import sys
import pickle
from pickle import UnpicklingError

from collections import defaultdict
from collections import OrderedDict
from helper import search_term_posting_in_index
from ranking import ranking

cache = defaultdict(lambda : False)

# get terms - postings from inverted index list according to query terms and sort by freqs
def get_query_postings(config,query_terms,term_line_relationship):
	global cache

	query_postings = defaultdict(lambda : False)

	for term in query_terms:
		# term not exist in cache
		if cache[term] == False:
			resource_term_posting = search_term_posting_in_index(config,term,term_line_relationship)
			if resource_term_posting is None:
				print("There is no term ",term,"in the indexer file")
				query_postings = None
				return
			else:
				query_postings[term] = resource_term_posting[term]

		# term exists in cache
		else:
			query_postings[term] = cache[term][0]

	return query_postings

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
	#sort_query_postings(query_postings)
	intersection_docs = set((query_postings[sorted_query_terms[0]]).keys())

	for i in range(1,len(sorted_query_terms)):
		intersection_docs = intersection_docs.intersection(set((query_postings[sorted_query_terms[i]]).keys()))
		if intersection_docs is None:
			return None
		if len(intersection_docs) == 0:
			return None

	return list(intersection_docs)


# main search function: currently still use boolean retrieval AND
# return the query result as a dictionary of doc_id and its score

def search(config, query_terms,term_line_relationship):
	if len(query_terms) == 0:
		return None

	query_postings = get_query_postings(config,query_terms,term_line_relationship)

	if query_postings is None:
		return None

	# for term,posting in query_postings.items():
	# 	print(term, end = ": ")
	# 	for doc_id, entry in posting.items():
	# 		print(doc_id, end = ",")

	# 	print("")

	query_doc_ids = []

	if len(query_terms) == 1:
		posting = query_postings[query_terms[0]]
		query_doc_ids = list(posting.keys())
	else:
		#### this version is with positions
		# intersection_doc_pos = boolean_retrieval_with_position(query_postings)
		# if intersection_doc_pos is None:
		# 	return None
		# query_doc_ids = list(intersection_doc_pos.keys())

		#### this version is without positions
		intersection_docs = boolean_retrieval_without_positions(query_postings)

		if intersection_docs is None:
			return None

		query_doc_ids = list(intersection_docs)

	# print("\nresult: ")
	# print(query_doc_ids)

	query_result = ranking(config,query_doc_ids,query_postings)

	return query_result