import inspect
import sys

from machineer.resources import *


class PSQL(Resource):

    def __init__(self, kws): 
        super(type(self), self).__init__(kws)
        self.methods = [ 'create', 'destroy' ]

        self.defineMethods()

    def v_create(self):
        return self.cli.cmd  ( self.opt['hostname']
                , 'postgres.db_exists'
                , [self.opt['db_name']]
                ) [self.opt['hostname']]

    def l_create(self):
        self.cli.cmd ( self.opt['hostname'], 'postgres.db_create', [self.opt['db_name']] ) 
        self.cli.cmd ( self.opt['hostname'], 'postgres.user_create', [ self.opt['db_user'] ]
                , kwarg = { 'user': self.opt['db_user'], 'password': self.opt['db_password'] } )
        self.cli.cmd ( self.opt['hostname']
                , 'postgres.db_alter'
                , [ self.opt['db_name'] ]
                , kwarg = { 'owner': self.opt['db_user'] }
                )
        self.cli.cmd ( self.opt['hostname']
                , 'postgres.owner_to'
                , [ self.opt['db_name'], self.opt['db_user'] ]
                )

    def l_destroy(self):
        self.cli.cmd ( self.opt['hostname'], 'postgres.db_remove', [self.opt['db_name']] ) 

    def status(self):
        s = self.v_create()
        return ResourceStatus (
              exists = s
            , isRunning = s
            , isEnabled = s
            , descr = 'Host {hostname}: {db_name} for {db_user}.' .format(**self.opt)
            )

Export = PSQL 


def _closure (method_name):
    def ret(opt):
        return getattr(Export(opt), method_name) 
    return ret

def methods_map(): 
    [
        setattr (sys.modules[__name__]
                    , method_name
                    , _closure(method_name)
                    )
        for method_name, method_obj in inspect.getmembers(Export({}))
        if inspect.ismethod(method_obj) or inspect.isfunction(method_obj)
    ]
methods_map()
