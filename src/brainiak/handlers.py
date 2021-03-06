# -*- coding: utf-8 -*-


import sys
import traceback
from contextlib import contextmanager

import ujson as json
from urllib import unquote
from tornado.httpclient import HTTPError as HTTPClientError
from tornado.web import HTTPError, RequestHandler
from tornado_cors import CorsMixin, custom_decorator

# must be imported before other modules
from brainiak.log import get_logger

from brainiak import __version__, event_bus, triplestore, settings
from brainiak.collection.get_collection import filter_instances
from brainiak.collection.json_schema import schema as collection_schema
from brainiak.context.get_context import list_classes
from brainiak.context.json_schema import schema as context_schema
from brainiak.event_bus import NotificationFailure, notify_bus
from brainiak.greenlet_tornado import greenlet_asynchronous
from brainiak.instance.create_instance import create_instance
from brainiak.instance.delete_instance import delete_instance
from brainiak.instance.edit_instance import edit_instance, instance_exists
from brainiak.instance.get_instance import get_instance
from brainiak.instance.patch_instance import apply_patch, get_instance_data_from_patch_list
from brainiak.prefixes import normalize_all_uris_recursively, list_prefixes, SHORTEN
from brainiak.root.get_root import list_all_contexts
from brainiak.root.json_schema import schema as root_schema
from brainiak.schema import get_class as schema_resource
from brainiak.schema.get_class import SchemaNotFound
from brainiak.search.search import do_search
from brainiak.suggest.json_schema import schema as suggest_schema
from brainiak.search.json_schema import schema as search_schema
from brainiak.stored_query.collection import get_stored_queries
from brainiak.stored_query.crud import store_query, get_stored_query, delete_stored_query, validate_headers
from brainiak.stored_query.execution import execute_query
from brainiak.stored_query.json_schema import query_crud_schema
from brainiak.suggest.json_schema import SUGGEST_PARAM_SCHEMA
from brainiak.suggest.suggest import do_suggest
from brainiak.utils import cache
from brainiak.utils.cache import memoize, build_instance_key
from brainiak.utils.i18n import _
from brainiak.utils.json import validate_json_schema, get_json_request_as_dict
from brainiak.utils.links import build_schema_url_for_instance, content_type_profile, build_schema_url, build_class_url
from brainiak.utils.params import CLASS_PARAMS, InvalidParam, LIST_PARAMS, GRAPH_PARAMS, INSTANCE_PARAMS, PAGING_PARAMS, \
    DEFAULT_PARAMS, SEARCH_PARAMS, RequiredParamMissing, DefaultParamsDict, ParamDict, CLIENT_ID_HEADER
from brainiak.utils.params import QueryExecutionParamDict
from brainiak.utils.resources import check_messages_when_port_is_mentioned, LazyObject, build_resource_url
from brainiak.utils.sparql import extract_po_tuples, clean_up_reserved_attributes, InstanceError, is_rdf_type_invalid


logger = LazyObject(get_logger)

custom_decorator.wrapper = greenlet_asynchronous


class ListServiceParams(ParamDict):
    """Customize parameters for services with pagination"""
    optionals = LIST_PARAMS


@contextmanager
def safe_params(valid_params=None, body_params=None):
    try:
        yield
    except InvalidParam as ex:
        msg = _(u"Argument {0:s} is not supported.").format(ex)
        if valid_params is not None:
            params_msg = ", ".join(sorted(set(valid_params.keys() + DEFAULT_PARAMS.keys())))
            msg += _(u" The supported querystring arguments are: {0}.").format(params_msg)
        else:
            params_msg = ", ".join(sorted(DEFAULT_PARAMS.keys()))
            msg += _(u" The supported querystring arguments are: {0}.").format(params_msg)

        if body_params is not None:
            body_msg = ", ".join(body_params)
            msg += _(u" The supported body arguments are: {0}.").format(body_msg)
        raise HTTPError(400, log_message=msg)
    except RequiredParamMissing as ex:
        msg = _(u"Required parameter ({0:s}) was not given.").format(ex)
        raise HTTPError(400, log_message=unicode(msg))


