# #!/usr/bin/python3

import time
import sys
import logging
import json
from flask import Flask, render_template, url_for, flash, redirect, request
from flask_sqlalchemy import SQLAlchemy

from forms import QueryTerm

from search import search
from indexer import inverted_index

from helper import get_configurations
from helper import analyze_text
from helper import update_query_cache
from helper import read_doc_ids_file
from helper import read_term_line_relationship_file

app = Flask(__name__)
app.config['SECRET_KEY'] = '012345678998765433210'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///result.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

log = logging.getLogger('werkzeug')

log.disabled = True
# app.logger.disabled = True


class UrlResult(db.Model):
	id = db.Column(db.Integer, primary_key = True)
	url = db.Column(db.String(120), nullable = False)

	def __repr__(self):
		return str(self.url)

# #################################################################################################################################

config = get_configurations()

doc_ids = dict()
term_line_relationship = dict()
num_documents = 0
num_terms = 0

query = ""
query_terms = []

query_time = 0
num_result_urls = 0

# #################################################################################################################################

def search_ui():
	global config
	global query
	global query_terms
	global term_line_relationships

	if config is None:
		print("No config file. Exit now")
		sys.exit()

	time_start = time.process_time()
	query_ids_results = []

	try:
		query_results = search(config,query_terms,term_line_relationship)
	except Exception:
		return query_ids_results, 0

	time_end = time.process_time()
	time_process = round((time_end-time_start)*(10**3))

	if query_results is not None:
		query_ids_results = list(query_results.keys())

	# print(query_ids_results)
	return query_ids_results,time_process


def update_database(query_ids_results):
	global config
	global db

	db.drop_all()

	db.create_all()

	for i in range(len(query_ids_results)):
		db.session.add(UrlResult(url = doc_ids[query_ids_results[i]]))

	db.session.commit()


def update_statistics():
	global config
	global doc_ids
	global term_line_relationship
	global num_documents
	global num_terms

	doc_ids = read_doc_ids_file(config)

	if doc_ids is None:
		doc_ids = dict()

	num_documents = len(doc_ids)

	term_line_relationship = read_term_line_relationship_file(config)

	if term_line_relationship is None:
		term_line_relationship = dict()

	num_terms = len(term_line_relationship)

# #################################################################################################################################

@app.route("/",methods = ['GET', 'POST'])
@app.route("/home",methods = ['GET', 'POST'])
def home():
	global config
	global query
	global query_terms
	global term_line_relationship
	global query_time
	global num_result_urls

	update_statistics()

	form = QueryTerm()

	if form.validate_on_submit():
		query = str(form.query_terms.data)

		query_terms = analyze_text(query)

		query_ids_results,query_time = search_ui()

		update_query_cache(config,query_terms,term_line_relationship)

		num_result_urls = len(query_ids_results)

		update_database(query_ids_results)

		return redirect(url_for('result'))
	return render_template('home.html', title ='Home', num_documents = num_documents, num_terms = num_terms, form = form)

@app.route("/about")
def about():
	return render_template('about.html', title='About')

@app.route("/update")
def update():
	global config
	global query
	global num_documents
	global num_terms
	global term_line_relationship
	global doc_ids

	if config is None:
		print("No config file. Exit now")
		sys.exit()

	time_start = time.process_time()

	num_documents, num_terms = inverted_index(config)

	if num_documents == 0:
		print("No files to index.")

	time_end = time.process_time()

	indexer_time = (time_end - time_start)

	update_statistics()

	return render_template('update.html', title ='Update', indexer_time = indexer_time, num_documents = num_documents, num_terms = num_terms)


@app.route("/result")
def result():
	global config
	global query
	global query_time
	global num_result_urls

	if config is None:
		print("No config file. Exit now")
		sys.exit()

	page = request.args.get('page', 1, type = int)
	result_urls = UrlResult.query.paginate(page = page, per_page = config.max_num_urls_per_query)


	update_query_cache(config,query_terms,term_line_relationship)

	return render_template('result.html', title='Result', query = query,
					 result_urls = result_urls, length = num_result_urls , query_time = query_time)

# #################################################################################################################################

def initial_indexer():
	global config

	if config is None:
		print("No config file. Exit now")
		sys.exit()

	print("\nIndexing document ...")
	time_start = time.process_time()

	num_documents, num_terms = inverted_index(config)

	if num_documents == 0:
		print("No files to index.")

	time_end = time.process_time()

	print("Complete indexing",num_documents, "documents in", (time_end - time_start),"s\n")

	print("WebUI is ready to use ... \n")


# #################################################################################################################################

if __name__ == '__main__':
	initial_indexer()

