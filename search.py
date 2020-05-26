import os, sys

from collections import defaultdict
from collections import OrderedDict

from ranking import ranking
from helper import search_term_posting_in_index

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


# main search function: currently still use boolean retrieval AND
# return the query result as a dictionary of doc_id and its score
def search(config, query_terms,term_line_relationship, prev_cache):
	global cache

	cache = prev_cache

	query_terms = list(OrderedDict.fromkeys(query_terms))

	if len(query_terms) == 0:
		return None

	query_postings = get_query_postings(config,query_terms,term_line_relationship)

	if query_postings is None:
		return None

	query_result = ranking(config,query_terms,query_postings)

	return query_result