from tornado.web import HTTPError

from brainiak import triplestore
from brainiak.prefixes import prefix_to_slug
from brainiak.utils import sparql


# Note that pagination was done outside the query
# because we are filtering query results based on prefixes
# (accessible from the application and not through SPARQL)
QUERY_LIST_DOMAIN = """
SELECT DISTINCT ?graph
WHERE {GRAPH ?graph { ?s ?p ?o }}
"""


def split_into_chunks(items, per_page):
    chunks = [items[index: index + per_page] for index in xrange(0, len(items), per_page)]
    return chunks


def list_domains(params):
    sparql_response = triplestore.query_sparql(QUERY_LIST_DOMAIN)
    all_domains_uris = sparql.filter_values(sparql_response, "graph")

    filtered_domains = filter_and_build_domains(all_domains_uris)

    if not filtered_domains:
        raise HTTPError(404, log_message="No domains were found.")

    domains_pages = split_into_chunks(filtered_domains, int(params["per_page"]))
    domains = domains_pages[int(params["page"])]

    domains_json = build_json(domains)
    return domains_json


def filter_and_build_domains(domains_uris):
    domains = []
    for uri in domains_uris:
        slug = prefix_to_slug(uri)
        if slug != uri:
            domain_info = {
                "title": slug,
                "@id": uri,
                "resource_id": slug
            }
            domains.append(domain_info)
    return domains


def build_json(domains):
    links = {}
    json = {
        'items': domains,
        'item_count': len(domains),
        'links': links
    }
    # TODO: add pagination
    return json
