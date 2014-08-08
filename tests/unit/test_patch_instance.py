import unittest

from tornado.web import HTTPError

from brainiak.instance.patch_instance import apply_patch, _get_value, \
    _get_operation_and_predicate, get_instance_data_from_patch_list


class PatchTestCase(unittest.TestCase):

    def test_apply_patch_replace_succeeds(self):
        instance_data = {
            u'http://on.to/name': u'Flipper',
            u'http://on.to/age': 4
        }
        patch_list = [
            {
                u'path': u'http://on.to/age',
                u'value': 5,
                u'op': u'replace'
            }
        ]
        computed = apply_patch(instance_data, patch_list)
        expected = {
            u'http://on.to/name': u'Flipper',
            u'http://on.to/age': 5
        }
        self.assertEqual(computed, expected)

    def test_apply_patch_replace_with_add_semantics(self):
        instance_data = {
            u'http://on.to/name': u'Flipper',
            u'http://on.to/age': 4
        }
        patch_list = [
            {
                u'path': u'http://on.to/birthDate',
                u'value': '2014-08-01',
                u'op': u'replace'
            }
        ]
        computed = apply_patch(instance_data, patch_list)
        expected = {
            u'http://on.to/name': u'Flipper',
            u'http://on.to/age': 4,
            u'http://on.to/birthDate': '2014-08-01'
        }
        self.assertEqual(computed, expected)

    def test_apply_patch_with_wrong_keys_raises_400(self):
        instance_data = {}
        patch_list = [
            {
                'wrong key': 'any value'
            }
        ]
        self.assertRaises(HTTPError, apply_patch, instance_data, patch_list)

    def test_apply_patch_remove_succeeds(self):
        instance_data = {
            'http://on.to/name': u'Flipper',
            'http://on.to/weight': 200.0
        }
        patch_list = [
            {
                u'path': 'http://on.to/weight',
                u'op': u'remove'
            }
        ]
        computed = apply_patch(instance_data, patch_list)
        expected = {
            u'http://on.to/name': u'Flipper',
        }
        self.assertEqual(computed, expected)

    def test_apply_patch_remove_succeeds_for_inexistent_key(self):
        instance_data = {
            'http://on.to/name': u'Flipper',
            'http://on.to/weight': 200.0
        }
        patch_list = [
            {
                u'path': 'http://on.to/age',
                u'op': u'remove'
            }
        ]
        computed = apply_patch(instance_data, patch_list)
        self.assertEqual(computed, instance_data)

    def test_apply_patch_remove_succeeds_for_expanded_uri(self):
        instance_data = {
            'http://dbpedia.org/ontology/name': u'Francis'
        }
        patch_list = [
            {
                u'path': 'dbpedia:name',
                u'op': u'remove'
            }
        ]
        computed = apply_patch(instance_data, patch_list)
        expected = {}
        self.assertEqual(computed, expected)

    def test_apply_patch_add_inexistent_data_succeeds(self):
        instance_data = {
        }
        patch_list = [
            {
                u'path': 'http://on.to/children',
                u'op': u'add',
                u'value': u'Mary'
            }
        ]
        computed = apply_patch(instance_data, patch_list)
        expected = {
            u'http://on.to/children': [u'Mary'],
        }
        self.assertEqual(computed, expected)

    def test_apply_patch_add_list_data_succeeds(self):
        instance_data = {
            'http://on.to/children': ['Dave', 'Eric']
        }
        patch_list = [
            {
                u'path': 'http://on.to/children',
                u'op': u'add',
                u'value': [u'Mary', u'John']
            }
        ]
        computed = apply_patch(instance_data, patch_list)
        expected = {
            u'http://on.to/children': ['Dave', 'Eric', 'John', 'Mary'],
        }
        self.assertEqual(computed, expected)

    def test_apply_patch_replace_unsupported_operation(self):
        instance_data = {
            'http://on.to/children': ['Dave', 'Eric']
        }
        patch_list = [
            {
                u'path': 'http://on.to/children',
                u'op': u'unsupported',
                u'value': [u'Mary', u'John']
            }
        ]
        self.assertRaises(HTTPError, apply_patch, instance_data, patch_list)

    def test_get_value(self):
        item = {"op": "replace", "path": "", "value": "test:123"}
        expected = "test:123"
        result = _get_value(item)
        self.assertEqual(result, expected)

    def test_get_value_raises_400(self):
        item = {"op": "replace", "path": ""}
        self.assertRaises(HTTPError, _get_value, item)

    def test_get_operation_and_predicate(self):
        item = {"op": "replace", "path": "test:path", "value": "test:123"}
        expected = ("replace", "test:path")
        result = _get_operation_and_predicate(item)
        self.assertEqual(result, expected)

    def test_get_operation_and_predicate_raises_400(self):
        item = {"missing_keys_op_path": 123, "value": "test:123"}
        self.assertRaises(HTTPError, _get_operation_and_predicate, item)

    def test_get_instance_data_from_patch_list(self):
        patch_list = [
            {"op": "replace", "path": "test:mother", "value": "test:mother_123"},
            {"op": "add", "path": "test:age", "value": 26}]
        expected = {
            "test:mother": "test:mother_123",
            "test:age": 26
        }
        result = get_instance_data_from_patch_list(patch_list)
        self.assertEqual(result, expected)
