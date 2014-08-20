from mock import patch
from unittest import TestCase

from jsonschema import ValidationError
from tornado.web import HTTPError

from brainiak.utils.json import validate_json_schema,\
    get_json_request_as_dict


class JSONTestCase(TestCase):

    JSON_SCHEMA_EXAMPLE = {
        "type": "object",
        "required": ["items"],
        "properties": {
            "items": {"type": "array"}
        }
    }

    def test_get_valid_json(self):
        valid_json_string = '{"items": []}'
        response = get_json_request_as_dict(valid_json_string)
        self.assertEqual(response["items"], [])

    def test_get_invalid_json(self):
        invalid_json_string = '{[][]}'
        self.assertRaises(HTTPError,
                          get_json_request_as_dict,
                          invalid_json_string)

    @patch("brainiak.utils.json.validate")
    def test_valid_json_schema(self, mocked_validate):
        valid_json = {"items": []}
        validate_json_schema(valid_json,
                             self.JSON_SCHEMA_EXAMPLE)

    @patch("brainiak.utils.json.validate", side_effect=ValidationError("aa"))
    def test_invalid_json_schema(self, mocked_validate):
        valid_json = {"items": {}}  # not an array
        self.assertRaises(HTTPError,
                          validate_json_schema,
                          valid_json,
                          self.JSON_SCHEMA_EXAMPLE)

    def test_json_with_escaped_quotes(self):
        expected = 'SELECT ?o ?label_o FROM <http://semantica.globo.com/esportes/> WHERE { ?s a esportes:MateriaEsporte . ?s base:permalink "http://globoesporte.globo.com/futebol/times/fluminense/noticia/2011/04/conca-x-200-timidez-brincadeiras-genialidade-e-gols-pelo-fluminense.html" . ?s ?p ?o . ?p a owl:ObjectProperty . ?o rdfs:label ?label_o . '
        json_request_body = '''{ "sparql_template": "SELECT ?o ?label_o FROM <http://semantica.globo.com/esportes/> WHERE { ?s a esportes:MateriaEsporte . ?s base:permalink \\"http://globoesporte.globo.com/futebol/times/fluminense/noticia/2011/04/conca-x-200-timidez-brincadeiras-genialidade-e-gols-pelo-fluminense.html\\" . ?s ?p ?o . ?p a owl:ObjectProperty . ?o rdfs:label ?label_o . ", "description": "a" }'''
        result_dict = get_json_request_as_dict(json_request_body)
        self.assertEqual(result_dict["sparql_template"], expected)
