import json

from tests.sparql import QueryTestCase
from tests.tornado_cases import TornadoAsyncHTTPTestCase
from brainiak import server


class PatchInstanceTestCase(TornadoAsyncHTTPTestCase, QueryTestCase):

    fixtures_by_graph = {"http://on.to/": ["tests/sample/people.ttl"]}
    maxDiff = None

    def get_app(self):
        return server.Application()

    def setUp(self):
        data = {
            "instance": "http://on.to/flipperTheDolphin",
            "class": "http://on.to/Person",
            "graph": "http://on.to/",
            "meta": "0"
        }
        self.test_url = '/_/_/_/?graph_uri={graph}&class_uri={class}&instance_uri={instance}&meta_properties={meta}&lang=en&expand_uri=0'
        self.test_url = self.test_url.format(**data)
        super(PatchInstanceTestCase, self).setUp()

    def test_patch_existent_instance_succeeds(self):
        # Check original state
        response = self.fetch(self.test_url, method='GET')
        computed = json.loads(response.body)
        self.assertEqual(response.code, 200)
        expected = {
            u'http://on.to/weight': 200.0,
            u'http://on.to/isHuman': False,
            u'http://on.to/name': u'Flipper',
            u'http://on.to/age': 4,
            u'rdf:type': u'http://on.to/Person'
        }
        self.assertEqual(computed, expected)

        patch_list = [
            {
                "op": "replace",
                "path": "http://on.to/age",
                "value": 5
            }
        ]

        response = self.fetch(self.test_url, method='PATCH', body=json.dumps(patch_list))
        self.assertEqual(response.code, 200)
        self.assertEqual(response.body, "")

        # Check if it was updated
        response = self.fetch(self.test_url, method='GET')
        computed = json.loads(response.body)
        expected = {
            u'http://on.to/weight': 200.0,
            u'http://on.to/isHuman': False,
            u'http://on.to/name': u'Flipper',
            u'http://on.to/age': 5,
            u'rdf:type': u'http://on.to/Person'
        }
        self.assertEqual(computed, expected)

    def test_patch_fails_due_to_removal_of_obligatory_field(self):
        patch_list = [
            {
                u'path': 'http://on.to/name',
                u'op': u'remove'
            }
        ]

        response = self.fetch(self.test_url, method='PATCH', body=json.dumps(patch_list))
        self.assertEqual(response.code, 400)
        computed_msg = json.loads(response.body)
        expected_msg = {"errors": ["HTTP error: 400\nLabel properties like rdfs:label or its subproperties are required"]}
        self.assertEqual(computed_msg, expected_msg)

    def test_patch_inexistent_instance_is_created(self):
        # Delete instance so it does not affect the test to create an instance with PATCH
        delete_response = self.fetch(self.test_url, method='DELETE')
        self.assertEqual(delete_response.code, 204)

        expected_data_after_creation = {
            u'http://on.to/weight': 200.0,
            u'http://on.to/isHuman': False,
            u'http://on.to/name': u'Flipper',
            u'http://on.to/age': 4,
            u'rdf:type': u'http://on.to/Person'
        }

        patch_list = [
            {
                "op": "add",
                "path": u'http://on.to/weight',
                "value": 200.0
            },
            {
                "op": "add",
                "path": u'http://on.to/isHuman',
                "value": False
            },
            {
                "op": "add",
                "path": u'http://on.to/name',
                "value": u'Flipper'
            },
            {
                "op": "add",
                "path": u'http://on.to/age',
                "value": 4
            },
            {
                "op": "add",
                "path": u'rdf:type',
                "value": u'http://on.to/Person'
            }
        ]

        # Make sure instance does not exist
        get_response_before_creation = self.fetch(self.test_url)
        self.assertEqual(get_response_before_creation.code, 404)

        patch_response = self.fetch(self.test_url, method='PATCH', body=json.dumps(patch_list))
        self.assertEqual(patch_response.code, 201)

        get_response_after_creation = self.fetch(self.test_url)
        instance_data_result = json.loads(get_response_after_creation.body)
        self.assertEqual(expected_data_after_creation, instance_data_result)
