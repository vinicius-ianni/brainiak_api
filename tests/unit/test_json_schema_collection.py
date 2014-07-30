# -*- coding: utf-8 -*-

import unittest
from brainiak.collection.json_schema import build_link


class TestCollectionJsonSchema(unittest.TestCase):

    def test_build_link(self):
        query_params = {'class_name': 'Country',
                        'context_name': 'place',
                        'expand_uri': '1'
                        }
        computed = build_link(query_params)
        self.assertIn('expand_uri=1', computed)
