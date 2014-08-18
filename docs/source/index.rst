.. brainiak documentation master file, created by
   sphinx-quickstart on Thu Feb  7 10:40:27 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Brainiak API documentation!
============================


Linked data offers a set of best practices for publishing, sharing and linking data and information on the web.
It is based on use of http URIs and semantic web standards such as `RDF <http://www.w3.org/RDF/>`_.

What is Linked Data? Please refer to this `great introduction video <http://www.youtube.com/watch?v=TJfrNo3Z-DU>`_, by Metaweb (acquired by Google).

For some web developers the need to understand the RDF data model and associated serializations and query language (`SPARQL <http://www.cambridgesemantics.com/semantic-university/sparql-by-example>`_) has proved a barrier to adoption of Linked Data.

This project seeks to build APIs, data formats and supporting tools to overcome this barrier.
Including, but not limited to, accessing Linked Data via a developer-friendly JSON format.

The Brainiak API provides a configurable way to access RDF data using simple RESTful URLs that are translated into queries to a SPARQL endpoint, where basic RDF manipulation, such as manipulating instances is easy with just some configuration.

Of course, SPARQL is more expressive than an API built on top of HTTP, therefore, we also support ad-hoc SPARQL queries for fast execution (see :doc:`/services/stored_query/stored_query`).

.. toctree::
   :maxdepth: 3

   concepts.rst
   tutorials.rst
   services.rst
   troubleshoot.rst

.. toctree::
   :maxdepth: 1

   releases.rst
