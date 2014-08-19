List of Contexts
================

This primitive retrieves a list of contexts where one can define classes and/or instances.
Contexts that contain no data are not listed.

This resource is **cached**. Read :doc:`/services/cache` for more information.

**Basic usage**

.. code-block:: bash

  $ curl -s 'http://brainiak.semantica.dev.globoi.com/'


Optional parameters
-------------------

.. include :: ../params/pages.rst
.. include :: ../params/item_count.rst


Possible responses
-------------------


**Status 200**

If there are contexts, the response body is a JSON containing contexts' titles, resources_id and @ids (URIs).

.. code-block:: json

  {
    "_base_url": "http://brainiak.semantica.dev.globoi.com",
    "_first_args": "page=1",
    "_next_args": "page=2",
    "items": [
        {
            "@id": "http://semantica.globo.com/graph1/",
            "resource_id": "graph1",
            "title": "graph1"
        },
        {
            "@id": "http://semantica.globo.com/sports/",
            "resource_id": "sports",
            "title": "sports"
        }
    ]
  }

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

If there are no contexts, the response status code is a 404.

.. include :: examples/list_context_404.rst

**Status 500**

If there was some internal problem, the response status code is a 500.
Please, contact semantica@corp.globo.com informing the URL and the JSON returned.
