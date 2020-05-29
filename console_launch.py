#!/usr/bin/python3

import sys, os, time
from collections import defaultdict
from search import search
from indexer import inverted_index
from helper import get_configurations, get_terms_from_query, read_doc_ids_file, read_term_line_relationship_file, read_strong_terms_file,read_anchor_terms_file, print_query_doc_name

#################################################################################################################################


def index(config):
	# M1: inverted index

	time_start = time.process_time()

	num_documents, num_terms = inverted_index(config)

	if num_documents == 0:
		print("No files to index. Exit now")
		sys.exit()

	time_end = time.process_time()

	print("Complete indexing",num_documents, "documents and",num_terms,"terms in", (time_end - time_start),"s\n")


#################################################################################################################################

def query_search(config):

	doc_ids = read_doc_ids_file(config)

	if doc_ids is None:
		doc_ids = defaultdict(bool)

	anchor_terms = read_anchor_terms_file(config)

	if anchor_terms is None:
		strong_terms = defaultdict(bool)

	num_documents = len(doc_ids)

	strong_terms = read_strong_terms_file(config)

	if strong_terms is None:
		strong_terms = defaultdict(bool)

	term_line_relationship = read_term_line_relationship_file(config)

	if term_line_relationship is None:
		term_line_relationship = defaultdict(bool)

	num_terms = len(term_line_relationship)

	cache = defaultdict(bool)

	# M2: query search . for now still using boolean retrieval AND

	loop = True

	while loop:
		query = input("Enter query: ")
		query = query.lower().strip()
		if query == "quit":
			is_quit = input("Enter Y if you want to quit - N if 'quit' is the query: ")
			if is_quit.lower().strip() == "y":
				loop = False
				continue

		# cache = read_cache_file(config)

		time_start = time.process_time()

		try:
			query_terms = get_terms_from_query(query)
			query_result = search(config, query_terms, doc_ids,term_line_relationship, cache, strong_terms, anchor_terms)
		except Exception:
			print("there is some error with the query: ", query,". Please try different query")
			continue
		time_end = time.process_time()

		print_query_doc_name(config,query,doc_ids,query_result,(time_end-time_start)*1000)

		# update_query_cache(config,query_terms,term_line_relationship)
	sys.exit()

#################################################################################################################################


if __name__ == '__main__':

	# if there is an output folder containing inverted index list already, we don't actually need to update it and just do query search

	config = get_configurations()

	if config is None:
		print("No config file. Exit now")
		sys.exit()

	is_update = input("\nDo You Want to Update Inverted Index List (Y/N): ")

	if is_update.lower().strip() == "y":
		index(config)

	query_search(config)

	sys.exit()