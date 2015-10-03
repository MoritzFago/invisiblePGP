#!/usr/bin/env python
#
# Usage example:
# 
# from configloader import Configuration
# Configuration.default = {
#     'number': 1,
#     'string': 'text',
#     'key': {
#         'list': [],
#     }
# }
# 
# Configuration.load("config.json") 
#
# Access via:
# Configuration['number'] 
# Configuration['key.list']
#
# DON'T FORGET TO ADD THE CONFIG FILE TO YOUR .gitignore



import os, os.path
import json

class ItemMeta(type):
    def __getitem__(cls, key):
        return cls.get(key)
    
    def __setitem__(cls, key, value):
        cls.set(key, value)

class Configuration(object):
    __metaclass__ = ItemMeta
    default = {}
    Delimiter = "."
    
    @classmethod
    def _needsUpdate(cls, data, default):
        if data.keys() != default.keys():
            return True
        for key in data:
            if isinstance(data[key], dict):
                if cls._needsUpdate(data[key], default[key]):
                    return True
        return False
    
    @classmethod
    def merge(cls, data, default, override = False):
        for key in default:
            if isinstance(default[key], dict):
                if key not in data:
                    data[key] = default[key]
                else:
                    cls.merge(data[key], default[key])
            elif key not in data or override:
                data[key] = default[key]
    
    @classmethod
    def load(cls, file, autosave = False, relative = True):
        cls.data = {}
        cls.file = os.path.join(os.path.dirname(__file__), file)
        cls.autosave = autosave
        if not os.path.exists(cls.file):
            cls.data.update(cls.default)
        with open(file, "r") as f:
            cls.data = json.load(f)
        if cls._needsUpdate(cls.data, cls.default):
            cls.merge(cls.data, cls.default)
            cls.save()
    
    @classmethod
    def save(cls, data = None):
        if data is None:
            data = cls.data
        with open(cls.file, "w") as f:
            json.dump(data, f,  sort_keys=True, indent=2, separators=(',', ': '))
    
    @classmethod
    def keys(cls):
        return cls.data.keys()
    
    @classmethod
    def __iter__(cls):
        for entry in cls.data:
            yield entry
    
    @classmethod
    def get(cls, key):
        parts = key.split(cls.Delimiter)
        elem = cls.data
        for part in parts:
            elem = elem[part]
        return elem
    
    @classmethod
    def set(cls, key, value):
        parts = key.split(cls.Delimiter)
        key = parts.pop()
        elem = cls.data
        for part in parts:
            if part not in elem:
                elem[part] = {}
            elem = elem[part]
        elem[key] = value
        if cls.autosave:
            cls.save(cls.data)