class BrainiakRequestHandler(CorsMixin, RequestHandler):

    CORS_ORIGIN = '*'
    CORS_HEADERS = settings.CORS_HEADERS

    def __init__(self, *args, **kwargs):
        super(BrainiakRequestHandler, self).__init__(*args, **kwargs)

    def compute_etag(self):
        return None

    def get_cache_path(self):
        raise Exception(u"Method get_cache_path should be overwritten for caching & purging purposes")

    @greenlet_asynchronous
    def purge(self, **kargs):
        if settings.ENABLE_CACHE:

            path = self.get_cache_path()
            recursive = int(self.request.headers.get('X-Cache-Recursive', '0'))
            cache.purge_by_path(path, recursive)
        else:
            raise HTTPError(405, log_message=_("Cache is disabled (Brainaik's settings.ENABLE_CACHE is set to False)"))

    def _request_summary(self):
        return u"{0} {1} ({2})".format(
            self.request.method, self.request.host, self.request.remote_ip)

    def _handle_request_exception(self, e):
        if hasattr(e, "status_code"):  # and e.code in httplib.responses:
            status_code = e.status_code
        else:
            status_code = 500

        error_message = u"[{0}] on {1}".format(status_code, self._request_summary())

        if isinstance(e, NotificationFailure):
            message = unicode(e)
            logger.error(message)
            self.send_error(status_code, message=message)

        elif isinstance(e, HTTPClientError):
            message = _(u"Access to backend service failed.  {0:s}.").format(unicode(e))
            extra_messages = check_messages_when_port_is_mentioned(unicode(e))
            if extra_messages:
                for msg in extra_messages:
                    message += msg

            if hasattr(e, "response") and e.response is not None and \
               hasattr(e.response, "body") and e.response.body is not None:
                    message += _(u"\nResponse:\n") + unicode(str(e.response.body).decode("utf-8"))

            logger.error(message)
            self.send_error(status_code, message=message)

        elif isinstance(e, InstanceError):
            logger.error(_(u"Ontology inconsistency: {0}\n").format(error_message))
            self.send_error(status_code, message=e.message)

        elif isinstance(e, HTTPError):
            try:
                possible_list = json.loads(e.log_message)
            except (TypeError, ValueError):
                pass
            else:
                if isinstance(possible_list, list):
                    self.send_error(status_code, errors_list=possible_list)
                    return
            if e.log_message:
                error_message += u"\n  {0}".format(e.log_message)
            if status_code == 500:
                logger.error(_(u"Unknown HTTP error [{0}]:\n  {1}\n").format(e.status_code, error_message))
                self.send_error(status_code, exc_info=sys.exc_info(), message=e.log_message)
            else:
                logger.error(_(u"HTTP error: {0}\n").format(error_message))
                self.send_error(status_code, message=e.log_message)
        else:
            logger.error(_(u"Uncaught exception: {0}\n").format(error_message), exc_info=True)
            self.send_error(status_code, exc_info=sys.exc_info())

    def add_cache_headers(self, meta):
        cache_verb = meta['cache']
        cache_msg = u"{0} from {1}".format(cache_verb, self.request.host)
        self.set_header("X-Cache", cache_msg)
        self.set_header("Last-Modified", meta['last_modified'])

    def _notify_bus(self, **kwargs):
        if kwargs.get("instance_data"):
            instance_data = kwargs["instance_data"]
            clean_instance_data = clean_up_reserved_attributes(instance_data)
            kwargs["instance_data"] = clean_instance_data
        # self.query is going to be introduced by descendants classes
        # the *_uri parameters are either explicit passed to ParamDict or derived from the given arguments
        notify_bus(instance=self.query_params["instance_uri"],
                   klass=self.query_params["class_uri"],
                   graph=self.query_params["graph_uri"],
                   **kwargs)

    def write_error(self, status_code, **kwargs):
        # Tornado clear the headers in case of errors, and the CORS headers are lost, we call prepare to reset CORS
        self.prepare()

        if 'errors_list' in kwargs:
            error_json = {"errors": kwargs["errors_list"]}
        else:
            error_message = u"HTTP error: %d" % status_code
            if "message" in kwargs and kwargs.get("message") is not None:
                error_message += u"\n{0}".format(kwargs.get("message"))
            if "exc_info" in kwargs:
                etype, value, tb = kwargs.get("exc_info")
                exception_msg = u'\n'.join(traceback.format_exception(etype, value, tb))
                error_message += u"\nException:\n{0}".format(exception_msg)

            error_json = {"errors": [error_message]}

        self.finish(error_json)

    def build_resource_url(self, resource_id):
        return build_resource_url(
            self.request.protocol,
            self.request.host,
            self.request.uri,
            resource_id,
            self.request.query)

    def finalize(self, response):
        self.write(response)
        # self.finish() -- this is automagically called by greenlet_asynchronous


