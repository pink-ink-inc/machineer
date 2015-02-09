import os
import collections
import re
import copy

from machineer.resources import *


class LXC(Resource):

    RawStatus = collections.namedtuple(
              'RawStatus'
            , ['name', 'state', 'ipv4', 'ipv6', 'autostart']
            )

    options = [ 'container' ]

    def _getRawStatusList(self):
        return [ self.RawStatus(* re.split('  +', line.strip())) for line in self.cli.cmd(
                  self.opt['hostname']
                , 'cmd.run'
                , ['lxc-ls --fancy']
                ) [self.opt['hostname']] .splitlines() [2:] ]

    @staticmethod
    def _resolveRawStatus(rawStatus):
        iplist = sum( [ line.split(', ') if line != '-' else [] # A tiny functional exercise.
                    for line in [rawStatus.ipv4, rawStatus.ipv6] ] , [ ] )
        return ResourceStatus(
              name = rawStatus.name
            , exists = True # Presumably.
                            # A rawStatus can only be generated from an existing instance.
            , isEnabled = rawStatus.autostart[0:3] == 'YES'
            , isRunning = rawStatus.state == 'RUNNING'
            , descr = ', '.join(iplist)
            )

    def _mkName(self):
        return "{container}".format(**self.opt)

    # def _path(self):
    #     return os.path.join(conf.get('master','lxcPath'), self._name())

    # def _config(self):
    #     return os.path.join(conf.get('master','lxcPath'), self._name(), 'config')


    # def __init__(self, kws):
    #     super(type(self), self).__init__(kws)
    #     self.opt.update(kws)
        # try: self.opt['container'] = "{ClusterName}-{InstanceID}".format(**self.opt)
        # except KeyError: pass

    def __init__(self, kws):
        super(type(self), self).__init__(kws)
        self.defineMethods()

    # def test(self):
    #     tgt = conf.get('master','hostname').encode('ascii')
    #     return self.cli.cmd(tgt, 'cmd.run', ['ls /'])

    def status(self):
        matches = [ x for x in self._getRawStatusList()
                if x.name == self._mkName() ]
        if len(matches) == 0: return ResourceStatus()
        else: return self._resolveRawStatus(matches[0])

    def list(self):
        return [ self._resolveRawStatus(x) for x in self._getRawStatusList() ]

    def l_create(self):
            self.cli.cmd ( self.opt['hostname'], 'file.mkdir'
                    , [ os.path.join (self.opt['root'], self._mkName()) ] )
            self.cli.cmd ( self.opt['hostname'], 'file.mkdir'
                    , [ os.path.join (self.opt['root'], self._mkName(), 'rootfs') ] )
            self.cli.cmd ( self.opt['hostname'], 'cp.get_template'
                    ,   [ 'salt://resource/LXC/config.jinja'
                        , os.path.join(self.opt['root'], self._mkName(), 'config') ]
                    , kwarg = self.opt )
            self.cli.cmd ( self.opt['hostname'], 'cmd.run',
                    [ 'echo {t} > {f}'.format (
                          f = os.path.join (
                              self.opt['root']
                            , self._mkName()
                            , 'rootfs', 'etc', 'hostname' )
                        , t = self._mkName() ) ] )

    def l_destroy(self):
        self.cli.cmd ( self.opt['hostname'] , 'file.rmdir'
                , [ os.path.join (self.opt['root'], self._mkName(), 'rootfs') ] )
        self.cli.cmd ( self.opt['hostname'] , 'file.remove'
                , [ os.path.join (self.opt['root'], self._mkName(), 'config') ] )
        self.cli.cmd ( self.opt['hostname'] , 'file.rmdir'
                , [ os.path.join (self.opt['root'], self._mkName()) ] )

    def l_enable(self):
        self.cli.cmd ( self.opt['hostname'], 'cp.get_template'
                ,   [ 'salt://resource/LXC/config.jinja'
                    , os.path.join(self.opt['root'], self._mkName(), 'config') ]
                , kwarg = dict ( self.opt, **{ 'autostart': True } )
                )

    def l_disable(self):
        self.cli.cmd ( self.opt['hostname'], 'cp.get_template'
                ,   [ 'salt://resource/LXC/config.jinja'
                    , os.path.join(self.opt['root'], self._mkName(), 'config') ]
                , kwarg = dict ( self.opt, **{ 'autostart': False } )
                )

    def l_start(self):
        self.cli.cmd ( self.opt['hostname'], 'file.write'
                ,   [ os.path.join(self.opt['root'], self._mkName(), '/rootfs/etc/hostname')
                    , '{container}'.format(**self.opt) ] )
        self.cli.cmd ( self.opt['hostname'], 'cmd.run',
            [ 'lxc-start'
                ' --daemon'
                ' --name {container}'
                .format (**self.opt) ]
            )

    def l_stop(self):
        self.cli.cmd ( self.opt['hostname'], 'cmd.run',
            [ 'lxc-stop'
                ' --name {container}'
                .format (**self.opt) ]
            )





