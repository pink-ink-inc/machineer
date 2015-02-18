import collections
import yaml
import jinja2
import json

# Vital global constants.
# -----------------------

conf_path = '/etc/machineer/machineer.conf'

# Generic functions that I will eventually librarize.
# ------------------------------------------------------------

def _tree_merge (trees): 
    def update(d, u):
        for k, v in u.iteritems():
            if isinstance(v, collections.Mapping):
                r = update(d.get(k, {}), v)
                d[k] = r
            else:
                d[k] = u[k]
        return d
    return reduce (update, trees)

def _device_mapper_path_escape (path):
    return ''.join ( [ char + char if char == '-' else char for char in list (path) ] )

def serialize(obj):
    return json.dumps ( obj
            , indent = 2
            )

def objectivize (string):
    return json.loads (string)

def options (opt):
    return _tree_merge ( [ yaml.load ( jinja2.Template (
        open (conf_path) .read() ) .render() )
                  , opt ] )

# Operations common for all schemata.
# -----------------------------------

dev = {}

