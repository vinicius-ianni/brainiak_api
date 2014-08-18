Using HTTP methods in a RESTful way
===================================

The HTTP verbs comprise a major portion of our “uniform interface” goal.
They represent the actions applied over the resources provided by the interface.

The primary or most commonly used HTTP verbs (or methods) are ``POST``, ``GET``, ``PUT``, and ``DELETE``.
These correspond to create, read, update, and delete (or CRUD) operations, respectively.
There are a number of other verbs, too, but are utilized less frequently such as ``OPTIONS``, ``HEAD`` and ``PURGE``.

Below is a table summarizing recommended return values of the primary HTTP methods in combination with the resource URIs:


+-----------------------------------+-----------------------------------------------+-------------------------------------+
|  HTTP                             | Collection                                    | Item                                |
|  Verb                             | (e.g. /place/City)                            | (e.g. /place/City/{id})             |
+===================================+===============================================+=====================================+
| ``HEAD`` HTTP header info         |                                               |                                     |
+-----------------------------------+-----------------------------------------------+-------------------------------------+
| ``GET`` retrieving resources      | 200 OK, list of cities. Use pagination,       | 200 *OK*, single city.              |
|                                   | sorting and filtering to navigate.            | 404 *Not Found* for missing {id}    |
+-----------------------------------+-----------------------------------------------+-------------------------------------+
| ``PUT`` replacing resources       | 404 *Not Found*                               | 200 *OK*.                           |
|                                   |                                               | 404 *Not Found* for missing {id}    |
+-----------------------------------+-----------------------------------------------+-------------------------------------+
| ``POST`` for creating resources   | 201 *Created*, ``Location`` header with link  | 404 *Not Found*.                    |
|                                   | to ``/place/City/{id}`` containing new ID.    |                                     |
+-----------------------------------+-----------------------------------------------+-------------------------------------+
| ``DELETE`` for deleting resources | 404 *Not Found*                               | 204 *No Content*, resource deleted. |
|                                   |                                               | 404 *Not Found*                     |
|                                   |                                               |                                     |
+-----------------------------------+-----------------------------------------------+-------------------------------------+
