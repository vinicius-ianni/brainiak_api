from tests.tornado_cases import TornadoAsyncHTTPTestCase


class TriplestoreConfigsTest(TornadoAsyncHTTPTestCase):

    def test_get_configs(self):
        expected = "[default]<br><br>app_name = Brainiak<br>auth_username = dba<br>url = http://localhost:8890/sparql-auth<br><br>[other]<br><br>app_name = Other<br>auth_username = one_user<br>url = http://localhost:8890/sparql-auth<br><br>[another]<br><br>app_name = Another<br>auth_username = dba<br>url = http://localhost:8890/sparql-auth<br><br>"
        response = self.fetch("/_triplestore_configs")
        result = response.body
        self.assertEqual(result, expected)

    def test_purge_configs(self):
        # Get configs
        response = self.fetch("/_triplestore_configs")
        self.assertEqual(response.code, 200)

        from brainiak.utils.config_parser import parser
        self.assertFalse(parser is None)

        # Purge configs
        response = self.fetch("/_triplestore_configs", method="PURGE")
        self.assertEqual(response.code, 200)

        from brainiak.utils.config_parser import parser
        self.assertTrue(parser is None)

    def test_other_method_raises_exception(self):
        expected = 405
        response = self.fetch("/_triplestore_configs", method="POST", body=" ")
        result = response.code
        self.assertEqual(result, expected)
