import sys
import inspect 

import salt.client
import yaml
import jinja2

from machineer.resources import *


__opts__ = salt.config.master_config('/etc/salt/master')
cli = salt.client.LocalClient()

def _wrap_log(f):
    def ret(*args, **kws):
        os.sys.stdout.write (
                ' -- Calling function {0[1]}'
                ' on host {0[0]}'
                ' with args following:\n' .format  (args)
                )
        os.sys.stdout.write (str(args))
        os.sys.stdout.write (str(kws))
        s = f (*args, **kws)
        os.sys.stdout.write ('\n' 'Output:' '\n')
        os.sys.stdout.write(str(s) if s else 'No output.')
        os.sys.stdout.write('\n')
        return s
    return ret
cli.cmd = _wrap_log ( cli.cmd )


methods = [ 'create', 'destroy', 'enable', 'disable', 'start', 'stop' ]

def create(opt):

    cli.cmd ( opt['InstanceID']
            , 'cp.get_template'
            ,   [ 'salt://resource/NextGISWeb/config.ini.jinja'
                , opt['conf_file_location'] ]
            , kwarg = opt ) [opt['InstanceID']]
    cli.cmd ( opt ['InstanceID']
            , 'file.chown'
            , [ opt['conf_file_location'], 'ngw', 'ngw']
            )
    cli.cmd ( opt['InstanceID']
            , 'cmd.run'
            , ['~ngw/env/bin/nextgisweb --config ~ngw/config.ini initialize_db']
            ) [opt['InstanceID']]

def destroy(opt):
    cli.cmd ( opt['InstanceID'], 'file.remove', [ opt['conf_file_location'] ] )

def status(opt):
    var = { '_exists': cli.cmd ( opt['InstanceID']
                , 'file.file_exists'
                , [ opt['conf_file_location'] ]
                )
          , '_disabled': cli.cmd ( opt['InstanceID']
                , 'file.file_exists'
                , [ opt['disable_switch_location'] ])
          , '_running': cli.cmd ( opt['InstanceID']
                , 'cmd.run'
                , [ 'initctl list | grep {job_name} | grep -o running' .format(**opt) ]
                )
          , '_description': cli.cmd ( opt['InstanceID']
                , 'cmd.run', [ 'initctl list | grep {job_name}' .format(**opt) ]
                )
          }

    print var
    var = { key: var [key] [ opt ['InstanceID'] ] if opt ['InstanceID'] in var [key] .keys() else None
            for key in var .keys() }


    return  { 'name': opt ['InstanceID']
            , 'exists': var ['_exists']
            , 'enabled': None if var ['_disabled'] == None else not var ['_disabled']
            , 'running': var ['_running']
            , 'description': var ['_description']
            }

def enable(opt):
    cli.cmd (opt['InstanceID']
            , 'file.remove', [opt['disable_switch_location']]) [opt['InstanceID']]

def start(opt):
    cli.cmd (opt['InstanceID']
            , 'cmd.run', [ 'initctl start {job_name}' .format(**opt) ] ) [opt['InstanceID']]

def disable(opt):
    cli.cmd (opt['InstanceID']
            , 'file.touch', [opt['disable_switch_location'] ]) [opt['InstanceID']]

def stop (opt):
    cli.cmd (opt['InstanceID']
                , 'cmd.run'
                , [ 'initctl stop {job_name}' .format (**opt)
                ]
            ) [opt['InstanceID']]

def check_create  (opt) : return status (opt) ['exists']
def check_enable  (opt) : return status (opt) ['enabled']
def check_start   (opt) : return status (opt) ['running']
def check_destroy (opt) : return not check_create (opt)
def check_disable (opt) : return not check_enable (opt)
def check_stop    (opt) : return not check_start  (opt)



def _wrap_simple(f): 
    def _wrap_simple_ret(obj):
        opt = {}
        try:
            opt .update (
                yaml.load ( jinja2.Template ( open(confPath) .read()) .render()
                    ) ['resources'] ['nextgisweb'] )
        except KeyError: pass
        opt .update ( **obj )
        return f(opt)
    return _wrap_simple_ret


[ setattr (sys.modules[__name__], func_name, _wrap_simple (func_obj) ) for func_name, func_obj in
    inspect.getmembers(sys.modules[__name__], inspect.isfunction)
        if func_name[0:1] != '_'
]

def _wrap_check(logic, check):
    def _wrap_check_ret(opt):
        print logic
        print check
 
        print ( ' --------- \n'
                'Entering the method wrapper.\n'
                'Logic function: {logic_name} from {logic_module}.\n'
                'Check function: {check_name} from {check_module}.\n' ) .format (
                  logic_name = logic.__name__
                , check_name = check.__name__
                , logic_module = logic.__module__
                , check_module = check.__module__
                )

        if not check(opt):
            print ' --- State is not desirable. Will run the logic.'
            logic(opt)
            print ' --- Logic completed.'
            assert check(opt)
            print ' --- Desirable state reached.'
        else:
            print ' --- State is already as desired.'
    return _wrap_check_ret


def _methods_wrap ():
    [
            setattr ( sys.modules[__name__]
                    , method_name
                    , _wrap_check  ( getattr (sys.modules[__name__], method_name )
                                , getattr (sys.modules[__name__], 'check_' + method_name )
                                )
                    )
 
            for method_name, method_obj in inspect.getmembers(sys.modules[__name__])
            if method_name in dir(sys.modules[__name__])
            and 'check_' + method_name in dir(sys.modules[__name__])
    ]

_methods_wrap()
