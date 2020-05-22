import time
import json
import sys
import logging
from time import sleep
from flask import Flask, render_template, url_for, flash, redirect, request
from forms import QueryTerm

from search import search
from indexer import indexer

from helper import get_configurations
from helper import query_prepare

app = Flask(__name__)
app.config['SECRET_KEY'] = '012345678998765433210'
log = logging.getLogger('werkzeug')
log.disabled = True
# app.logger.disabled = True

#################################################################################################################################

print()

def search_ui(query,term_line_relationship):
	config = get_configurations()

	if config is None:
		print("No config file. Exit now")
		sys.exit()

	time_start = time.process_time()
	query_ids_results = []

	try:
		query_results = search(config,query,term_line_relationship)
	except Exception:
		return query, query_ids_results, 0

	time_end =time.process_time()
	time_process = round((time_end-time_start)*1000)


	if query_results is not None:
		query_ids_results = list(query_results.keys())

	# print(query_ids_results)
	return config,query,query_ids_results,time_process



#################################################################################################################################

@app.route("/",methods = ['GET', 'POST'])
@app.route("/home",methods = ['GET', 'POST'])
def home():
	doc_ids,term_line_relationship = query_prepare()

	num_documents = 0
	num_terms = 0

	if doc_ids is not None:
		num_documents = len(doc_ids)

	if term_line_relationship is not None:
		num_terms = len(term_line_relationship)

	form = QueryTerm()
	if form.validate_on_submit():
		config, query,query_ids_results,query_time = search_ui(str(form.query_terms.data), term_line_relationship)

		num_result_urls = len(query_ids_results)

		doc_name_results = []

		for i in range(num_result_urls):
			if i < int(config.max_num_urls_per_query):
				doc_name_results.append(doc_ids[str(query_ids_results[i])])

		messages = json.dumps({"query" : query, "doc_name_results": doc_name_results, "query_time" : query_time, "num_result_urls" : num_result_urls})

		return redirect(url_for('result', messages = messages))
	return render_template('home.html', title ='Home', num_documents = num_documents, num_terms = num_terms, form = form)

@app.route("/about")
def about():
	return render_template('about.html', title='About')

@app.route("/update")
def update():
	config = get_configurations()

	if config is None:
		print("No config file. Exit now")
		sys.exit()

	time_start = time.process_time()

	extra_num_documents = indexer(config)

	time_end = time.process_time()

	indexer_time = round(time_end - time_start)

	doc_ids,term_line_relationship = query_prepare()

	num_terms = 0

	if term_line_relationship is not None:
		num_terms = len(term_line_relationship)

	num_documents = 0

	if doc_ids is not None:
		num_documents = len(doc_ids)

	return render_template('update.html', title ='Update', indexer_time = indexer_time, extra_num_documents = extra_num_documents, num_documents = num_documents, num_terms = num_terms)

@app.route("/result")
def result():
	messages = json.loads(request.args['messages'])
	return render_template('result.html', title='Result', query = messages["query"],
					 doc_name_results = messages["doc_name_results"], length = messages["num_result_urls"] , query_time = messages["query_time"])

def initial_indexer():

	config = get_configurations()

	if config is None:
		print("No config file. Exit now")
		sys.exit()

	print("\nIndexing document ...")
	time_start = time.process_time()

	num_documents = indexer(config)
	if num_documents == 0:
		print("No files to index. Exit now")

	time_end = time.process_time()

	print("Complete indexing",num_documents, "documents in", (time_end - time_start),"s\n")

	print("WebUI is ready to use ... \n")

if __name__ == '__main__':
	initial_indexer()

