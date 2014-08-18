from mock import patch
from brainiak.utils.sparql import QUERY_VALUE_EXISTS, is_result_true, find_graph_from_class, \
    find_graph_and_class_from_instance
from tests.sparql import QueryTestCase


class ValidateUniquenessTestCase(QueryTestCase):

    graph_uri = "http://example_alternative.onto/"
    fixtures_by_graph = {
        graph_uri: ["tests/sample/animalia.n3"]
    }
    maxDiff = None

    @patch("brainiak.triplestore.log")
    def test_query(self, mock_log):
        query_params = {
            "graph_uri": self.graph_uri,
            "class_uri": "http://example.onto/City",
            "instance_uri": "http://example.onto/York",
            "predicate_uri": "http://example.onto/nickname",
            "object_value": '"City of York"'
        }
        query = QUERY_VALUE_EXISTS % query_params
        query_result = self.query(query)
        self.assertTrue(is_result_true(query_result))

    @patch("brainiak.triplestore.log")
    def test_query_answer_false(self, mock_log):
        query_params = {
            "graph_uri": self.graph_uri,
            "class_uri": "http://example.onto/City",
            "instance_uri": "http://example.onto/York",
            "predicate_uri": "http://example.onto/nickname",
            "object_value": '"Unexistent value"'
        }
        query = QUERY_VALUE_EXISTS % query_params
        query_result = self.query(query)
        self.assertFalse(is_result_true(query_result))

    @patch("brainiak.triplestore.log")
    def test_find_graph_from_class_with_existing_class(self, mock_log):
        class_uri = "http://example.onto/FurLenght"
        graph_uri = find_graph_from_class(class_uri)
        self.assertEqual(graph_uri, "http://example_alternative.onto/")

    @patch("brainiak.triplestore.log")
    def test_find_graph_and_class_from_instance(self, mock_log):
        instance_uri = "http://example.onto/Nina"
        graph_uri, class_uri = find_graph_and_class_from_instance(instance_uri)
        self.assertEqual(graph_uri, "http://example_alternative.onto/")
        self.assertEqual(class_uri, "http://example.onto/Yorkshire_Terrier")
