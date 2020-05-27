#!/usr/bin/python3

import sys, os, time

from indexer import inverted_index
from search import search
from helper import get_configurations
from helper import read_doc_ids_file
from helper import read_term_line_relationship_file
from helper import get_terms_from_query
from helper import print_query_doc_name
from helper import update_query_cache
from helper import read_cache_file
from helper import read_strong_index_file

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
	# store doc_ids in memory for fast retrieval (since doc_ids_file is supposed to need small memory space)

	print("Reading doc_ids file ...")

	doc_ids = read_doc_ids_file(config)
	if doc_ids is None:
		print("Doc_ids file is empty or does not exist. Exit now")
		sys.exit()
	print("Complete reading doc_ids file\n")


	print("Reading strong_index file ... ")

	strong_index = read_strong_index_file(config)
	if strong_index is None:
		print("strong_index file is empty or does not exist. Exit now")
		sys.exit()
	print("Complete reading strong_index file\n")

	# store term_line_relationship for fast retrieval (since term_line_relationship file is supposed to need small memory space)

	print("Reading term_line_relationship file ... ")

	term_line_relationship = read_term_line_relationship_file(config)
	if term_line_relationship is None:
		print("term_line_relationship file is empty or does not exist. Exit now")
		sys.exit()
	print("Complete reading term_line_relationship file\n")

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

		cache = read_cache_file(config)

		time_start = time.process_time()

		try:
			query_terms = get_terms_from_query(query)
			query_result = search(config, query_terms, doc_ids,term_line_relationship, cache, strong_index)
		except Exception:
			print("there is some error with the query: ", query,". Please try different query")
			continue
		time_end = time.process_time()

		print_query_doc_name(config,query,doc_ids,query_result,(time_end-time_start)*1000)

		update_query_cache(config,query_terms,term_line_relationship)
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









