List of Collections
===================

This service retrieves all classes of a specific context (i.e. graph).
The results are paginated.

**Basic usage**

.. code-block:: bash

  $ curl -s 'http://brainiak.semantica.dev.globoi.com/place/'

This will retrieve all classes in the ``place`` graph.

.. code-block:: json

  {
    "@context": {
        "@language": "pt"
    },
    "@id": "http://semantica.globo.com/place/",
    "_base_url": "http://brainiak.semantica.dev.globoi.com/place",
    "_first_args": "page=1",
    "_next_args": "page=2",
    "items": [
        {
            "@id": "http://semantica.globo.com/place/City",
            "class_prefix": "http://semantica.globo.com/place/",
            "resource_id": "City",
            "title": "Cidade"
        },
        {
            "@id": "http://semantica.globo.com/place/Country",
            "class_prefix": "http://semantica.globo.com/place/",
            "resource_id": "Country",
            "title": "Pa\u00eds"
        }
    ]
  }


Optional parameters
-------------------

.. include :: ../params/default.rst
.. include :: ../params/graph_uri.rst
.. include :: ../params/pages.rst
.. include :: ../params/item_count.rst


Possible responses
-------------------

**Status 200**

If there are classes in this graph, the response body is a JSON containing classes' titles and @ids (URIs).
By default, the first page containing 10 items is returned (``?page=1&per_page=10``).

.. code-block:: bash

  $ curl -s 'http://brainiak.semantica.dev.globoi.com/place/?page=1&per_page=10'

.. code-block:: json

  {
    "@context": {
        "@language": "pt"
    },
    "@id": "http://semantica.globo.com/place/",
    "_base_url": "http://brainiak.semantica.dev.globoi.com/place",
    "_first_args": "page=1",
    "_next_args": "page=2",
    "items": [
        {
            "@id": "http://semantica.globo.com/place/City",
            "class_prefix": "http://semantica.globo.com/place/",
            "resource_id": "City",
            "title": "Cidade"
        },
        {
            "@id": "http://semantica.globo.com/place/Country",
            "class_prefix": "http://semantica.globo.com/place/",
            "resource_id": "Country",
            "title": "Pa\u00eds"
        }
    ]
  }

If there are no classes for this graph, the response will contain a warning and a items list empty.

.. include :: examples/list_collections_no_results.rst


**Status 400**

If there are unknown parameters in the request query string, the response status code is 400.
A JSON containing both the wrong parameters and the accepted ones is returned.

.. code-block:: json

    {
        "errors": [
            "HTTP error: 400\nArgument invalid_param is not supported. The supported querystring arguments are: do_item_count, expand_uri, graph_uri, lang, page, per_page, sort_by, sort_include_empty, sort_order."
        ]
    }

**Status 404**

If the graph does not exist, the response status code is 404.

.. include :: examples/list_collections_404.rst

**Status 500**

If there was some internal problem, the response status code is a 500.
Please, contact semantica@corp.globo.com informing the URL and the JSON returned.