class RootJsonSchemaHandler(BrainiakRequestHandler):

    SUPPORTED_METHODS = list(BrainiakRequestHandler.SUPPORTED_METHODS) + ["PURGE"]

    def get_cache_path(self):
        return cache.build_key_for_root_schema()

    def get(self):
        with safe_params():
            self.query_params = ParamDict(self)

        response = memoize(
            self.query_params,
            root_schema,
            key=self.get_cache_path()
        )
        if response is None:
            raise HTTPError(404, log_message=_("Failed to retrieve json-schema"))

        self.add_cache_headers(response['meta'])
        # FIXME: handle cache policy uniformly
        self.set_header("Cache-control", "private")
        self.set_header("max-age", "0")

        self.finalize(response['body'])


class RootHandler(BrainiakRequestHandler):

    SUPPORTED_METHODS = list(BrainiakRequestHandler.SUPPORTED_METHODS) + ["PURGE"]

    @greenlet_asynchronous
    def purge(self):
        if settings.ENABLE_CACHE:
            valid_params = PAGING_PARAMS
            with safe_params(valid_params):
                self.query_params = ParamDict(self, **valid_params)
            recursive = int(self.request.headers.get('X-Cache-Recursive', '0'))
            cache.purge_root(recursive)
        else:
            raise HTTPError(405, log_message=_("Cache is disabled (Brainaik's settings.ENABLE_CACHE is set to False)"))

    @greenlet_asynchronous
    def get(self):
        valid_params = PAGING_PARAMS
        with safe_params(valid_params):
            self.query_params = ParamDict(self, **valid_params)
        response = memoize(self.query_params,
                           list_all_contexts,
                           function_arguments=self.query_params,
                           key=cache.build_key_for_root(self.query_params))
        if response is None:
            raise HTTPError(404, log_message=_("Failed to retrieve list of graphs"))

        self.add_cache_headers(response['meta'])
        self.finalize(response['body'])

    def finalize(self, response):
        # FIXME: handle cache policy uniformly
        self.set_header("Cache-control", "private")
        self.set_header("max-age", "0")

        if isinstance(response, dict):
            self.write(response)
            url_schema = build_schema_url(self.query_params, propagate_params=True)
            self.set_header("Content-Type", content_type_profile(url_schema))


class ContextJsonSchemaHandler(BrainiakRequestHandler):

    def get(self, context_name):
        with safe_params():
            self.query_params = ParamDict(self, context_name=context_name)
        self.finalize(context_schema(self.query_params))


class ContextHandler(BrainiakRequestHandler):

    @greenlet_asynchronous
    def get(self, context_name):
        valid_params = LIST_PARAMS + GRAPH_PARAMS
        with safe_params(valid_params):
            self.query_params = ParamDict(self, context_name=context_name, **valid_params)
        del context_name

        response = list_classes(self.query_params)
        if response is None:
            raise HTTPError(404, log_message=_(u"Context {0} not found").format(self.query_params['graph_uri']))

        self.finalize(response)

    def finalize(self, response):
        self.write(response)
        url_schema = build_schema_url(self.query_params, propagate_params=True)
        self.set_header("Content-Type", content_type_profile(url_schema))
        # FIXME: handle cache policy uniformly
        self.set_header("Cache-control", "private")
        self.set_header("max-age", "0")


