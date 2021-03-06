# -*- coding: utf-8 -*-
from copy import copy
import re
from urllib import urlencode
from urlparse import unquote, parse_qs
from contextlib import contextmanager

from tornado.web import HTTPError

from brainiak import settings
from brainiak.prefixes import expand_uri, safe_slug_to_prefix, extract_prefix, _MAP_PREFIX_TO_SLUG
from brainiak.utils.i18n import _
from brainiak.utils.sparql import PATTERN_O, PATTERN_P, find_graph_from_class, find_graph_and_class_from_instance
from brainiak.utils.config_parser import ConfigParserNoSectionError, parse_section


CLIENT_ID_HEADER = "X-Brainiak-Client-Id"


class InvalidParam(Exception):
    pass


class RequiredParamMissing(Exception):
    pass


class DefaultParamsDict(dict):

    def __init__(self, **kw):
        dict.__init__(self, **kw)
        self.required = []

    def set_required(self, required):
        self.required = list(set(required))

    def __add__(self, other):
        new_dict = DefaultParamsDict()
        new_dict.update(self)
        new_dict.update(other)
        new_dict.set_required(self.required + other.required)
        return new_dict


class RequiredParamsDict(DefaultParamsDict):
    "Class used to easily mark required parameters"
    def __init__(self, **kw):
        DefaultParamsDict.__init__(self, **kw)
        self.set_required(kw.keys())


def optionals(*args):
    """Build an instance of DefaultParamsDict from a list of parameter names"""
    result = {key: None for key in args}
    return DefaultParamsDict(**result)

# The parameters below as given to ParamDict with other keyword arguments,
# but they are not URL arguments because they are part of the URL path

EXPAND_URI = optionals('expand_uri')

DEFAULT_PARAMS = optionals('lang', 'graph_uri', 'expand_uri')

NON_ARGUMENT_PARAMS = ('context_name', 'class_name', 'instance_id')

PAGING_PARAMS = DefaultParamsDict(page=settings.DEFAULT_PAGE,
                                  per_page=settings.DEFAULT_PER_PAGE,
                                  do_item_count="0")

LIST_PARAMS = PAGING_PARAMS + DefaultParamsDict(sort_by="",
                                                sort_order="ASC",
                                                sort_include_empty="1")

INSTANCE_PARAMS = optionals('graph_uri', 'class_prefix', 'class_uri', 'instance_prefix', 'instance_uri', 'expand_object_properties', 'meta_properties')

CLASS_PARAMS = optionals('graph_uri', 'class_prefix', 'class_uri')

GRAPH_PARAMS = optionals('graph_uri')

SEARCH_PARAMS = RequiredParamsDict(pattern="", graph_uri="", class_uri="")


def normalize_last_slash(url):
    return url if url.endswith("/") else url + "/"


# Define possible params and their processing order
VALID_PARAMS = [
    'lang',
    'expand_uri',
    'graph_uri',
    'context_name', 'class_name', 'class_prefix', 'class_uri',
    'instance_id', 'instance_prefix', 'instance_uri',
    'page', 'per_page',
    'sort_by', 'sort_order', 'sort_include_empty',
    'do_item_count',
    'direct_instances_only',
    'expand_object_properties',
    'meta_properties',
    'pattern',
    'valid_patterns'
]

VALID_PATTERNS = (
    PATTERN_P,
    PATTERN_O
)


@contextmanager
def safe_split():
    try:
        yield
    except IndexError:
        pass


