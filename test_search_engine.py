import json
import os
import tempfile
import unittest
from collections import defaultdict

from helper import (
    get_configurations,
    get_terms_from_query,
    read_anchor_terms_file,
    read_doc_ids_file,
    read_strong_terms_file,
    read_term_line_relationship_file,
)
from indexer import inverted_index
from ranking import get_high_idf_terms
from search import search


class SearchEngineTests(unittest.TestCase):
    def make_config(self, root):
        config = get_configurations()
        config.input_folder_name = os.path.join(root, "DEV") + os.sep
        config.output_folder_name = os.path.join(root, "output") + os.sep
        config.partial_index_folder_name = "partial_index" + os.sep
        config.doc_id_file_name = os.path.join(config.output_folder_name, "doc_ids.bin")
        config.anchor_terms_file_name = os.path.join(config.output_folder_name, "anchor_terms.bin")
        config.term_line_relationship_file_name = os.path.join(
            config.output_folder_name, "term_line_relationships.bin"
        )
        config.index_file_name = os.path.join(config.output_folder_name, "index.bin")
        config.query_cache_file_name = os.path.join(config.output_folder_name, "query_cache.bin")
        config.strong_terms_file_name = os.path.join(config.output_folder_name, "strong_terms.bin")
        config.result_database_file_name = "sqlite:///" + os.path.join(
            config.output_folder_name, "result.db"
        )
        config.max_documents_per_batch = 2
        return config

    def write_document(self, folder, name, url, title, body):
        os.makedirs(folder, exist_ok=True)
        with open(os.path.join(folder, name), "w", encoding="utf-8") as handle:
            json.dump(
                {
                    "url": url,
                    "content": f"<html><title>{title}</title><body>{body}</body></html>",
                },
                handle,
            )

    def test_index_and_search_end_to_end(self):
        with tempfile.TemporaryDirectory() as root:
            config = self.make_config(root)
            corpus = os.path.join(config.input_folder_name, "site")

            self.write_document(
                corpus,
                "python.json",
                "https://example.test/python",
                "Python Search",
                "python indexing retrieval engine uniquealpha",
            )
            self.write_document(
                corpus,
                "graph.json",
                "https://example.test/graph",
                "Graph Networks",
                "graph network barabasi erdos uniquebeta",
            )
            self.write_document(
                corpus,
                "database.json",
                "https://example.test/database",
                "Database Systems",
                "database storage transactions uniquegamma",
            )

            num_documents, num_terms = inverted_index(config)
            self.assertEqual(num_documents, 3)
            self.assertGreater(num_terms, 3)

            doc_ids = read_doc_ids_file(config)
            term_lines = read_term_line_relationship_file(config)
            strong_terms = read_strong_terms_file(config)
            anchor_terms = read_anchor_terms_file(config)

            results, only_stop_words = search(
                config,
                get_terms_from_query("python retrieval"),
                doc_ids,
                term_lines,
                strong_terms,
                anchor_terms,
            )

            self.assertFalse(only_stop_words)
            self.assertGreaterEqual(len(results), 1)
            self.assertEqual(doc_ids[results[0]][1], "https://example.test/python")

            no_results, only_stop_words = search(
                config,
                get_terms_from_query("termdoesnotexist"),
                doc_ids,
                term_lines,
                strong_terms,
                anchor_terms,
            )
            self.assertEqual(no_results, [])
            self.assertFalse(only_stop_words)

    def test_empty_query(self):
        config = get_configurations()
        result, only_stop_words = search(
            config,
            [],
            defaultdict(bool),
            defaultdict(bool),
            defaultdict(bool),
            defaultdict(bool),
        )
        self.assertEqual(result, [])
        self.assertFalse(only_stop_words)

    def test_high_idf_threshold_terminates_for_common_terms(self):
        config = get_configurations()
        config.threshold_high_idf_terms = 0.1
        config.threshold_increase_percent = 0.2
        postings = {
            "common": {0: object(), 1: object(), 2: object()},
        }
        result = get_high_idf_terms(config, 3, ["common"], postings)
        self.assertEqual(result, ["common"])


if __name__ == "__main__":
    unittest.main()
