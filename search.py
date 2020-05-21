import os
import sys
import re

from helper import analyze_text
from helper import get_query_postings


# return just doc_ids list from the given posting of a term

def get_doc_ids_list(posting):
	doc_pos = dict()

	for entry in posting:
		doc_pos[entry["doc_id"]] = entry["positions"]

	return doc_pos


# return a tf_idf_score of the given doc_id and given posting of a term

def find_tf_idf_score(posting,doc_id):
	for entry in posting:
		if entry['doc_id'] == doc_id:
			return entry['tf_idf']

	return 0


# return the positions that the 2 terms appear next to each other

def intersection_positions(positions_a,positions_b,gap):
	x = set(positions_a)

	y = set()

	for i in positions_b:
		y.add(i-gap)

	return list(x.intersection(y))

# return the intersection list of docs-positions of 2 terms

def intersection_docs_positions(doc_pos_a,doc_pos_b,gap):
	intersection_doc_pos = dict()

	for doc_a,pos_a in doc_pos_a.items():
		if doc_a in list(doc_pos_b.keys()):
			pos_b = doc_pos_b[doc_a]
			intersection_pos = intersection_positions(pos_a,pos_b,gap)

			if len(intersection_pos) > 0:
				intersection_doc_pos[doc_a] = intersection_pos

	return intersection_doc_pos


# return the intersection list using boolean retrieval AND

def boolean_retrieval(query_postings):
	if len(query_postings) == 0:
		return None

	intersection_doc_pos = get_doc_ids_list(query_postings[0]["posting"])

	gap = 1

	for i in range(len(query_postings)):
		if i+1 < len(query_postings):
			next_doc_pos = get_doc_ids_list(query_postings[i+1]["posting"])
			intersection_doc_pos = intersection_docs_positions(intersection_doc_pos,next_doc_pos,i+1)

	if len(intersection_doc_pos) > 0:
		return intersection_doc_pos

	return None


# main search function: currently still use boolean retrieval AND
# return the query result as a dictionary of doc_id and its score

def search(config, query,term_line_relationship):
	query_terms = analyze_text(query)
	if len(query_terms) == 0:
		return None

	query_postings = get_query_postings(config,query_terms,term_line_relationship)

	if query_postings is None:
		return None

	query_doc_ids = []

	if len(query_terms) == 1:
		posting = query_postings[0]["posting"]
		for entry in posting:
			query_doc_ids.append(entry["doc_id"])
	else:
		intersection_doc_pos = boolean_retrieval(query_postings)
		if intersection_doc_pos is None:
			return None
		query_doc_ids = list(intersection_doc_pos.keys())

	if len(query_doc_ids) == 0:
		return None

	query_doc_score = dict()

	for doc_id in query_doc_ids:
		score = 0

		for query_posting in query_postings:
			score += find_tf_idf_score(query_posting["posting"],doc_id)

		query_doc_score[doc_id] = score

	reverse_sorted_query_doc_score = sorted(query_doc_score.items(), key = lambda kv:(kv[1], kv[0]),reverse = True)

	query_result = dict(reverse_sorted_query_doc_score)

	return query_result