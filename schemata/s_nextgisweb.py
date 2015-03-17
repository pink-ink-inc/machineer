'''

'''
import sys
import time
import datetime
import copy
import os

import yaml
import jinja2

import machineer.generic
import machineer.registry
import machineer.schemata.s_machineer

import machineer.resources.proxy
import machineer.resources.psql
import machineer.resources.nextgisweb

def _options (opt):
    timestamp = int (time.time())

    opt = machineer.generic._tree_merge ( [ yaml.load ( jinja2.Template (
        open (machineer.generic.conf_path) .read() ) .render() )
                  , opt ] )

    opt = machineer.generic._tree_merge ( [ opt, machineer.schemata.s_machineer._options (opt) ] )

    opt = machineer.generic._tree_merge ( [ opt,
            { 'resources':
                { 'PSQL':
                    { 'db_user': opt ['resources'] ['LXC'] ['container']
                    , 'db_pass': opt ['resources'] ['LXC'] ['container']
                    , 'db_name': opt ['resources'] ['LXC'] ['container']
                    }
                }
            }
        ] )

    opt = machineer.generic._tree_merge ( [ opt,
            { 'resources':
                { 'nextgisweb':
                    { 'db_host': opt ['resources'] ['PSQL'] ['hostname']
                    , 'db_user': opt ['resources'] ['LXC'] ['container']
                    , 'db_pass': opt ['resources'] ['LXC'] ['container']
                    , 'db_name': opt ['resources'] ['LXC'] ['container']
                    , 'InstanceID': opt ['resources'] ['LXC'] ['container']
                    , 'backup_id' : opt ['resources'] ['LXC'] ['container'] + '-' + str (timestamp)
                    , 'soul': opt ['param'] ['soul']
                    }
                }
            }
        ] )

    opt = machineer.generic._tree_merge ( [ opt,
            { 'resources':
                { 'proxy':
                    { 'int_name': opt ['resources'] ['LXC'] ['container']
                        .split ('.') [0]
                    , 'ext_name': opt ['param'] ['Name']
                    , 'project': opt ['param'] ['Project']
                    , 'instance': opt ['param'] ['InstanceID']
                    }
                }
            }
        ] )

    opt ['resources'] ['mount-data'] = copy.deepcopy (opt ['resources'] ['Mount'])

    opt = machineer.generic._tree_merge ( [ opt,
            { 'resources':
                { 'mount-data':
                    { 'device': os.path.join  ( opt ['resources'] ['Mount'] ['xfs_root']
                                              , opt ['param'] ['InstanceID']
                                              )
                    , 'mountpoint': os.path.join ( opt ['resources'] ['Mount'] ['mountpoint']
                                                 , 'data'
                                                 )
                    , 'order': 70
                    , 'options':   ','.join ( opt ['resources'] ['Mount'] ['options'] .split(',')
                                            + [ 'prjquota' ]
                                            )
                    , 'num_id': timestamp
                    }
                }
            }
        ] )

    return opt

def opt (opt):
    ret = machineer.generic._tree_merge ( [ machineer.schemata.s_machineer.opt (opt), _options (opt) ] )
    machineer.registry.write_instance_subkey (opt, 'opt', ret)
    return ret

def _resources (opt):
    return  { 'PSQL': machineer.resources.psql.PSQL ( _options (opt) ['resources'] ['PSQL'] )
            , 'mount-data': machineer.resources.mount.Mount (
                _options (opt) ['resources'] ['mount-data'] )
            }

def create (opt):
    opt = _options (opt)
    machineer.schemata.s_nextgisweb.opt (opt)
    machineer.schemata.s_machineer.create (opt)

    resources = _resources (opt)
    resources ['PSQL'] .create ()
    resources ['mount-data'] .create ()
    machineer.resources.proxy .create (opt ['resources'] ['proxy'])

    return status (opt)

def start (opt):
    opt = _options (opt)
    resources = _resources (opt)

    create (opt)
    resources ['mount-data'] .enable ()
    resources ['mount-data'] .start ()

    machineer.schemata.s_machineer .start (opt)

    n = 0
    while not machineer.resources.nextgisweb .check_start (opt ['resources'] ['nextgisweb']):
            time .sleep (1)
            n = n + 1
            if n == 60: raise Exception

    machineer.resources.nextgisweb .stop (opt ['resources'] ['nextgisweb'])
    machineer.resources.nextgisweb .destroy (opt ['resources'] ['nextgisweb'])
    machineer.resources.nextgisweb .create (opt ['resources'] ['nextgisweb'])
    machineer.resources.nextgisweb .enable (opt ['resources'] ['nextgisweb'])
    machineer.resources.nextgisweb .start (opt ['resources'] ['nextgisweb'])

    machineer.resources.proxy .create  (opt ['resources'] ['proxy'])
    machineer.resources.proxy .enable  (opt ['resources'] ['proxy'])
    machineer.resources.proxy .restart  (opt ['resources'] ['proxy'])

    machineer.registry.write_instance_subkey (opt, 'counters', [])

    return status (opt)

def status (opt):
    opt = _options (opt) 
    resources = _resources (opt)
    ret = machineer.generic._tree_merge ( [ machineer.schemata.s_machineer .status (opt)
            , { 'PSQL': resources ['PSQL'] .status() }
            , { key: getattr ( sys.modules [ 'machineer.resources.{}' .format (key) ], 'status' )
                    (opt ['resources'] [key])
                for key in [ 'nextgisweb', 'proxy' ] }
            ] )
    machineer.registry.write_instance_subkey (opt, 'status', ret)
    return ret

def disable (opt):
    opt = _options (opt)
    machineer.resources.proxy .disable (opt ['resources'] ['proxy'])
    machineer.resources.proxy .restart (opt ['resources'] ['proxy'])
    # To disable LXC or not to disable LXC ?

    return status (opt)

def destroy (opt):
    disable (opt)
    resources ['mount-data'] .stop ()
    resources ['mount-data'] .disable ()
    machineer.schemata.s_machineer .destroy (opt)
    opt = _options (opt)
    machineer.resources.proxy .destroy (opt ['resources'] ['proxy'])
    resources = _resources (opt)
    resources ['PSQL'] .destroy ()
    resources ['mount-data'] .destroy ()

    return status (opt)

def forget (opt):
    machineer.schemata.s_machineer .forget (opt)
    return True

def backup (opt):
    opt = _options (opt)
    resources = _resources (opt)
    machineer.resources.nextgisweb .backup (opt ['resources'] ['nextgisweb'] )
    machineer.registry.append_project_subkey (opt, 'souls', opt ['resources'] ['nextgisweb'] ['backup_id'])
    return opt ['resources'] ['nextgisweb'] ['backup_id']

