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

    def _getRawStatusList(self):
        return [ LXC.RawStatus(* re.split('  +', line.strip())) for line in self.cli.cmd(
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
            , isEnabled = rawStatus.autostart == 'YES'
            , isRunning = rawStatus.state == 'RUNNING'
            , descr = ', '.join(iplist)
            )

    def _containerName(self):
        return "{ClusterName}-{InstanceID}".format(**self.opt)

    # def _path(self):
    #     return os.path.join(conf.get('master','lxcPath'), self._name())

    # def _config(self):
    #     return os.path.join(conf.get('master','lxcPath'), self._name(), 'config')


    def __init__(self, kws): 
        super(type(self), self).__init__(kws)
        self.opt.update(kws)
        # try: self.opt['container'] = "{ClusterName}-{InstanceID}".format(**self.opt)
        # except KeyError: pass

    # def test(self):
    #     tgt = conf.get('master','hostname').encode('ascii')
    #     return self.cli.cmd(tgt, 'cmd.run', ['ls /'])

    def status(self):
        matches = [ x for x in self._getRawStatusList()
                if x.name == self._containerName() ]
        if len(matches) == 0: return ResourceStatus()
        else: return self._resolveRawStatus(matches[0])

    def list(self):
        return [ self._resolveRawStatus(x) for x in self._getRawStatusList() ]

        

    def create(self):
        pass


