'''

'''
import sys
import time

import yaml
import jinja2

import machineer.generic
import machineer.schemata.s_machineer

import machineer.resources.proxy
import machineer.resources.psql
import machineer.resources.nextgisweb

def _options (opt):
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
                    }
                }
            }
        ] )

    return opt

def opt (opt):
    return machineer.generic._tree_merge ( [ machineer.schemata.s_machineer.opt (opt), _options (opt) ] )

def _resources (opt):
    return  { 'PSQL': machineer.resources.psql.PSQL ( _options (opt) ['resources'] ['PSQL'] )
            }

def create (opt):
    opt = _options (opt)
    machineer.schemata.s_machineer.create (opt)

    resources = _resources (opt)
    resources ['PSQL'] .create ()
    machineer.resources.proxy .create (opt ['resources'] ['proxy'])

    return status (opt)

def start (opt):
    opt = _options (opt)
    resources = _resources (opt)

    create (opt)

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

    return status (opt)

def status (opt):
    opt = _options (opt) 
    resources = _resources (opt)
    return machineer.generic._tree_merge ( [ machineer.schemata.s_machineer .status (opt)
            , { 'PSQL': resources ['PSQL'] .status() }
            , { key: getattr ( sys.modules [ 'machineer.resources.{}' .format (key) ], 'status' )
                    (opt ['resources'] [key])
                for key in [ 'nextgisweb', 'proxy' ] }
            ] )

def disable (opt):
    opt = _options (opt)
    machineer.resources.proxy .disable (opt ['resources'] ['proxy'])
    machineer.resources.proxy .restart (opt ['resources'] ['proxy'])
    # To disable LXC or not to disable LXC ?

    return status (opt)

def destroy (opt):
    disable (opt)
    machineer.schemata.s_machineer .destroy (opt)
    opt = _options (opt)
    machineer.resources.proxy .destroy (opt ['resources'] ['proxy'])
    resources = _resources (opt)
    resources ['PSQL'] .destroy ()

    return status (opt)

