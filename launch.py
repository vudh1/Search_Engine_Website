import sys
import time

from config import read_config_file

from indexer import indexer

from search import search

from helper import read_doc_ids_file
from helper import read_term_line_relationship
from helper import print_query_doc_name


#################################################################################################################################


def get_configurations():

	# read the configurations (file names, values, etc.)
	print("\nReading config file ...")

	config = read_config_file("config.ini")

	print("Complete reading config file ...\n")

	return config

#################################################################################################################################


def inverted_index(config):

	if config is None:
		print("No config file. Exit now")
		sys.exit()

	# M1: inverted index

	print("Indexing document ...")
	time_start = time.process_time()

	num_documents = indexer(config)
	if num_documents == 0:
		print("No files to index. Exit now")
		sys.exit()

	time_end = time.process_time()

	print("Complete indexing",num_documents, "documents in", (time_end - time_start),"s\n")


#################################################################################################################################


def query_search(config):

	if config is None:
		print("No config file. Exit now")
		sys.exit()

	# store doc_ids in memory for fast retrieval (since doc_ids_file is supposed to need small memory space)

	print("Reading doc_ids file ...")

	doc_ids = read_doc_ids_file(config)
	if doc_ids is None:
		print("Doc_ids file is empty or does not exist. Exit now")
		sys.exit()
	print("Complete reading doc_ids file\n")


	# store term_line_relationship for fast retrieval (since term_line_relationship file is supposed to need small memory space)

	print("Reading term_line_relationship file ... ")

	term_line_relationship = read_term_line_relationship(config)
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

		time_start = time.process_time()

		try:
			query_result = search(config, query,term_line_relationship)
		except Exception:
			print("there is some error with the query: ", query,". Please try different query")
			continue

		time_end = time.process_time()

		print_query_doc_name(config,query,doc_ids,query_result,(time_end-time_start)*1000)

	sys.exit()


#################################################################################################################################


if __name__ == '__main__':

	# if there is an output folder containing inverted index list already, we don't actually need to update it and just do query search

	is_update = input("\nDo You Want to Update Inverted Index List (Y/N): ")

	config = get_configurations()

	if is_update.lower().strip() == "y":
		inverted_index(config)

	query_search(config)

	sys.exit()