class ClassHandler(BrainiakRequestHandler):

    SUPPORTED_METHODS = list(BrainiakRequestHandler.SUPPORTED_METHODS) + ["PURGE"]

    def __init__(self, *args, **kwargs):
        super(ClassHandler, self).__init__(*args, **kwargs)

    @greenlet_asynchronous
    def purge(self, context_name, class_name):
        if settings.ENABLE_CACHE:
            with safe_params():
                self.query_params = ParamDict(self,
                                              context_name=context_name,
                                              class_name=class_name)
            path = cache.build_key_for_class(self.query_params)
            cache.purge_by_path(path, False)
        else:
            raise HTTPError(405, log_message=_("Cache is disabled (Brainaik's settings.ENABLE_CACHE is set to False)"))

    @greenlet_asynchronous
    def get(self, context_name, class_name):
        self.request.query = unquote(self.request.query)

        with safe_params():
            self.query_params = ParamDict(self,
                                          context_name=context_name,
                                          class_name=class_name)
        del context_name
        del class_name

        try:
            response = schema_resource.get_cached_schema(self.query_params, include_meta=True)
        except schema_resource.SchemaNotFound as e:
            raise HTTPError(404, log_message=e.message)

        if self.query_params['expand_uri'] == "0":
            response = normalize_all_uris_recursively(response, mode=SHORTEN)
        self.add_cache_headers(response['meta'])
        self.finalize(response['body'])


class CollectionJsonSchemaHandler(BrainiakRequestHandler):

    @greenlet_asynchronous
    def get(self, context_name, class_name):
        query_params = ParamDict(self, context_name=context_name, class_name=class_name)
        try:
            self.finalize(collection_schema(query_params))
        except schema_resource.SchemaNotFound as e:
            raise HTTPError(404, log_message=e.message)


