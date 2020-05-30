import os, sys

from collections import defaultdict, OrderedDict

from ranking import ranking
from helper import search_term_posting_in_index
from helper import stem_stop_words

# get terms - postings from inverted index list according to query terms
def get_query_postings(config,total_query_terms,term_line_relationship):
	unique_query_terms = list(OrderedDict.fromkeys(total_query_terms))

	query_postings = defaultdict(bool)

	for term in unique_query_terms:
		resource_term_posting = search_term_posting_in_index(config,term,term_line_relationship)
		if resource_term_posting is not None:
			query_postings[term] = defaultdict(bool, resource_term_posting[term])

	return query_postings


# main search function: currently still use boolean retrieval AND
# return the query result as a dictionary of doc_id and its score
def search(config, total_query_terms, doc_ids,term_line_relationship, strong_terms, anchor_terms):

	# as return empty after tokenizing
	if total_query_terms == 0:
		return [], False

	# remove stop words
	total_query_terms = [i for i in total_query_terms if stem_stop_words[i] == False]

	# only stop words in the query, use the same query
	if len(total_query_terms) == 0:
		return [], True
	else:
		query_postings = get_query_postings(config,total_query_terms,term_line_relationship)

		if query_postings is None:
			return []

		query_result = ranking(config, doc_ids,total_query_terms,strong_terms, anchor_terms,query_postings)

		if query_result is None:
			query_result = []

		# only choose the top K result
		if len(query_result) > config.max_num_urls_per_query:
			query_result = query_result[:config.max_num_urls_per_query]

		return query_result, False