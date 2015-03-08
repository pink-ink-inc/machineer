import redis

import machineer.generic

sep = ':'

def _key (opt):
    root = '::machineer-api:api:registry'
    projects = root + ':projects'
    project = projects + ':{0[param][Project]}' .format (opt)
    properties = project + ':properties'
    instance = project + ':instance:{0[param][InstanceID]}' .format (opt)
    return  { 'root': root
            , 'projects': projects
            , 'project': project
            , 'instance': instance
            , 'properties': properties
            }

def _store (opt):
    return redis.StrictRedis ( host = opt ['schemata'] ['redis-server'] ['hostname'] )

def add_blueprint (opt):
    opt = machineer.generic.options (opt)
    store = _store (opt)
    store.sadd ( _key (opt) ['project'], machineer.generic.serialize (opt ['param']) )

def get_blueprints (opt):
    opt = machineer.generic.options (opt)
    store = _store (opt)
    return machineer.generic.serialize ( [ machineer.generic.objectivize (string)
        for string in store.smembers ( _key (opt) ['project'] ) ] )


def del_blueprint (opt):
    opt = machineer.generic.options (opt)
    store = _store (opt)
    store.srem ( _key (opt) ['project'], machineer.generic.serialize (opt ['param']) )

def write_subkey (opt, key, subkey, data):
    oprt = machineer.generic.options (opt)
    store = _store (opt)
    store.sadd (_key (opt) [key], subkey)
    store.set (sep.join ([_key (opt) [key], subkey])
            , machineer.generic.serialize (data)
            )
    del store

def append_subkey (opt, key, subkey, data):
    oprt = machineer.generic.options (opt)
    store = _store (opt)
    store.sadd (_key (opt) [key], subkey)
    store.rpush (sep.join ([_key (opt) [key], subkey]), data)
    del store

def read_subkeys (opt, key):
    opt = machineer.generic.options (opt)
    store = _store (opt)
    ret = list ( store.smembers (_key(opt) [key]) )
    del store
    return ret

def read_subkey_serial (opt, key, subkey):
    opt = machineer.generic.options (opt)
    store = _store (opt)
    ret = machineer.generic.serialize ( [ machineer.generic.objectivize ( store.get (key) )
        for key in store.keys ( sep.join ([_key (opt) [key], subkey]) ) ] )
    del store
    return ret

def lrange_subkey_serial (opt, key, subkey):
    opt = machineer.generic.options (opt)
    store = _store (opt)
    ret = machineer.generic.serialize ( [ store.lrange (key, 0, -1)
        for key in store.keys ( sep.join ([_key (opt) [key], subkey]) ) ] )
    del store
    return ret

def append_project_subkey (opt, subkey, data):
    return append_subkey (opt, 'properties', subkey, data)

def read_project_subkey_serial (opt, subkey):
    return read_subkey_serial (opt, 'properties', subkey)

def lrange_project_subkey_serial (opt, subkey):
    return lrange_subkey_serial (opt, 'properties', subkey)

def write_instance_subkey (opt, subkey, data):
    opt = machineer.generic.options (opt)
    store = _store (opt)
    store.sadd ( _key (opt) ['instance'], subkey )
    store.set ( sep.join ([_key (opt) ['instance'], subkey])
            , machineer.generic.serialize (data) )
    del store

def read_instance_subkey_serial (opt, subkey):
    opt = machineer.generic.options (opt)
    store = _store (opt)
    ret = machineer.generic.serialize ( [ machineer.generic.objectivize ( store.get (key) )
        for key in store.keys ( sep.join ([_key (opt) ['instance'], subkey]) ) ] )
    del store
    return ret

def read_instance_subkeys (opt):
    opt = machineer.generic.options (opt)
    store = _store (opt)
    ret = list ( store.smembers (_key(opt) ['instance']) )
    del store
    return ret

def destroy_instance_record (opt):
    opt = machineer.generic.options (opt)
    store = _store (opt)
    [ store.delete (key) for key in store.keys (_key(opt) ['instance'] + '*') ]
    del store

