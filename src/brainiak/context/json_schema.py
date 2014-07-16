# -*- coding: utf-8 -*-
from brainiak.utils.links import merge_schemas, pagination_schema, append_param


def schema(query_params):
    context_name = query_params['context_name']
    href = build_href(query_params)

    base = {
        "$schema": "http://json-schema.org/draft-04/schema#",
        "title": context_name,
        "type": "object",
        "required": ["items"],
        "properties": {
            "do_item_count": {"type": "integer"},
            "item_count": {"type": "integer"},
            "@id": {"type": "string", "format": "uri"},
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["title", "@id", "resource_id"],
                    "properties": {
                        "title": {"type": "string"},
                        "@id": {"type": "string"},
                        "resource_id": {"type": "string"}
                    },
                    "links": [
                        {
                            "href": href,
                            "method": "GET",
                            "rel": "list"
                        },
                        {
                            "href": href,
                            "method": "GET",
                            "rel": "collection"
                        }
                    ]
                }
            },
        },
        "links": [
            {
                "href": "{+_base_url}",
                "method": "GET",
                "rel": "self"
            }
        ]
    }

    merge_schemas(base, pagination_schema(u'/{0}/'.format(context_name)))
    return base


def build_href(query_params):
    context_name = query_params['context_name']
    expand_uri = query_params.get('expand_uri', None)

    href = u"/{0}/{{resource_id}}?class_prefix={{class_prefix}}".format(context_name)
    if expand_uri is not None:
        href = append_param(href, 'expand_uri={0}'.format(query_params['expand_uri']))
    return href
