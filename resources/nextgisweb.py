

from machineer.resources import *


class NextGISWeb(Resource):

    methods = [ 'create', 'destroy', 'enable', 'disable', 'start', 'stop' ]
    options = [ 'InstanceID'
            , 'db_host', 'db_name', 'db_user', 'db_pass' ]

    def __init__(self, kws): 
        super(type(self), self).__init__(kws)
        self.defineMethods() 
        for option in self.options:
            if option not in self.opt.keys():
                self.opt[option] = self.opt['InstanceID']

    def l_create(self):
        self.cli.cmd ( self.opt['InstanceID']
                , 'cp.get_template'
                ,   [ 'salt://resource/NextGISWeb/config.ini.jinja'
                    , self.opt['conf_file_location'] ]
                , kwarg = self.opt )

    def l_destroy(self):
        self.cli.cmd ( self.opt['InstanceID'], 'file.remove', [ self.opt['conf_file_location'] ] )

    def status(self):
        return ResourceStatus( name = self.opt['InstanceID']
                , exists = self.cli.cmd ( self.opt['InstanceID']
                    , 'file.file_exists'
                    , [ self.opt['conf_file_location'] ]
                    ) [self.opt['InstanceID']]
                , isEnabled = not self.cli.cmd ( self.opt['InstanceID']
                    , 'file.file_exists'
                    , [ self.opt['disable_switch_location'] ]) [self.opt['InstanceID']]
                , isRunning = self.cli.cmd ( self.opt['InstanceID']
                    , 'cmd.run'
                    , [ 'initctl list | grep ngw-uwsgi | grep -o running' ]
                    ) [self.opt['InstanceID']] == 'running'
                , descr = self.cli.cmd ( self.opt['InstanceID']
                    , 'cmd.run', [ 'initctl list | grep ngw-uwsgi' ] ) [self.opt['InstanceID']]
                )
    def l_enable(self):
        pass

    def l_start(self):
        pass

    def l_disable(self):
        pass

    def l_stop (self):
        pass