class CollectionHandler(BrainiakRequestHandler):

    def __init__(self, *args, **kwargs):
        super(CollectionHandler, self).__init__(*args, **kwargs)

    @greenlet_asynchronous
    def get(self, context_name, class_name):
        valid_params = LIST_PARAMS + CLASS_PARAMS + DefaultParamsDict(direct_instances_only='0')
        with safe_params(valid_params):
            self.query_params = ParamDict(self,
                                          context_name=context_name,
                                          class_name=class_name,
                                          **valid_params)
        del context_name
        del class_name

        response = filter_instances(self.query_params)

        if self.query_params['expand_uri'] == "0":
            response = normalize_all_uris_recursively(response, mode=SHORTEN)

        self.finalize(response)

    @greenlet_asynchronous
    def post(self, context_name, class_name):
        valid_params = CLASS_PARAMS
        with safe_params(valid_params):
            self.query_params = ParamDict(self,
                                          context_name=context_name,
                                          class_name=class_name,
                                          **valid_params)
        del context_name
        del class_name

        try:
            schema = schema_resource.get_cached_schema(self.query_params)
        except SchemaNotFound:
            schema = None
        if schema is None:
            class_uri = self.query_params["class_uri"]
            graph_uri = self.query_params["graph_uri"]
            raise HTTPError(404, log_message=_(u"Class {0} doesn't exist in context {1}.").format(class_uri, graph_uri))

        instance_data = get_json_request_as_dict(self.request.body)
        instance_data = normalize_all_uris_recursively(instance_data)

        try:
            (instance_uri, instance_id) = create_instance(self.query_params, instance_data)
        except InstanceError as ex:
            raise HTTPError(500, log_message=unicode(ex))

        instance_url = self.build_resource_url(instance_id)

        self.set_header("location", instance_url)
        self.set_header("X-Brainiak-Resource-URI", instance_uri)

        self.query_params["instance_uri"] = instance_uri
        self.query_params["instance_id"] = instance_id
        self.query_params["expand_object_properties"] = "1"

        instance_data = get_instance(self.query_params)

        if settings.NOTIFY_BUS:
            self._notify_bus(action="POST", instance_data=instance_data)

        self.finalize(201)

    def finalize(self, response):

        # FIXME: handle cache policy uniformly
        self.set_header("Cache-control", "private")
        self.set_header("max-age", "0")

        if response is None:
            # TODO separate filter message logic (e.g. if response is None and ("p" in self.query_params or "o" in self.query_params))
            filter_message = []
            po_tuples = extract_po_tuples(self.query_params)
            sorted_po_tuples = sorted(po_tuples, key=lambda po: po[2])
            for (p, o, index) in sorted_po_tuples:
                if not index:
                    index = ''
                if not p.startswith("?"):
                    filter_message.append(u" with p{0}=({1})".format(index, p))
                if not o.startswith("?"):
                    filter_message.append(u" with o{0}=({1})".format(index, o))
            self.query_params["filter_message"] = "".join(filter_message)
            self.query_params["page"] = int(self.query_params["page"]) + 1  # Showing real page in response
            msg = _(u"Instances of class ({class_uri}) in graph ({graph_uri}){filter_message}, language=({lang}) and in page=({page}) were not found.")

            response = {
                "warning": msg.format(**self.query_params),
                "items": []
            }
            self.write(response)
        elif isinstance(response, int):  # status code
            self.set_status(response)
        else:
            self.write(response)

        url_schema = build_schema_url(self.query_params, propagate_params=True)
        self.set_header("Content-Type", content_type_profile(url_schema))


