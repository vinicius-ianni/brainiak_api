List of Instances
=================

This service retrieves all instances of a specific class or Instances
according a propert/value filter. The results are paginated.

**Basic usage**

.. code-block:: bash

  $ curl -s 'http://brainiak.semantica.dev.globoi.com/place/Continent'


This will retrieve all instances of ``Continent`` in the graph ``place``


Optional parameters
-------------------

.. include :: ../params/default.rst
.. include :: ../params/pages.rst
.. include :: ../params/item_count.rst
.. include :: ../params/graph_uri.rst
.. include :: ../params/class.rst
.. include :: ../params/sort.rst
.. include :: ../params/direct_instances_only.rst
.. include :: ../params/inference.rst

Special filters ?p ?o
---------------------

.. include :: ../params/po.rst


Possible responses
-------------------


**Status 200**

If there are instances that match the query, the response body is a JSON containing instances' titles, resources_id and @ids (URIs).
By default, the first page containing 10 items is returned (``?page=1&per_page=10``).

.. code-block:: json

  {
    "@context": {
        "@language": "pt"
    },
    "@id": "place:Continent",
    "_base_url": "http://brainiak.semantica.dev.globoi.com/place/Continent",
    "_class_prefix": "place",
    "_first_args": "per_page=10&page=1",
    "_next_args": "per_page=10&page=2",
    "_schema_url": "http://brainiak.semantica.dev.globoi.com/place/Continent/_schema",
    "items": [
      {
        "@id": "http://semantica.globo.com/place/Continent/Africa",
        "class_prefix": "place",
        "instance_prefix": "http://semantica.globo.com/place/Continent/",
        "resource_id": "Africa",
        "title": "\u00c1frica"
      },
      {
        "@id": "http://semantica.globo.com/place/Continent/Antarctica",
        "class_prefix": "place",
        "instance_prefix": "http://semantica.globo.com/place/Continent/",
        "resource_id": "Antarctica",
        "title": "Oceania"
      },
      {
        "@id": "http://semantica.globo.com/place/Continent/Europe",
        "class_prefix": "place",
        "instance_prefix": "http://semantica.globo.com/place/Continent/",
        "resource_id": "Europe",
        "title": "Europa"
      },
      {
        "@id": "http://semantica.globo.com/place/Continent/Asia",
        "class_prefix": "place",
        "instance_prefix": "http://semantica.globo.com/place/Continent/",
        "resource_id": "Asia",
        "title": "\u00c1sia"
      },
      {
        "@id": "http://semantica.globo.com/place/Continent/America",
        "class_prefix": "place",
        "instance_prefix": "http://semantica.globo.com/place/Continent/",
        "resource_id": "America",
        "title": "Am\u00e9rica"
      }
    ],
    "pattern": ""
  }

If there are no instances for this class, the response will contain a warning and a items list empty.

.. include :: examples/list_instance_no_results.rst

**Status 400**

If there are unknown parameters in the request query string, the response status code is 400.
A JSON containing both the wrong parameters and the accepted ones is returned.

.. code-block:: bash

  curl -s 'http://brainiak.semantica.dev.globoi.com/place/Continent?invalid_param=1'

.. code-block:: json

    {
        "errors": [
            "HTTP error: 400\nArgument invalid_param is not supported. The supported querystring arguments are: class_prefix, class_uri, direct_instances_only, do_item_count, expand_uri, graph_uri, lang, page, per_page, sort_by, sort_include_empty, sort_order."
        ]
    }

**Status 404**

If the class does not exist, the response status code is a 404.

.. include :: examples/list_instance_404.rst

**Status 500**

If there was some internal problem, the response status code is a 500.
Please, contact semantica@corp.globo.com informing the URL and the JSON returned.
