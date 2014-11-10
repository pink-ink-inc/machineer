import os
import collections
import re

import salt.client

from machineer.resources import *


class LXC(Resource):

    def __init__(self, kws):
        self.name = "{ClusterName}-{InstanceID}".format(**kws)
        self.path   = os.path.join(conf.get('master','lxcPath'), self.name)
        self.config = os.path.join(conf.get('master','lxcpath'), self.name, 'config')
        self.cli = salt.client.LocalClient()

    def test(self):
        tgt = conf.get('master','hostname').encode('ascii')
        print type(tgt)
        print tgt
        print 'master-18'
        return self.cli.cmd(tgt, 'cmd.run', ['ls /'])

    def status(self):
        LXCRawStatus = collections.namedtuple(
                  'LXCRawStatus'
                , ['name', 'state', 'ipv4', 'ipv6', 'autostart']
                )

        lines = self.cli.cmd(
                  conf.get('master','hostname')
                , 'cmd.run'
                , ['lxc-ls --fancy']
                ) [conf.get('master','hostname')] .splitlines() [2:]

        containers = [ LXCRawStatus(* re.split('  +', line.strip())) for line in lines ] 
        matches = [ x for x in containers if x.name == self.name ]

        if len(matches) == 0:
            return ResourceStatus() 

        else: # A tiny functional exercise.
            iplist = sum( [ line.split(', ') if line != '-' else []
                        for line in [matches[0].ipv4, matches[0].ipv6] ] , [ ] ) 
            return ResourceStatus(
                  exists = True
                , isEnabled = matches[0].autostart == 'YES'
                , isRunning = matches[0].state == 'RUNNING'
                , statusDescription = ', '.join(iplist)
                )

    def create(self):
        pass


