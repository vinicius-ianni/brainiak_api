Get a Class
============

A class is where the definition of the data structure resides.

In this service, we can get a class defined in some context.

**Basic usage**


.. code-block:: bash

  $ curl -s 'http://brainiak.semantica.dev.globoi.com/place/City/_schema'

.. code-block:: json

    {
        "$schema": "http://json-schema.org/draft-04/schema#",
        "@context": {
            "@language": "pt"
        },
        "description": "Lugar perene e urbanizado onde pessoas habitam.",
        "id": "http://semantica.globo.com/place/City",
        "links": [
            {
                "href": "{+_base_url}",
                "method": "GET",
                "rel": "self"
            },
            {
                "href": "/place/City/_schema",
                "method": "GET",
                "rel": "class"
            },
            {
                "href": "/place/City?class_prefix=http://semantica.globo.com/place/",
                "method": "POST",
                "rel": "create",
                "schema": {
                    "$ref": "{+_base_url}"
                }
            }]
        "properties": {
            "http://semantica.globo.com/place/latitude": {
                "class": "http://semantica.globo.com/place/Place",
                "datatype": "http://www.w3.org/2001/XMLSchema#float",
                "description": "Coordenada de latitude de acordo com WGS84.",
                "graph": "http://semantica.globo.com/place/",
                "title": "Latitude",
                "type": "number"
            },
            "http://semantica.globo.com/place/longitude": {
                "class": "http://semantica.globo.com/place/Place",
                "datatype": "http://www.w3.org/2001/XMLSchema#float",
                "description": "Coordenada de longitude de acordo com WGS84.",
                "graph": "http://semantica.globo.com/place/",
                "title": "Longitude",
                "type": "number"
            },
        },
        "title": "Cidade",
        "type": "object"
    }


Why _schema? In our data model we have a clear distinction between class
(structure of data) and instances (the data content itself), and by using a request like
GET <context>/<class> we could not have a clear distinction whether we want
the whole collection of instances or we want the definition of this class.

Thus, the _schema suffix is used to distinguish the latter case from the former.
It also serves to inform that the class definition will be given in json-schema format.



Optional parameters
-------------------

.. include :: ../params/default.rst
.. include :: ../params/graph_uri.rst
.. include :: ../params/class.rst


Possible responses
------------------


**Status 200**


If the class exists, the response body is a JSON representing the class definition.

.. code-block:: bash

  $ curl -s 'http://brainiak.semantica.dev.globoi.com/place/Country/_schema'

.. code-block:: json

    {
        "$schema": "http://json-schema.org/draft-04/schema#",
        "@context": {
            "@language": "pt"
        },
        "description": "A relatively large and permanent settlement, particularly a large urban settlement.",
        "id": "http://semantica.globo.com/place/City",
        "links": [
            {
                "href": "{+_base_url}",
                "method": "GET",
                "rel": "self"
            },
            {
                "href": "/place/City/_schema",
                "method": "GET",
                "rel": "class"
            },
            {
                "href": "/place/City",
                "method": "POST",
                "rel": "create",
                "schema": {
                    "$ref": "{+_base_url}"
                }
            }
        ],
        "properties": {
            "http://semantica.globo.com/place/latitude": {
                "class": "http://semantica.globo.com/place/Place",
                "datatype": "http://www.w3.org/2001/XMLSchema#float",
                "description": "Coordenada de latitude de acordo com WGS84.",
                "graph": "http://semantica.globo.com/place/",
                "title": "Latitude",
                "type": "number"
            },
            "http://semantica.globo.com/place/longitude": {
                "class": "http://semantica.globo.com/place/Place",
                "datatype": "http://www.w3.org/2001/XMLSchema#float",
                "description": "Coordenada de longitude de acordo com WGS84.",
                "graph": "http://semantica.globo.com/place/",
                "title": "Longitude",
                "type": "number"
            }
        },
        "title": "City",
        "type": "object"
    }

**Status 400**


If there are unknown parameters in the request, the response is a 400
with a JSON informing the wrong parameters and the accepted ones.

.. include :: examples/get_schema_400.rst

**Status 404**

If the class does not exist, the response is a 404 with a JSON
informing the error

.. include :: examples/get_schema_404.rst
