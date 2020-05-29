import os, sys

from collections import defaultdict, OrderedDict

from ranking import ranking
from helper import search_term_posting_in_index
from helper import stem_stop_words

cache = defaultdict(bool)

# get terms - postings from inverted index list according to query terms
def get_query_postings(config,total_query_terms,term_line_relationship):
	global cache

	unique_query_terms = list(OrderedDict.fromkeys(total_query_terms))

	query_postings = defaultdict(bool)

	for term in unique_query_terms:
		# term not exist in cache
		# if cache[term] == False:
		resource_term_posting = search_term_posting_in_index(config,term,term_line_relationship)
		if resource_term_posting is not None:
			query_postings[term] = defaultdict(bool, resource_term_posting[term])
		# term exists in cache
		# else:
		# 	query_postings[term] = cache[term][0]

	return query_postings


# main search function: currently still use boolean retrieval AND
# return the query result as a dictionary of doc_id and its score
def search(config, old_total_query_terms, doc_ids,term_line_relationship, prev_cache, strong_terms, anchor_terms):
	global cache

	if old_total_query_terms == 0:
		return []

	cache = prev_cache

	# remove stop words
	new_total_query_terms = [i for i in old_total_query_terms if stem_stop_words[i] == False]

	# only stop words in the query, use the same query
	if len(new_total_query_terms) == 0:
		new_total_query_terms = old_total_query_terms

	query_postings = get_query_postings(config,new_total_query_terms,term_line_relationship)

	if query_postings is None:
			return []

	query_result = ranking(config, doc_ids,new_total_query_terms,strong_terms, anchor_terms,query_postings)

	if query_result is None:
		query_result = []

	if len(query_result) > config.max_num_urls_per_query:
			query_result = query_result[:config.max_num_urls_per_query]

	return query_result