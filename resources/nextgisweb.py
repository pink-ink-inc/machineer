import sys
import inspect 

from machineer.resources import *


class NextGISWeb(Resource):

    methods = [ 'create', 'destroy', 'enable', 'disable', 'start', 'stop' ]

    def __init__(self, kws): 
        super(type(self), self).__init__(kws)

    def create(self):
        self.cli.cmd ( self.opt['InstanceID']
                , 'cp.get_template'
                ,   [ 'salt://resource/NextGISWeb/config.ini.jinja'
                    , self.opt['conf_file_location'] ]
                , kwarg = self.opt ) [self.opt['InstanceID']]
        self.cli.cmd ( self.opt['InstanceID']
                , 'cmd.run'
                , ['~ngw/env/bin/nextgisweb --config ~ngw/config.ini initialize_db']
                ) [self.opt['InstanceID']]

    def destroy(self):
        self.cli.cmd ( self.opt['InstanceID'], 'file.remove', [ self.opt['conf_file_location'] ] )

    def status(self):
        return  { 'name': self.opt['InstanceID']
                , 'exists': self.cli.cmd ( self.opt['InstanceID']
                    , 'file.file_exists'
                    , [ self.opt['conf_file_location'] ]
                    ) [self.opt['InstanceID']]
                , 'enabled': not self.cli.cmd ( self.opt['InstanceID']
                    , 'file.file_exists'
                    , [ self.opt['disable_switch_location'] ]) [self.opt['InstanceID']]
                , 'running': self.cli.cmd ( self.opt['InstanceID']
                    , 'cmd.run'
                    , [ 'initctl list | grep {job_name} | grep -o running' .format(**self.opt) ]
                    ) [self.opt['InstanceID']] == 'running'
                , 'description': self.cli.cmd ( self.opt['InstanceID']
                    , 'cmd.run', [ 'initctl list | grep {job_name}' .format(**self.opt) ]
                    ) [self.opt['InstanceID']]
                }

    def enable(self):
        self.cli.cmd (self.opt['InstanceID']
                , 'file.remove', [self.opt['disable_switch_location']]) [self.opt['InstanceID']]

    def start(self):
        self.cli.cmd (self.opt['InstanceID']
                , 'cmd.run', [ 'initctl start {job_name}' .format(**self.opt) ] ) [self.opt['InstanceID']]

    def disable(self):
        self.cli.cmd (self.opt['InstanceID']
                , 'file.write', [self.opt['disable_switch_location']
                    , 'Until this file is removed, upstart will not launch the service.'
                    ]) [self.opt['InstanceID']]

    def stop (self):
        self.cli.cmd (self.opt['InstanceID']
                    , 'cmd.run'
                    , [ 'initctl stop {job_name}' .format (**self.opt)
                    ]
                ) [self.opt['InstanceID']]

def _check_create  (obj) : return status(obj)()['exists']
def _check_enable  (obj) : return status(obj)()['enabled']
def _check_start   (obj) : return status(obj)()['running']
def _check_destroy (obj) : return lambda: not _check_create (obj)
def _check_disable (obj) : return lambda: not _check_enable (obj)
def _check_stop    (obj) : return lambda: not _check_start  (obj)

Export = NextGISWeb

def _closure (method_name):
    def ret(opt):
        __name__ = getattr(Export(opt), method_name).__name__
        return getattr(Export(opt), method_name)() 
    return ret

def _methods_map(): 
    [
        setattr (sys.modules[__name__]
                    , method_name
                    , _closure(method_name)
                    )
        for method_name, method_obj in inspect.getmembers(Export({}))
        if inspect.ismethod(method_obj) or inspect.isfunction(method_obj)
    ]

def _wrapper(logic, check):
    def ret(obj):
        # print ' -- Logic {l}'.format (l = logic.__name__)
        print ( ' --------- \n'
                'Entering the method wrapper.\n'
                'Logic function: {logic_name} from {logic_module}.\n'
                'Check function: {check_name} from {check_module}.\n' ) .format (
                          logic_name = logic.__name__
                        , check_name = check.__name__
                        , logic_module = logic.__module__
                        , check_module = check.__module__
                        ) 
        if not check(obj):
            print ' --- State is not desirable. Will run the logic.'
            logic()
            print ' --- Logic completed.'
            assert check(obj)
            print ' --- Desirable state reached.'
        else:
            print ' --- State is already as desired.'
    return ret


def _methods_wrap ():
    [
            # sys.stdout.write (method_name
            #     + ' -- '
            #     + str(getattr (sys.modules[__name__], method_name )) + '\n'
            #     # + ' -- '
            #     + str( getattr (sys.modules[__name__], '_check_' + method_name))
            #     + '\n' 
            #     )

            # setattr   ( sys.modules[__name__], method_name, (lambda x: wrap_method (
            #           (lambda: getattr (sys.modules[__name__], method_name) (x))
            #         , (lambda: getattr (sys.modules[__name__], '_check_' + method_name) (x)) )
            #         )
            #     )

            setattr ( sys.modules[__name__]
                    , method_name
                    , _wrapper  ( getattr (sys.modules[__name__], method_name )
                                , getattr (sys.modules[__name__], '_check_' + method_name )
                                )
                    )

            for method_name, method_obj in inspect.getmembers(sys.modules[__name__])
            if method_name in dir(sys.modules[__name__])
            and '_check_' + method_name in dir(sys.modules[__name__])
            and ( inspect.ismethod (method_obj) or inspect.isfunction (method_obj) )
            # and (  inspect.ismethod ( getattr (sys.modules[__name__], '_check_' + method_name ))
            #     or inspect.ismethod ( getattr (sys.modules[__name__], '_check_' + method_name )))
    ]

_methods_map()
_methods_wrap()

_wrapper(disable, _check_disable)({'InstanceID': 'tempora-nova-001.nextgisweb'})