class InstanceHandler(BrainiakRequestHandler):

    SUPPORTED_METHODS = list(BrainiakRequestHandler.SUPPORTED_METHODS) + ["PURGE"]

    def __init__(self, *args, **kwargs):
        super(InstanceHandler, self).__init__(*args, **kwargs)

    @greenlet_asynchronous
    def purge(self, context_name, class_name, instance_id):
        if settings.ENABLE_CACHE:
            optional_params = INSTANCE_PARAMS
            with safe_params(optional_params):
                self.query_params = ParamDict(self,
                                              context_name=context_name,
                                              class_name=class_name,
                                              instance_id=instance_id,
                                              **optional_params)
            path = build_instance_key(self.query_params)
            cache.purge_by_path(path, False)
        else:
            raise HTTPError(405, log_message=_("Cache is disabled (Brainaik's settings.ENABLE_CACHE is set to False)"))

    @greenlet_asynchronous
    def get(self, context_name, class_name, instance_id):
        optional_params = INSTANCE_PARAMS
        with safe_params(optional_params):
            self.query_params = ParamDict(self,
                                          context_name=context_name,
                                          class_name=class_name,
                                          instance_id=instance_id,
                                          **optional_params)

        response = memoize(self.query_params,
                           get_instance,
                           key=build_instance_key(self.query_params),
                           function_arguments=self.query_params)

        if response is None:
            error_message = u"Instance ({0}) of class ({1}) in graph ({2}) was not found.".format(
                self.query_params['instance_uri'],
                self.query_params['class_uri'],
                self.query_params['graph_uri'])
            raise HTTPError(404, log_message=error_message)

        response_meta = response['meta']
        response = response['body']

        if self.query_params["expand_uri"] == "0":
            response = normalize_all_uris_recursively(response, mode=SHORTEN)

        self.add_cache_headers(response_meta)
        self.finalize(response)

    @greenlet_asynchronous
    def patch(self, context_name, class_name, instance_id):
        valid_params = INSTANCE_PARAMS
        with safe_params(valid_params):
            self.query_params = ParamDict(self,
                                          context_name=context_name,
                                          class_name=class_name,
                                          instance_id=instance_id,
                                          **valid_params)
        del context_name
        del class_name
        del instance_id

        patch_list = get_json_request_as_dict(self.request.body)

        # Retrieve original data
        instance_data = memoize(self.query_params,
                                get_instance,
                                key=build_instance_key(self.query_params),
                                function_arguments=self.query_params)

        if instance_data is not None:
            # Editing an instance
            instance_data = instance_data['body']
            instance_data.pop('http://www.w3.org/1999/02/22-rdf-syntax-ns#type', None)

            # compute patch
            changed_data = apply_patch(instance_data, patch_list)

            # Try to put
            edit_instance(self.query_params, changed_data)
            status = 200

            # Clear cache
            cache.purge_an_instance(self.query_params['instance_uri'])

            self.finalize(status)
        else:
            # Creating a new instance from patch list
            instance_data = get_instance_data_from_patch_list(patch_list)
            instance_data = normalize_all_uris_recursively(instance_data)

            rdf_type_error = is_rdf_type_invalid(self.query_params, instance_data)
            if rdf_type_error:
                raise HTTPError(400, log_message=rdf_type_error)

            instance_uri, instance_id = create_instance(self.query_params,
                                                        instance_data,
                                                        self.query_params["instance_uri"])
            resource_url = self.request.full_url()
            status = 201
            self.set_header("location", resource_url)
            self.set_header("X-Brainiak-Resource-URI", instance_uri)

            self.finalize(status)

    @greenlet_asynchronous
    def put(self, context_name, class_name, instance_id):
        valid_params = INSTANCE_PARAMS
        with safe_params(valid_params):
            self.query_params = ParamDict(self,
                                          context_name=context_name,
                                          class_name=class_name,
                                          instance_id=instance_id,
                                          **valid_params)
        del context_name
        del class_name
        del instance_id

        instance_data = get_json_request_as_dict(self.request.body)
        instance_data = normalize_all_uris_recursively(instance_data)

        rdf_type_error = is_rdf_type_invalid(self.query_params, instance_data)
        if rdf_type_error:
            raise HTTPError(400, log_message=rdf_type_error)

        try:
            if not instance_exists(self.query_params):
                try:
                    schema = schema_resource.get_cached_schema(self.query_params)
                except SchemaNotFound:
                    schema = None
                if schema is None:
                    msg = _(u"Class {0} doesn't exist in graph {1}.")
                    raise HTTPError(404, log_message=msg.format(self.query_params["class_uri"],
                                                                self.query_params["graph_uri"]))
                instance_uri, instance_id = create_instance(self.query_params, instance_data, self.query_params["instance_uri"])
                resource_url = self.request.full_url()
                status = 201
                self.set_header("location", resource_url)
                self.set_header("X-Brainiak-Resource-URI", instance_uri)
            else:
                edit_instance(self.query_params, instance_data)
                status = 200
        except InstanceError as ex:
            raise HTTPError(400, log_message=unicode(ex))
        except SchemaNotFound as ex:
            raise HTTPError(404, log_message=unicode(ex))

        cache.purge_an_instance(self.query_params['instance_uri'])

        self.query_params["expand_object_properties"] = "1"
        instance_data = get_instance(self.query_params)

        if instance_data and settings.NOTIFY_BUS:
            self.query_params["instance_uri"] = instance_data["@id"]
            self._notify_bus(action="PUT", instance_data=instance_data)

        self.finalize(status)

    @greenlet_asynchronous
    def delete(self, context_name, class_name, instance_id):
        valid_params = INSTANCE_PARAMS
        with safe_params(valid_params):
            self.query_params = ParamDict(self,
                                          context_name=context_name,
                                          class_name=class_name,
                                          instance_id=instance_id,
                                          **valid_params)
        del context_name
        del class_name
        del instance_id

        deleted = delete_instance(self.query_params)
        if deleted:
            response = 204
            if settings.NOTIFY_BUS:
                self._notify_bus(action="DELETE")
            cache.purge_an_instance(self.query_params['instance_uri'])
        else:
            msg = _(u"Instance ({0}) of class ({1}) in graph ({2}) was not found.")
            error_message = msg.format(self.query_params["instance_uri"],
                                       self.query_params["class_uri"],
                                       self.query_params["graph_uri"])
            raise HTTPError(404, log_message=error_message)
        self.finalize(response)

    def finalize(self, response):
        # FIXME: handle uniformly cache policy
        # Meanwhile we do not have a consitent external cache handling policy
        # this avoids a client (such as chrome browser) caching a resource for ever
        self.set_header("Cache-control", "private")
        self.set_header("max-age", "0")

        if isinstance(response, dict):
            self.write(response)
            class_url = build_class_url(self.query_params)
            schema_url = build_schema_url_for_instance(self.query_params, class_url)
            header_value = content_type_profile(schema_url)
            self.set_header("Content-Type", header_value)
        elif isinstance(response, int):  # status code
            self.set_status(response)
            # A call to finalize() was removed from here! -- rodsenra 2013/04/25


