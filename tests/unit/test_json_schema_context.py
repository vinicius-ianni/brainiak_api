# -*- coding: utf-8 -*-

import unittest
from brainiak.context.json_schema import build_href


class TestContextJsonSchema(unittest.TestCase):

    def test_build_href(self):
        query_params = {'context_name': 'place',
                        'expand_uri': '1'
                        }
        computed = build_href(query_params)
        self.assertIn('expand_uri=1', computed)
