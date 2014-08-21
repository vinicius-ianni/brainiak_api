from collections import OrderedDict
from ConfigParser import ConfigParser, NoSectionError

from brainiak import settings


parser = None


class ConfigParserNoSectionError(Exception):
    pass


def parse_section(filename=settings.TRIPLESTORE_CONFIG_FILEPATH, section="default"):
    global parser
    if not parser:
        _parse_file(filename)
    try:
        config_dict = dict(parser.items(section))
    except NoSectionError:
        raise ConfigParserNoSectionError(u"There is no {0} section in the file {1}".format(section, filename))
    return config_dict


def get_all_configs(filename=settings.TRIPLESTORE_CONFIG_FILEPATH):
    global parser
    if not parser:
        _parse_file()

    configs_dict = {}

    for section in parser.sections():
        section_dict = dict(parser.items(section))
        section_dict.pop("auth_mode")
        section_dict.pop("auth_password")
        configs_dict[section] = section_dict
    return configs_dict


def format_all_configs(configs_dict):
    formatted_configs = ""
    for config_name in configs_dict:
        formatted_configs += "[{0}]<br><br>".format(config_name)
        for config in OrderedDict(sorted(configs_dict[config_name].items())):
            formatted_configs += "{0} = {1}<br>".format(config, configs_dict[config_name][config])
        formatted_configs += "<br>"
    return formatted_configs


def _parse_file(filename=settings.TRIPLESTORE_CONFIG_FILEPATH):
    global parser
    parser = ConfigParser()
    parser.read(filename)