class SuggestJsonSchemaHandler(BrainiakRequestHandler):

    def get(self):
        self.finalize(suggest_schema())


class SuggestHandler(BrainiakRequestHandler):

    @greenlet_asynchronous
    def post(self):
        valid_params = PAGING_PARAMS

        with safe_params(valid_params):
            self.query_params = ParamDict(self, **valid_params)

            raw_body_params = get_json_request_as_dict(self.request.body)
            body_params = normalize_all_uris_recursively(raw_body_params)
            if '@context' in body_params:
                del body_params['@context']

            validate_json_schema(body_params, SUGGEST_PARAM_SCHEMA)

        response = do_suggest(self.query_params, body_params)
        if self.query_params['expand_uri'] == "0":
            response = normalize_all_uris_recursively(response, mode=SHORTEN)
        self.finalize(response)

    def finalize(self, response):
        # FIXME: handle cache policy uniformly
        self.set_header("Cache-control", "private")
        self.set_header("max-age", "0")

        if response is None:
            msg = _("There were no search results.")
            raise HTTPError(404, log_message=msg)
        elif isinstance(response, dict):
            self.write(response)
            url_schema = build_schema_url(self.query_params, propagate_params=True)
            self.set_header("Content-Type", content_type_profile(url_schema))
        elif isinstance(response, int):  # status code
            self.set_status(response)
            # A call to finalize() was removed from here! -- rodsenra 2013/04/25


class SearchJsonSchemaHandler(BrainiakRequestHandler):

    def get(self, context_name, class_name):
        self.finalize(search_schema(context_name, class_name))


class SearchHandler(BrainiakRequestHandler):

    @greenlet_asynchronous
    def get(self, context_name, class_name):
        valid_params = SEARCH_PARAMS + PAGING_PARAMS
        with safe_params(valid_params):
            self.query_params = ParamDict(self,
                                          context_name=context_name,
                                          class_name=class_name,
                                          **valid_params)
            self.query_params.validate_required(self, valid_params)

        response = do_search(self.query_params)
        self.finalize(response)

    def finalize(self, response):
        # FIXME: handle cache policy uniformly
        self.set_header("Cache-control", "private")
        self.set_header("max-age", "0")

        self.write(response)
        url_schema = build_schema_url(self.query_params, propagate_params=True)
        self.set_header("Content-Type", content_type_profile(url_schema))


class PrefixHandler(BrainiakRequestHandler):

    @greenlet_asynchronous
    def get(self):
        valid_params = LIST_PARAMS
        with safe_params(valid_params):
            self.query_params = ParamDict(self, **valid_params)

        response = list_prefixes()
        self.finalize(response)


class HealthcheckHandler(BrainiakRequestHandler):

    def get(self):
        self.write("WORKING")


class VersionHandler(BrainiakRequestHandler):

    def get(self):
        self.write(__version__)


class VirtuosoStatusHandler(BrainiakRequestHandler):

    def get(self):
        self.write(triplestore.status())


