import sys
import inspect 
import requests

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

def quick_status(opt):
    return  { 'exists': cli.cmd (opt['hostname']
                , 'file.file_exists'
                , ['/etc/nginx/sites-available/{int_name}.conf' .format (**opt)]
                ) [opt['hostname']]
            , 'enabled': cli.cmd (opt['hostname']
                , 'file.file_exists'
                , ['/etc/nginx/sites-enabled/{int_name}.conf' .format (**opt)]
                ) [opt['hostname']]
            , 'running': False
            }

def status(opt):
    for i in range(3):
        try:
            print 'requesting {ext_name}...' .format (**opt)
            r = requests.get ('http://{ext_name}/resource/0/child/' .format (**opt) , timeout=20)
            resp = r.json()
            alive = True
        except Exception as e:
            alive = False
        if alive: break

    return  { 'exists': cli.cmd (opt['hostname']
                , 'file.file_exists'
                , ['/etc/nginx/sites-available/{int_name}.conf' .format (**opt)]
                ) [opt['hostname']]
            , 'enabled': cli.cmd (opt['hostname']
                , 'file.file_exists'
                , ['/etc/nginx/sites-enabled/{int_name}.conf' .format (**opt)]
                ) [opt['hostname']]
            , 'running': alive
            }

def create(opt):
    cli.cmd (opt ['hostname']
            , 'cp.get_template'
            ,   [ 'salt://resource/proxy/uwsgi.jinja'
                , '/etc/nginx/sites-available/{int_name}.conf' .format(**opt) ]
            , kwarg = opt ) [opt['hostname']]

def destroy(opt):
    cli.cmd ( opt['hostname'], 'file.remove'
            , [ '/etc/nginx/sites-available/{int_name}.conf' .format (**opt) ] )

def enable (opt):
    cli.cmd ( opt['hostname'], 'file.symlink'
            , [ '/etc/nginx/sites-available/{int_name}.conf'.format (**opt)
                , '/etc/nginx/sites-enabled/{int_name}.conf'.format (**opt)] )

def disable(opt):
    cli.cmd ( opt['hostname'], 'file.remove'
            , [ '/etc/nginx/sites-enabled/{int_name}.conf' .format (**opt) ] )

def restart (opt):
    cli.cmd (opt['hostname'], 'cmd.run', ['initctl reload machineer-nginx'])


def check_create  (opt) : return quick_status(opt) ['exists']
def check_enable  (opt) : return quick_status(opt)['enabled']
def check_start   (opt) : return status(opt)['running']
def check_destroy (opt) : return not check_create (opt)
def check_disable (opt) : return not check_enable (opt)
# def check_stop    (opt) : return not check_start  (opt)



def _wrap_simple(f): 
    def _wrap_simple_ret(obj):

        opt = {}
        try:
            opt .update (
                yaml.load ( jinja2.Template ( open(confPath) .read()) .render()
                    ) ['resources'] ['proxy'] )
        except KeyError as e: raise e
        opt .update ( **obj )
        return f(opt)
    _wrap_simple_ret.__name__ = f.__name__
    return _wrap_simple_ret


[ setattr (sys.modules[__name__], func_name, _wrap_simple (func_obj) ) for func_name, func_obj in
    inspect.getmembers(sys.modules[__name__], inspect.isfunction)
        if func_name[0:1] != '_'
]

def _wrap_check(logic, check):
    def _wrap_check_ret(opt):
        print logic
 
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
