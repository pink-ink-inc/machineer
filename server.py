import inspect
import types


import flask
import machineer.schemata
import json
import rq
import time
import sys
import redis

import machineer.generic
import machineer.registry
import machineer.schemata

# Settings
# -------

app = flask.Flask(__name__)
app.host = '0.0.0.0'
app.debug = True
r = redis.Redis()
q = rq.Queue ( connection = r, async = False )

# API
# ===

# System information:
# -------------------

@app.route('/api/info/version')
def _info_version():
    ret = { 'Machineer': '1.0' }
    return machineer.generic.serialize (ret)

@app.route('/api/info/test')
def _api_info_echo(*args, **kws):
    callme = _info_echo
    return machineer.generic.serialize (callme(*args, **kws))

@app.route('/api/info/schemata')
def _api_info_schemata(*args, **kws):
    callme = _info_schemata
    return machineer.generic.serialize (callme(*args, **kws))

@app.route('/api/info/schemata/<schema>')
def _api_info_schemata_schema(*args, **kws):
    callme = _info_schemata_schema
    return machineer.generic.serialize (callme(*args, **kws))

@app.route('/api/info/schemata/<schema>/<method>')
def _api_info_schemata_schema_method(*args, **kws): 
    callme = _info_schemata_schema_method
    return machineer.generic.serialize (callme(*args, **kws))

def _info_echo():
    return flask.request.json

def _info_schemata():
    return []

def _info_schemata_schema(schema):
    s = machineer.schemata
    return [ method for method in getattr(s, schema).keys()
        if method[0:1] != '_' and callable ( getattr (s,schema) [method] ) ]

def _info_schemata_schema_method(schema, method):
    return  { 'doc': machineer.schemata.schema['method'].__doc__
            , 'opt': {}
            }

# Registry queries:
# ------------------

@app.route('/api/registry/projects')
def _api_registry_projects(*args, **kws): 
    callme = _registry_projects
    return machineer.generic.serialize (callme(*args, **kws))

@app.route('/api/registry/projects/<project>')
def _api_registry_projects_project(project): 
    opt = machineer.generic._tree_merge ( [ _registry_projects_project_new (project)
            , { 'param': { 'Project': project } } ] )
    return ( machineer.registry.get_blueprints (opt) )
    

@app.route('/api/registry/projects/<project>/new/interface')
def _api_registry_projects_project_new_interface(*args, **kws): 
    callme = _registry_projects_project_new_interface
    return machineer.generic.serialize (callme(*args, **kws))

@app.route('/api/registry/projects/<project>/new')
def _api_registry_projects_project_new(*args, **kws): 
    callme = _registry_projects_project_new
    return machineer.generic.serialize (callme(*args, **kws))

@app.route('/api/registry/projects/<project>/instance/<instance>')
def _api_registry_projects_project_instance_instance (project, instance): 
    opt = machineer.generic._tree_merge ( [ _registry_projects_project_new (project)
            , { 'param': { 'InstanceID': instance , 'Project': project } } ] )
    return machineer.generic.serialize ( machineer.registry.read_instance_subkeys (opt) )

@app.route('/api/registry/projects/<project>/instance/<instance>/<subkey>')
def _api_registry_projects_project_instance_instance_status(project, instance, subkey): 
    opt = machineer.generic._tree_merge ( [ _registry_projects_project_new (project)
            , { 'param': { 'InstanceID': instance , 'Project': project } } ] )
    return machineer.registry.read_instance_subkey_serial (opt, subkey)


def _registry_projects():
    return [ 'machineer', 'nextgisweb' ]

def _registry_projects_project(project):
    # TODO: There's no reason not to handle all registry queries inline.
    return machineer.schemata.list_(project)

def _registry_projects_project_new(project):
    ordinal = int(time.time()) - 1423849659
    if project == 'machineer':
        return  { 'param':
                    { 'InstanceID': 'inst-{}' .format (ordinal)
                    , 'Project': project
                    , 'InstanceClass': 'trusty-01'
                    , 'Master': 'master-20'
                    }
                }
    elif project == 'nextgisweb':
        return  { 'param':
                    { 'InstanceID': 'instance-{}' .format (ordinal)
                    , 'Project': project
                    , 'InstanceClass': 'image-3-00'
                    , 'Master': 'master-20'
                    , 'Name': 'inst-{}.gis.to' .format (ordinal)
                    , 'Password': '{}{}' .format (project, ordinal)
                    }
                }