class CacheStatusHandler(BrainiakRequestHandler):

    def get(self):
        response = cache.status_message()
        cache_keys = cache.keys("")
        if cache_keys:
            response += "<br>Cached keys:<br>"
            response += "<br>".join(cache_keys)
        else:
            response += "<br>There are no cached keys"

        self.write(response)


class EventBusStatusHandler(BrainiakRequestHandler):

    def get(self):
        self.write(event_bus.status())


class StatusHandler(BrainiakRequestHandler):

    def get(self):
        triplestore_status = triplestore.status()
        event_bus_status = event_bus.status()
        output = []
        if "SUCCEED" not in triplestore_status:
            output.append(triplestore_status)
        if "FAILED" in event_bus_status:
            output.append(event_bus_status)
        if output:
            response = "\n".join(output)
        else:
            response = _(u"WORKING")
        self.write(response)


class StoredQueryCollectionHandler(BrainiakRequestHandler):

    @greenlet_asynchronous
    def get(self):
        valid_params = PAGING_PARAMS

        with safe_params(valid_params):
            self.query_params = ParamDict(self, **valid_params)
            response = get_stored_queries(self.query_params)

        self.write(response)


class StoredQueryCRUDHandler(BrainiakRequestHandler):

    def __init__(self, *args, **kwargs):
        super(StoredQueryCRUDHandler, self).__init__(*args, **kwargs)

    @greenlet_asynchronous
    def get(self, query_id):
        stored_query = get_stored_query(query_id)
        if stored_query is not None:
            self.finalize(stored_query)
        else:
            not_found_message = _("The stored query with id '{0}' was not found").format(query_id)
            raise HTTPError(404,
                            log_message=not_found_message)

    @greenlet_asynchronous
    def put(self, query_id):
        validate_headers(self.request.headers)
        client_id = self.request.headers.get(CLIENT_ID_HEADER)
        client_id_dict = {"client_id": client_id}

        json_payload_object = get_json_request_as_dict(self.request.body)
        validate_json_schema(json_payload_object, query_crud_schema)
        json_payload_object.update(client_id_dict)

        # TODO return instance data when editing it?
        status = store_query(json_payload_object, query_id, client_id)
        self.finalize(status)

    @greenlet_asynchronous
    def delete(self, query_id):
        validate_headers(self.request.headers)
        client_id = self.request.headers.get(CLIENT_ID_HEADER)

        delete_stored_query(query_id, client_id)
        self.finalize(204)

    def finalize(self, response):
        # FIXME: handle cache policy uniformly
        self.set_header("Cache-control", "private")
        self.set_header("max-age", "0")

        if isinstance(response, dict):
            self.write(response)
            # TODO json schema navigation?
        elif isinstance(response, int):  # status code
            self.set_status(response)


class StoredQueryExecutionHandler(BrainiakRequestHandler):

    @greenlet_asynchronous
    def get(self, query_id):
        stored_query = get_stored_query(query_id)
        if stored_query is None:
            not_found_message = _("The stored query with id '{0}' was not found during execution attempt").format(query_id)
            raise HTTPError(404,
                            log_message=not_found_message)

        valid_params = PAGING_PARAMS

        with safe_params(valid_params):
            self.query_params = QueryExecutionParamDict(self)
            response = execute_query(query_id, stored_query, self.query_params)

        # return result
        return self.finalize(response)


class UnmatchedHandler(BrainiakRequestHandler):

    def default_action(self):
        raise HTTPError(404,
                        log_message=_(u"The URL ({0}) is not recognized.").format(self.request.full_url()))

    @greenlet_asynchronous
    def get(self):
        self.default_action()

    @greenlet_asynchronous
    def post(self):
        self.default_action()

    @greenlet_asynchronous
    def put(self):
        self.default_action()

    @greenlet_asynchronous
    def delete(self):
        self.default_action()

    @greenlet_asynchronous
    def patch(self):
        self.default_action()
