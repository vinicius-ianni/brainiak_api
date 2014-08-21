from unittest import TestCase
from brainiak.utils.config_parser import ConfigParserNoSectionError, parse_section, \
    get_all_configs, format_all_configs


class ConfigParserTestCase(TestCase):

    maxDiff = None

    def test_parse_config_file_and_other_section(self):
        local_ini = "src/brainiak/triplestore.ini"
        response = parse_section(local_ini, "other")
        expected_response = {
            'url': 'http://localhost:8890/sparql-auth',
            'app_name': 'Other',
            'auth_mode': 'digest',
            'auth_username': 'one_user',
            'auth_password': 'one_password'
        }
        self.assertEqual(response, expected_response)

    def test_parse_default_config_file_and_default_section(self):
        response = parse_section()
        expected_response = {
            'url': 'http://localhost:8890/sparql-auth',
            'app_name': 'Brainiak',
            'auth_mode': 'digest',
            'auth_username': 'dba',
            'auth_password': 'dba'
        }
        self.assertEqual(response, expected_response)

    def test_parse_inexistent_section(self):
        self.assertRaises(ConfigParserNoSectionError, parse_section, **{"section": "xubiru"})

    def test_get_all_configs(self):
        expected = {
            'default': {
                'url': 'http://localhost:8890/sparql-auth',
                'auth_username': 'dba',
                'app_name': 'Brainiak'},
            'other': {
                'url': 'http://localhost:8890/sparql-auth',
                'auth_username': 'one_user',
                'app_name': 'Other'},
            'another': {
                'url': 'http://localhost:8890/sparql-auth',
                'auth_username': 'dba',
                'app_name': 'Another'}
        }
        result = get_all_configs()
        self.assertEqual(result, expected)

    def test_format_all_configs(self):
        expected = "[default]<br><br>app_name = Brainiak<br>auth_username = dba<br>url = http://localhost:8890/sparql-auth<br><br>[other]<br><br>app_name = Other<br>auth_username = one_user<br>url = http://localhost:8890/sparql-auth<br><br>"
        input_dict = {
            'default': {
                'url': 'http://localhost:8890/sparql-auth',
                'auth_username': 'dba',
                'app_name': 'Brainiak'},
            'other': {
                'url': 'http://localhost:8890/sparql-auth',
                'auth_username': 'one_user',
                'app_name': 'Other'}
        }
        result = format_all_configs(input_dict)
        self.assertEqual(result, expected)
