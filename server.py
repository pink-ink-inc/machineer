import types


import flask
import machineer.schemata
import json
import rq
import time
import sys
import redis


# Setings
# -------

app = flask.Flask(__name__)
app.host = '0.0.0.0'
app.debug = True
r = redis.Redis()
q = rq.Queue ( connection = r, async = False )

def _serialize(obj):
    return json.dumps ( obj
            , indent = 2
            )

# API
# ===

# System information:
# -------------------

@app.route('/api/info/version')
def _info_version():
    ret = { 'Machineer': '1.0' }
    return _serialize (ret)

@app.route('/api/info/test')
def _api_info_echo(*args, **kws):
    callme = _info_echo
    return _serialize (callme(*args, **kws))

@app.route('/api/info/schemata')
def _api_info_schemata(*args, **kws):
    callme = _info_schemata
    return _serialize (callme(*args, **kws))

@app.route('/api/info/schemata/<schema>')
def _api_info_schemata_schema(*args, **kws):
    callme = _info_schemata_schema
    return _serialize (callme(*args, **kws))

@app.route('/api/info/schemata/<schema>/<method>')
def _api_info_schemata_schema_method(*args, **kws): 
    callme = _info_schemata_schema_method
    return _serialize (callme(*args, **kws))

def _info_echo():
    return flask.request.json

def _info_schemata():
    s = machineer.schemata
    return [ o for o in dir(s) if type(getattr(s, o)) == types.DictType and o[0:1] != '_' ]

def _info_schemata_schema(schema):
    s = machineer.schemata
    return { schema: [ method.__name__ for method in dir(schema)
            if type(method) == types.FunctionType and method[0:1] != '_' ]
            for schema in _info_schemata() }

def _info_schemata_schema_method(schema, method):
    return  { 'doc': machineer.schemata.schema['method'].__doc__
            , 'opt': {}
            }

# Registry queries:
# ------------------

@app.route('/api/registry/projects')
def _api_registry_projects(*args, **kws): 
    callme = _registry_projects
    return _serialize (callme(*args, **kws))

@app.route('/api/registry/projects/<project>')
def _api_registry_projects_project(*args, **kws): 
    callme = _registry_projects_project
    return _serialize (callme(*args, **kws))

@app.route('/api/registry/projects/<project>/<instance>/status')
def _api_registry_projects_project_instance_status(*args, **kws): 
    callme = _registry_projects_project_instance_status
    return _serialize (callme(*args, **kws))

@app.route('/api/registry/projects/<project>/<instance>/brief')
def _api_registry_projects_project_instance_brief(*args, **kws): 
    callme = _registry_projects_project_instance_brief
    return _serialize (callme(*args, **kws))

@app.route('/api/registry/projects/<project>/<instance>/state')
def _api_registry_projects_project_instance_state(*args, **kws): 
    callme = _registry_projects_project_instance_state
    return _serialize (callme(*args, **kws))

def _registry_projects():
    return [ 'machineer', 'nextgisweb' ]

def _registry_projects_project(project):
    # TODO: There's no reason not to handle all registry queries inline.
    return machineer.schemata.list_(project)

def _registry_projects_project_instance_status (project, instance):
    # TODO: There's no reason not to handle all registry queries inline.
    return machineer.schemata.api [project] ['get_status'] (
                { 'param':
                    { 'InstanceID': instance
                    , 'Project': project
                    , 'InstanceClass': ''
                    , 'Master': ''
                    }
                }
            )

def _registry_projects_project_instance_brief (project, instance):
    return 'z'

def _registry_projects_project_instance_state (project, instance):
    # Locked / unlocked
    return 'z'

# Method calls:
# --------------

@app.route('/api/call/<schema>/<method>', methods = ['POST'])
def _api_call_schema_method(*args, **kws):
    global post_body
    post_body = flask.request.json
    callme = _call_schema_method
    return _serialize (callme(*args, **kws))

def _call_schema_method (schema, method):
    return  ( machineer.schemata.api [schema] [method] (post_body)
            if schema in machineer.schemata.api.keys()
            # Or a dict?
            else machineer.schemata.schema ['method'] (post_body)
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
