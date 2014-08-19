
**p**: Filters the instances that have the (**p**)redicate specified used in a triple.

**o**: Filters the instances that have the (**o**)bject specified used in a triple.

By combining ``p`` and/or ``o`` parameters you can specify a filter for instances that have
this property and/or object values. For example:

.. code-block:: http

  GET 'http://brainiak.semantica.dev.globoi.com/place/Country/?p=place:partOfContinent&o=http://semantica.globo.com/place/Continent/America'

It is also possible to set multiple ``p's`` and/or ``o's``, adding a number after them (p1, o1, p2, o2, etc).
Example:

.. code-block:: http

  GET 'http://brainiak.semantica.dev.globoi.com/place/City/?o=place:UF_RJ&p1=place:longitude&p2=place:latitude&per_page=1'

.. code-block:: json

    {
        "@context": {
            "@language": "pt"
        },
        "@id": "http://semantica.globo.com/place/City",
        "_base_url": "http://brainiak.semantica.dev.globoi.com/place/City",
        "_class_prefix": "http://semantica.globo.com/place/",
        "_first_args": "p2=place:latitude&per_page=1&p1=place:longitude&page=1&o=base:UF_RJ",
        "_next_args": "p2=place:latitude&per_page=1&p1=place:longitude&page=2&o=base:UF_RJ",
        "_schema_url": "http://brainiak.semantica.dev.globoi.com/place/City/_schema",
        "items": [
            {
                "@id": "http://semantica.globo.com/place/City/Globoland",
                "class_prefix": "http://semantica.globo.com/place/",
                "instance_prefix": "http://semantica.globo.com/place/City/",
                "p": "http://semantica.globo.com/place/partOfState",
                "place:latitude": -22.9583,
                "place:longitude": -43.4071,
                "resource_id": "673caaed-9ebb-4677-b200-0eccac65a3e5",
                "title": "Globoland"
            }
        ],
        "pattern": ""
    }

What happened where?

Querystring p/o parameters are matched using numbers.
If the number is omitted consider ``p0``.
Therefore, for parameters ``o=place:UF_RJ&p1=place:longitude&p2=place:latitude``, we have.

=======  ================  ===============
Number           P                O
=======  ================  ===============
0             -              place:UF_RJ
1         place:latitude          -
2         place:longitude         -
=======  ================  ===============

Places in blank will match everything in base.
The query above will be translated to this (simplified) query:

.. code-block:: sparql

  SELECT * {
    ?s a               place:City .
    ?s ?p0             place:UF_RJ .
    ?s place:longitude ?o1 .
    ?s place:latitude  ?o2 .
  }

By fixing a ``?o=place:UF_RJ`` without a matching ?p, for example, we set that instances of class City must have some property with value ``?o=place:UF_RJ``.
In the ontology tested, the property to be matched with this object value is ``isPartOf``, meaning that ``Globoland`` is part of state (`Unidade Federativa <http://en.wikipedia.org/wiki/States_of_Brazil>`_) ``o=place:UF_RJ``.

Fixing predicates like in ``p1=place:longitude&p2=place:latitude`` will only present instances that have this predicate, and the values for this properties will appear in the filtered collection result.
