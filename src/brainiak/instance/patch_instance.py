from tornado.web import HTTPError

from brainiak.prefixes import normalize_uri, EXPAND


MISSING_REQUIRED_PATCH_KEY = u"Incorrect patch item. Every object in the list must contain the following keys: [op, path]"
MISSING_VALUE_KEY = u"Objects in 'replace' or 'add' operations must have a 'value' entry"
UNSUPPORTED_OPERATION = u"Unsupported value in 'op': Supported operations are [add, replace, remove]"


def apply_patch(instance_data, patch_list):
    """
    Apply changes described in patch_list to the original instance_data.
    Return new dictionary containing the changes.

    For more information on patch_list: http://tools.ietf.org/html/rfc6902

    Example of usage:

    instance_data = {
        u'http://on.to/name': u'Flipper',
        'http://on.to/weight': 200.0
        u'http://on.to/age': 4
    }
    patch_list = [
        {
            u'path': u'http://on.to/age',
            u'value': 5,
            u'op': u'replace'
        },
        {
            u'path': u'http://on.to/weight',
            u'op': u'remove'
        }
    ]

    response = apply_patch(instance_data, patch_list)

    Value of response:

    reponse = {
        u'http://on.to/name': u'Flipper',
        u'http://on.to/age': 5
    }
    """
    original_data = instance_data.copy()
    patch_data = {}
    for item in patch_list:
        operation, predicate = _get_operation_and_predicate(item)
        predicate = normalize_uri(predicate, EXPAND)

        if operation == 'replace':
            value = item['value']
            patch_data[predicate] = value
        elif operation == 'remove':
            original_data.pop(predicate, None)
        elif operation == 'add':
            new_values = item['value']
            if not isinstance(new_values, list):
                new_values = [new_values]
            values = original_data.get(predicate, [])
            if not isinstance(values, list):
                values = [values]

            values.extend(new_values)
            patch_data[predicate] = sorted(list(set(values)))
        else:
            raise HTTPError(400, log_message=UNSUPPORTED_OPERATION)

    patch_data = patch_data
    changed_data = dict(original_data, **patch_data)
    return changed_data


def get_instance_data_from_patch_list(patch_list):
    instance_data = {}
    for item in patch_list:
        operation, predicate = _get_operation_and_predicate(item)
        value = _get_value(item)

        if operation in ("replace", "add"):
            instance_data[predicate] = value

    return instance_data


def _get_operation_and_predicate(item):
    try:
        operation = item['op']
        predicate = item['path']
    except KeyError:
        raise HTTPError(400, log_message=MISSING_REQUIRED_PATCH_KEY)
    return operation, predicate


def _get_value(item):
    value = item.get("value", None)
    if value is None:
        raise HTTPError(400, log_message=MISSING_VALUE_KEY)
    return value