def _registry_projects_project_new_interface(project):
    ordinal = int(time.time()) - 1423849659
    if project == 'machineer':
        return  [{  'name': 'param', 'type': 'dict', 'inner':
                      [ {'name': 'InstanceID', 'type': 'string', 'inner': 'inst-{}' .format (ordinal) }
                    , { 'name': 'Project', 'type': 'string', 'inner': project }
                    , { 'name': 'InstanceClass', 'type': 'radio', 'inner': [ 'trusty-01' ] }
                    , { 'name': 'Master', 'type': 'radio', 'inner': [ 'master-20' ] } ] 
                }]
    elif project == 'nextgisweb':
        return  [{ 'name': 'param', 'type': 'dict', 'inner':
                [ { 'name': 'InstanceID', 'type': 'string', 'inner': 'instance-{}' .format (ordinal) }
                , { 'name': 'Project', 'type': 'string', 'inner': project }
        , { 'name': 'InstanceClass', 'type': 'string', 'inner': 'image-3-00' }
                    , { 'name': 'Master', 'type': 'string', 'inner': 'master-20' }
                    , { 'name': 'Name', 'type': 'radio', 'inner': [ 'inst-{}.gis.to' .format (ordinal), 'temp-{}.gis.to' .format (ordinal) ] }
                    , { 'name': 'Password', 'type': 'string', 'inner': '{}{}' .format (project, ordinal) }
                 ]   
                }]



def _registry_projects_project_instance_instance_status (project, instance):
    # TODO: There's no reason not to handle all registry queries inline.
    return machineer.registry.read_instance_subkey_serial

def _registry_projects_project_instance_instance_brief (project, instance):
    return 'z'

def _registry_projects_project_instance_instance_state (project, instance):
    # Locked / unlocked
    return 'z'

# Method calls:
# --------------

@app.route('/api/call/<schema>/<method>', methods = ['POST'])
def _api_call_schema_method(*args, **kws):
    global post_body
    post_body = flask.request.json
    callme = _call_schema_method
    return machineer.generic.serialize (callme(*args, **kws))

def _call_schema_method (schema, method):
    schemata =  { mod_name [2:] :
                    { method_name: method_obj
                        for method_name, method_obj
                        in inspect.getmembers (mod_obj, inspect.isfunction)
                        if method_name [0] != '_'
                    }
                    for mod_name, mod_obj
                    in inspect.getmembers (machineer.schemata, inspect.ismodule)
                    if mod_name[0:2] == 's_'
                }

    return  ( schemata [schema] [method] (post_body)
            if schema in schemata.keys() and method in schemata [schema] .keys()
            # Or a dict?
            else '404'
            )

# Legacy:
# --------

@app.route('/api/', methods = ['POST'])
def api_post_root(): 
        return json.dumps (
              machineer.schemata.list_ ()
            , indent = 2
            )

@app.route('/api/<glob>', methods = ['POST'])
def api_post_glob(glob):

    if glob == 'test':
        return json.dumps (
                  flask.request.json
                , indent = 2
                )

    if glob != '':
        return json.dumps (
              machineer.schemata.list_ (glob)
            , indent = 2
            ) 

@app.route('/api/methods/<c>', methods = ['POST'])
def api_post_methods(c):
    return json.dumps (
              machineer.schemata.api [c] .keys()
            , indent = 2
            )


@app.route('/api/class/<c>/<f>', methods = ['POST'])
def api_post_class(c, f):

    if c == 'test':
        return json.dumps (flask.request.json)

    if f in machineer.schemata.api [c] .keys() :
        return json.dumps (
                  machineer.schemata.api [c] [f] (flask.request.json)
                , indent = 2
                )

    flask.abort(404)


if __name__ == '__main__':
    app.run(host = app.host, debug = app.debug)
