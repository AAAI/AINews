#!/usr/bin/env python
import ConfigParser
import string

_ConfigDefault = {
    "database.dbms":            "mysql",
    "database.name":            "",
    "database.user":            "root",
    "database.password":        "",
    "database.host":            "127.0.0.1"
    }

def load_config(file, config={}):
    """
    returns a dictionary with key's of the form
    <section>.<option> and the values 
    """
    config = config.copy()
    cp = ConfigParser.ConfigParser()
    cp.read(file)
    for sec in cp.sections():
        name = string.lower(sec)
        for opt in cp.options(sec):
            value = string.strip(cp.get(sec, opt))
            if value == 'On':       value = True
            elif value == 'Off':    value = False
            config[name + "." + string.lower(opt)] = value
    return config


if __name__=="__main__":
    config =  load_config("config.ini", _ConfigDefault)
    print config