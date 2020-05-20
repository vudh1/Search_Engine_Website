import re

from configparser import ConfigParser

# adding more config variables here after adding in 'config.ini' file for using

class Config(object):

	#read configurations for file names and values
	def __init__(self, config):
		self.input_folder_name = config["FILE_NAME"]["INPUT_FOLDER_NAME"]
		self.output_folder_name = config["FILE_NAME"]["OUTPUT_FOLDER_NAME"]

		# doc_id and name file
		self.doc_id_file_name = self.output_folder_name + config["FILE_NAME"]["DOC_IDS_FILE_NAME"]

		# terms_to_postings file : this is all inverted_index list
		self.postings_file_name = self.output_folder_name + config["FILE_NAME"]["TERMS_TO_POSTINGS_FILE_NAME"]

		# term_line_relationship file: this file store the line number of the term which can be found in postings_file_name
		self.term_line_relationship_file_name = self.output_folder_name + config["FILE_NAME"]["TERM_LINE_RELATIONSHIP_FILE_NAME"]

		# the number of urls printed to console after query
		self.max_num_urls_per_query = config["NUMBERS"]["MAX_NUM_URLS_PER_QUERY"]

def read_config_file(config_file):
	cparser = ConfigParser()
	cparser.read(config_file)
	config = Config(cparser)
	return config