Caching
=======

Enabling cache
--------------

Cache is enabled or disabled at the ``settings.py`` of the application, through the variable ``ENABLE_CACHE``.
When this global cache configuration is enabled, cache is set (or not) for each resource of the API.
To check if cache is enabled for some resource, run:

.. code-block:: bash

  $ curl -i -X OPTIONS http://brainiak.semantica.dev.globoi.com/

  HTTP/1.1 204 No Content
  Server: nginx
  Date: Thu, 03 Jul 2014 21:00:33 GMT
  Content-Type: text/html; charset=UTF-8
  Content-Length: 0
  Connection: keep-alive
  Access-Control-Allow-Methods: GET, OPTIONS, PURGE
  Access-Control-Max-Age: 86400
  Access-Control-Allow-Origin: *
  Access-Control-Allow-Headers: Content-Type, Authorization, Backstage-Client-Id

If cache is enabled, ``PURGE`` will be shown on the response header ``Access-Control-Allow-Methods``.


Resource cache status
---------------------

It is possible to check the cache status of a certain resource by the following headers:

 * **X-Cache**: tells if there was a ``HIT`` (cached data) or ``MISS`` (fresh data) at Brainiak API
 * **Last-Modified**: date and time when the response was computed. This is specially useful when ``X-Cache`` returns ``HIT``.

Example
-------

The first time a URL is accessed, there will be no cache - so ``X-Cache``  will return ``MISS``:

.. code-block:: bash

  $ curl -i -X GET http://brainiak.semantica.dev.globoi.com/

  HTTP/1.1 200 OK
  Server: nginx
  Date: Thu, 03 Jul 2014 21:00:35 GMT
  Content-Type: application/json; profile=http://brainiak.semantica.dev.globoi.com/_schema_list
  Content-Length: 1008
  Connection: keep-alive
  X-Cache: MISS from brainiak.semantica.dev.globoi.com
  Last-Modified: Thu, 03 Jul 2014 18:00:35 -0300
  Etag: "4d53e4145ce64273c7604ad86c4cc81d5dddbb05"
  Access-Control-Allow-Origin: *

From the second time on, ``X-Cache`` will contain ``HIT`` and ``Last-Modified`` will be the same:

.. code-block:: bash

  $ curl -i -X GET http://brainiak.semantica.dev.globoi.com/

  HTTP/1.1 200 OK
  Server: nginx
  Date: Thu, 03 Jul 2014 21:00:36 GMT
  Content-Type: application/json; profile=http://brainiak.semantica.dev.globoi.com/_schema_list
  Content-Length: 1008
  Connection: keep-alive
  X-Cache: HIT from brainiak.semantica.dev.globoi.com
  Last-Modified: Thu, 03 Jul 2014 18:00:35 -0300
  Etag: "f288c34015f52392c33fd6bffd95e7bfb25c4a0a"
  Access-Control-Allow-Origin: *

Purge
-----

To cleanup cache, the ``PURGE`` method should be used.
Note that for purging purposes, query string parameters are ignored.
That means that the same instance could have been cached with different parameters,
but when purging the instance all versions should be removed from the cache disregarding the parameters that they were cached with.


For the time being, we support purging: just the root, a particular instance, the whole cache.


Purge Root
----------

Example:

.. code-block:: bash

  $ curl -i -X PURGE http://brainiak.semantica.dev.globoi.com/

  HTTP/1.1 200 OK
  Server: nginx
  Date: Thu, 03 Jul 2014 21:00:36 GMT
  Content-Type: text/html; charset=UTF-8
  Content-Length: 0
  Connection: keep-alive
  Access-Control-Allow-Origin: *

Purge Instance
--------------

There is support to PURGE a specific instance given its full path.

.. code-block:: bash

  $ curl -i -X PURGE  http://brainiak.semantica.dev.globoi.com/person/Person/IsaacNewton



Purge all (Recursive purge)
---------------------------

It is also possible to cleanup recursively, calling ``PURGE`` with the header ``X-Cache-Recursive`` set to ``1``:

.. code-block:: bash

  $ curl -i -X PURGE --header "X-Cache-Recursive: 1" http://brainiak.semantica.dev.globoi.com/

At this time, we only accept purging all cache.
In the near future, it will be accepted more granular purging, such as purge everything cached from this context, collection, and so on.
