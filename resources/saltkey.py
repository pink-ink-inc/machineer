import os
import StringIO 

import salt.config
import salt.wheel

from machineer.resources import Resource, ResourceStatus


class SaltKey(Resource):

    options = ['minion_id']


    def __init__(self, kws):
        super(type(self), self).__init__(kws) 
        self.defineMethods()
        self.wheel = salt.wheel.Wheel(self.__opts__)
        self.opt['minion_fs_path'] = os.path.join (
                self.opt['minion_fs_path_prefix'], self.opt['minion_id'], 'rootfs' )

    def status(self):
        keys = self.wheel.call_func('key.list_all')
        keys['all'] = keys['minions'] + keys['minions_pre'] + keys['minions_rejected']
        self.opt['key_state'] = [ x['label'] for x in [
                {'truth': self.opt['minion_id'] in keys['minions'], 'label': 'accepted'}
              , {'truth': self.opt['minion_id'] in keys['minions_pre'], 'label': 'pending'}
              , {'truth': self.opt['minion_id'] in keys['minions_rejected'], 'label': 'rejected'}
              , {'truth': self.opt['minion_id'] not in keys['all'], 'label': 'non-existent'}
              ] if x['truth'] ] [0]
        return ResourceStatus ( name = self.opt['minion_id']
                , isRunning = self.opt['key_state'] in ['accepted']
                , isEnabled = self.opt['key_state'] in ['accepted', 'pending']
                , exists    = self.opt['key_state'] in ['accepted', 'pending', 'rejected']
                , descr = '{minion_id} in {key_state}'.format(**self.opt)
                )

    def l_create(self):
        key = self.wheel.call_func('key.gen')
        open('/tmp/minion_conf', 'w').write (
                self.cli.cmd ( self.opt['minion_fs_hostname'], 'cmd.run'
            , [ 'cat {minion_conf}'.format ( minion_conf = os.path.join (
                  self.opt['minion_fs_path']
                , self.opt['minion_conf_path']))])[self.opt['minion_fs_hostname']])
        self.minion_config = salt.config.minion_config ('/tmp/minion_conf')
        with open ( os.path.join (
                    self.__opts__['pki_dir'], 'minions_rejected', self.opt['minion_id']
                    ), 'w') as f:
            f.write(key['pub'])
        self.cli.cmd ( self.opt['minion_fs_hostname'], 'file.write',
                [ os.path.join (
                          self.opt['minion_fs_path']
                        # , self.minion_config['pki_dir' .strip('/')]
                        , 'etc/salt/pki/minion'
                        , 'minion.pub' )
                , key['pub'] ] )
        self.cli.cmd ( self.opt['minion_fs_hostname'], 'file.write',
                [ os.path.join (
                          self.opt['minion_fs_path']
                        # , self.minion_config['pki_dir' .strip('/')]
                        , 'etc/salt/pki/minion'
                        , 'minion.pem' )
                , key['priv'] ] )
        self.cli.cmd ( self.opt['minion_fs_hostname'], 'file.set_mode'
                , [ os.path.join (
                          self.opt['minion_fs_path']
                        , self.minion_config['pki_dir'] .strip(os.path.sep)
                        , 'minion.pem' )
                , '0640' ] )

    def l_destroy(self):
        os.remove ( os.path.join (
                    self.__opts__['pki_dir'], 'minions_rejected', self.opt['minion_id'] ) )

    def l_enable(self):
        os.rename (
                  os.path.join (
                    self.__opts__['pki_dir'], 'minions_rejected', self.opt['minion_id'] )
                , os.path.join (
                    self.__opts__['pki_dir'], 'minions_pre', self.opt['minion_id'] ) )

    def l_disable(self):
        os.rename (
                  os.path.join (
                    self.__opts__['pki_dir'], 'minions_pre', self.opt['minion_id'] )
                , os.path.join (
                    self.__opts__['pki_dir'], 'minions_rejected', self.opt['minion_id'] ) )

    def l_start(self):
        os.rename (
                  os.path.join (
                    self.__opts__['pki_dir'], 'minions_pre', self.opt['minion_id'] )
                , os.path.join (
                    self.__opts__['pki_dir'], 'minions', self.opt['minion_id'] ) )

    def l_stop(self):
        os.rename (
                  os.path.join (
                    self.__opts__['pki_dir'], 'minions', self.opt['minion_id'] )
                , os.path.join (
                    self.__opts__['pki_dir'], 'minions_pre', self.opt['minion_id'] ) )


