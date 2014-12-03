

from machineer.resources import *


class PSQL(Resource):

    methods = [ 'create', 'destroy', 'chown' ]
    options = [ 'db_name', 'db_owner' ]

    def __init__(self, kws): 
        super(type(self), self).__init__(kws)
        self.defineMethods()

    def v_create(self):
        return self.cli.cmd ( self.opt['hostname']
                , 'postgres.db_exists'
                , [self.opt['db_name']] ) [self.opt['hostname']]

    def l_create(self):
        self.cli.cmd ( self.opt['hostname'], 'postgres.db_create', [self.opt['db_name']] ) 

    def v_chown(self):
        return self.cli.cmd ( self.opt['hostname'], 'postgres.db_list', []
                ) [self.opt['hostname']] [self.opt['db_name']] ['Owner'] == self.opt['db_user']

    def l_chown(self):
        self.cli.cmd ( self.opt['hostname']
                , 'postgres.db_alter'
                , [ self.opt['db_name'] ]
                , kwarg = { 'owner': self.opt['db_user'] }
                )
        self.cli.cmd ( self.opt['hostname']
                , 'postgres.owner_to'
                , [ self.opt['db_name'], self.opt['db_user'] ]

    def l_destroy(self):
        self.cli.cmd ( self.opt['hostname'], 'postgres.db_remove', [self.opt['db_name']] ) 
