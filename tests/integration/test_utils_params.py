# -*- coding: utf-8 -*-
from brainiak.utils.params import ParamDict
from tests.mocks import MockHandler
from tests.sparql import QueryTestCase
from tests.tornado_cases import TornadoAsyncHTTPTestCase


class ParamsResolvingUnderscoresTestCase(TornadoAsyncHTTPTestCase, QueryTestCase):

    fixtures_by_graph = {"http://dbpedia.org/ontology/": ["tests/sample/sports.n3"]}
    maxDiff = None

    def test_unspecified_context_with_just_class_name_must_fail(self):
        handler = MockHandler()
        response = ParamDict(handler, context_name="_", class_uri="News")
        self.assertEqual(response['graph_uri'], '_')

    def test_unspecified_context_with_class_uri_must_set_class_name_and_graph_uri(self):
        handler = MockHandler(querystring="class_uri=http://dbpedia.org/ontology/News")
        response = ParamDict(handler, context_name="_", class_uri="News")
        self.assertEqual(response['graph_uri'], 'http://dbpedia.org/ontology/')
        self.assertEqual(response['class_name'], 'News')

    def test_unspecified_context_and_class_with_just_instance_uri(self):
        handler = MockHandler(querystring="instance_uri=http://dbpedia.org/ontology/Aikido")
        response = ParamDict(handler, context_name="_", class_name="_", instance_uri=None)
        self.assertEqual(response['graph_uri'], 'http://dbpedia.org/ontology/')
        self.assertEqual(response['class_name'], 'Sport')
        self.assertEqual(response['class_uri'], 'http://dbpedia.org/ontology/Sport')
        self.assertEqual(response['context_name'], 'ontology')