class ParamDict(dict):
    "Utility class to generate default params on demand and memoize results"

    def __init__(self, handler, **kw):
        dict.__init__(self)
        self.handler = handler
        # preserve the order below, defaults are overriden first
        request = self.request = handler.request

        # auxiliary dictionary to propagate parameters across functions
        self._aux_parameters = {}

        self.triplestore_config = None
        self._set_triplestore_config(request)

        self.arguments = self._make_arguments_dict(handler)

        # preserve the specified optional parameters
        self.optionals = copy(kw)
        protocol = request.headers.get("X-Forwarded-Proto", "http")
        self.base_url = "{0}://{1}{2}".format(protocol, request.host, normalize_last_slash(request.path))
        self.resource_url = self.base_url + "{resource_id}"

        # Set params with value None first, just to mark them as valid parameters
        for key in [k for k, v in self.optionals.items() if v is None]:
            dict.__setitem__(self, key, None)

        self._set_defaults()

        # Update optionals in the appropriate order
        # Overriding default values if the override value is not None
        for key in VALID_PARAMS:
            if key in self.optionals:
                value = self.optionals[key]
                if value is not None:
                    # the value None is used as a flag to avoid override the default value
                    self[key] = self.optionals[key]
                del kw[key]  # I have consumed this item, remove it to check for invalid params

        unprocessed_keys = kw.keys()
        for key in unprocessed_keys:
            if self._matches_dynamic_pattern(key):
                value = self.optionals[key]
                if value is not None:
                    # the value None is used as a flag to avoid override the default value
                    self[key] = self.optionals[key]
                del kw[key]

        if kw:
            raise InvalidParam(kw.popitem()[0])

        # Override params with arguments passed in the handler's request object
        self._override_with(handler)
        self._post_override()

    def _make_arguments_dict(self, handler):
        query_string = unquote(self.request.query)
        query_dict = parse_qs(query_string, keep_blank_values=True)
        return {key: handler.get_argument(key) for key in query_dict}

    def _set_triplestore_config(self, request):
        auth_client_id = request.headers.get(CLIENT_ID_HEADER, 'default')
        try:
            self.triplestore_config = parse_section(section=auth_client_id)
        except ConfigParserNoSectionError:
            raise HTTPError(404, _(u"Client-Id provided at '{0}' ({1}) is not known").format(CLIENT_ID_HEADER, auth_client_id))

    def __setitem__(self, key, value):
        """Process collateral effects in params that are related.
        Changes in *_prefix should reflect in *_uri.
        """
        def _key_is_undefined(key):
            try:
                value = dict.__getitem__(self, key)
                return not value or value == '_'
            except KeyError:
                return True

        if key == 'graph_uri':
            graph_uri_value = safe_slug_to_prefix(value)
            dict.__setitem__(self, key, graph_uri_value)
            with safe_split():
                if graph_uri_value and _key_is_undefined('context_name'):
                    # FIXME: the code below should disappear after #10602 - Normalização no tratamento de parâmetros no Brainiak
                    context_name_value = _MAP_PREFIX_TO_SLUG.get(graph_uri_value, '_')
                    dict.__setitem__(self, 'context_name', context_name_value)

        elif key == 'class_uri':
            class_uri_value = expand_uri(value)
            dict.__setitem__(self, key, class_uri_value)
            with safe_split():
                # FIXME: the code below should disappear after #10602 - Normalização no tratamento de parâmetros no Brainiak
                if class_uri_value and _key_is_undefined('class_name'):
                    class_name_value = class_uri_value.split("/")[-1]
                    dict.__setitem__(self, 'class_name', class_name_value)

                # FIXME: the code below should disappear after #10602 - Normalização no tratamento de parâmetros no Brainiak
                # class_prefix must be set when class_uri is defined, because it is used by json-schema logic.
                if class_uri_value:
                    class_prefix_value = "/".join(class_uri_value.split("/")[:-1]) + "/"
                    dict.__setitem__(self, 'class_prefix', class_prefix_value)

        elif key == "context_name":
            dict.__setitem__(self, key, value)
            uri = safe_slug_to_prefix(value)
            dict.__setitem__(self, "graph_uri", uri)
            dict.__setitem__(self, "class_prefix", uri)

        elif key == "class_name":
            dict.__setitem__(self, key, value)
            class_prefix = self["class_prefix"]
            if not class_prefix.endswith('/'):
                class_prefix += "/"
            dict.__setitem__(self, "class_uri", "{0}{1}".format(class_prefix, self["class_name"]))

        elif key == "instance_id":
            dict.__setitem__(self, key, value)
            dict.__setitem__(self, "instance_uri", u"{0}{1}/{2}".format(self["class_prefix"], self["class_name"], self["instance_id"]))
            dict.__setitem__(self, "instance_prefix", extract_prefix(self["instance_uri"]))

        elif key == "class_prefix":
            dict.__setitem__(self, key, safe_slug_to_prefix(value))
            dict.__setitem__(self, "class_uri", u"{0}{1}".format(self["class_prefix"], self["class_name"]))

        elif key == "instance_prefix":
            dict.__setitem__(self, key, safe_slug_to_prefix(value))
            dict.__setitem__(self, "instance_uri", u"{0}{1}".format(self["instance_prefix"], self["instance_id"]))

        elif key == "instance_uri":
            dict.__setitem__(self, key, value)
            dict.__setitem__(self, "instance_prefix", extract_prefix(value))

        else:
            dict.__setitem__(self, key, value)

    def _set_if_optional(self, key, value):
        if (key in self.optionals) and (value is not None):
            self[key] = value

    def _set_defaults(self):
        """Define a set of predefined keys"""
        self["lang"] = self.optionals.get("lang", settings.DEFAULT_LANG)

        self._set_if_optional("context_name", self.optionals.get("context_name", "invalid_context"))
        self._set_if_optional("class_name", self.optionals.get("class_name", "invalid_class"))
        self._set_if_optional("instance_id", self.optionals.get("instance_id", "invalid_instance"))

        self["expand_uri"] = self.optionals.get("expand_uri", settings.DEFAULT_URI_EXPANSION)

        # if the context name is defined, the graph_uri should follow it by default, but it can be overriden
        if "context_name" in self:
            self["graph_uri"] = safe_slug_to_prefix(self.optionals["context_name"])

        self._set_if_optional("class_prefix", self.optionals.get("graph_uri", ''))

        class_uri = self.optionals.get("class_uri")
        if class_uri is not None:
            self._set_if_optional("instance_prefix", class_uri + "/")

    def _matches_dynamic_pattern(self, key, valid_patterns=VALID_PATTERNS):
        return any([pattern.match(key) for pattern in valid_patterns])

    def _override_with(self, handler):
        "Override this dictionary with values whose keys are present in the request"
        # order is critical below because *_uri should be set before *_prefix
        for key in self.arguments:
            if (key not in self) and (not self._matches_dynamic_pattern(key)):
                raise InvalidParam(key)

            value = self.arguments.get(key, None)
            if value is not None:
                try:
                    self[key] = expand_uri(value)
                except KeyError as ex:
                    raise RequiredParamMissing(unicode(ex))

    def _post_override(self):
        "This method is called after override_with()  to do any post processing"
        if self.get("lang", '') == "undefined":
            self["lang"] = ""  # empty string is False -> lang not set

        # In order to keep up with Repos, pages numbering start at 1.
        # As for Virtuoso pages start at 0, we convert page, if provided
        if "page" in self.arguments:
            self["page"] = unicode(int(self["page"]) - 1)

        if "sort_order" in self.arguments:
            self["sort_order"] = self["sort_order"].upper()

        # expand underscores in path variables from _uri given params
        if self.get("instance_uri", '_') != '_' and (self.get("graph_uri") == '_' or self.get("class_uri") == '_/_'):
            candidate_graph_uri, candidate_class_uri = find_graph_and_class_from_instance(self["instance_uri"])
            if candidate_graph_uri and candidate_class_uri:
                self["graph_uri"] = candidate_graph_uri
                self["class_uri"] = candidate_class_uri

        elif self.get("class_uri", '_') != '_' and self.get("graph_uri") == '_':
            candidate_graph_uri = find_graph_from_class(self["class_uri"])
            if candidate_graph_uri:
                self["graph_uri"] = candidate_graph_uri

    def to_string(self):
        "Return all parameters as param_name=param_value separated by &"
        excluded_keys = ('class_name', 'class_prefix', 'context_name', 'instance_prefix', 'instance_id', 'graph_uri', 'class_uri')
        result = u"&".join([u"{0}={1}".format(k, v) for k, v in sorted(self.items()) if (k not in excluded_keys) and (v is not None)])
        return result

    def format_url_params(self, exclude_keys=None, **kw):
        if exclude_keys is None:
            exclude_keys = NON_ARGUMENT_PARAMS
        else:
            exclude_keys.extend(NON_ARGUMENT_PARAMS)

        effective_args = {}
        for key in VALID_PARAMS:
            if key in self.arguments and key not in exclude_keys:
                value = self[key]
                if value:
                    effective_args[key] = value

        effective_args.update(kw)
        return urlencode(effective_args, doseq=True)

    def validate_required(self, handler, required_spec):
        "Check if all required params specified by required_spec are indeed present in the request"
        arguments = self._make_arguments_dict(handler).keys()
        for required_param in required_spec.required:
            if required_param not in arguments:
                raise RequiredParamMissing(required_param)

    def set_aux_param(self, key, value):
        self._aux_parameters[key] = value

    def get_aux_param(self, key):
        return self._aux_parameters[key]


class QueryExecutionParamDict(ParamDict):

    def __init__(self, handler, **kw):
        self.valid_patterns = [re.compile(".*")]
        super(QueryExecutionParamDict, self).__init__(handler, **kw)

    def _matches_dynamic_pattern(self, key):
        valid_patterns = self.valid_patterns
        return super(QueryExecutionParamDict, self)._matches_dynamic_pattern(key, valid_patterns=valid_patterns)
