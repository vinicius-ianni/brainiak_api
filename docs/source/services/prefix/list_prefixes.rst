List of Prefixes
================

This service retrieves registered prefixes, used in compact communication with the API.

**Basic usage**

.. code-block:: bash

  $ curl -s 'http://brainiak.semantica.dev.globoi.com/_prefixes'


Optional parameters
-------------------

.. include :: ../params/pages.rst


Possible responses
-------------------

**Status 200**

The response body is a JSON containing the prefixes in a "@context" section
and the root context, which is a context whose name is not in the prefix URI.

.. code-block:: json

    {
        "@context": {
            "dbpedia": "http://dbpedia.org/ontology/",
            "dc": "http://purl.org/dc/elements/1.1/"
        }
    }

**Status 400**

If there are unknown parameters in the request query string, the response status code is 400.
A JSON containing both the wrong parameters and the accepted ones is returned.

.. code-block:: json

    {
        "errors": [
            "HTTP error: 400\nO argumento invalid_param não é suportado. Os argumentos de querystring suportados são: do_item_count, expand_uri, graph_uri, lang, page, per_page, sort_by, sort_include_empty, sort_order."]
    }

**Status 500**

If there was some internal problem, the response status code is a 500.
Please, contact semantica@corp.globo.com informing the URL and the JSON returned.
