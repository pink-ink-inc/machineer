import base64
import hashlib
import operator
import os
import collections

from machineer.resources import *



class Mount(Resource):

    RawStatus = collections.namedtuple (
              'RawStatus'
            , ['device', 'mountpoint']
            )

    options = [ 'device', 'mountpoint', 'order' ]

    @staticmethod
    def _stringToNamedTuple (tup, string, defaultValue = ' '):
        return tup (** dict(zip( tup._fields, list ( defaultValue * len (tup._fields)) ))
                ) ._replace (** dict(zip( tup._fields, string.split() )))

    def _getStatusList(self, xs):
            return [ Mount._stringToNamedTuple (Mount.RawStatus, x)
                    for x in xs ]

    def _getListEnabled(self):
        try:
            xs = self.cli.cmd ( self.opt['hostname'], 'cmd.run'
                    , [ 'cat {fstabs} 2>/dev/null'.format(fstabs = os.path.join(self.opt['fstab_d'], '*')) ]
                    ) [self.opt['hostname']] .splitlines()
        except KeyError:
            xs = []
        return self._getStatusList(xs)

    def _getListRunning(self):
        try:
            xs = [ ' '.join(operator.itemgetter(0,2)(line.split()))
                    for line in self.cli.cmd ( self.opt['hostname'], 'cmd.run'
                            , [ 'mount' ]
                            ) [self.opt['hostname']] .splitlines() ]
        except KeyError:
            xs = []
        return self._getStatusList(xs)


    def _findFirst(self, xs, cond):
        matches = [ x for x in xs if cond(x) ]
        if len(matches):
            return matches[0]

    def _mkName(self):
        h = hashlib.sha1()
        h.update ( self.opt['device'] + self.opt['mountpoint'] )
        self.opt['digest'] = base64.b32encode(h.digest())
        return '{order}-{digest}'.format(**self.opt)

    def __init__(self, kws):
        super(type(self), self).__init__(kws)

        self.opt['name'] = self._mkName()
        self.opt['fstab'] = os.path.join(self.opt['fstab_d'], self.opt['name'])

        self.defineMethods()

    def identify(self, x):
        def readlink(path):
            return self.cli.cmd ( self.opt['hostname'], 'cmd.run',
                [ 'readlink -f {}' .format (path) ] ) [self.opt['hostname']]

        return bool (
                readlink(self.opt['device']) == readlink(x.device) and
                readlink(self.opt['mountpoint']) == readlink(x.mountpoint)
                )

    def _checkDevice(self):
        return sum(
                [ self.cli.cmd ( self.opt['hostname'], 'file.is_blkdev'
                    , [self.opt['device']] )[self.opt['hostname']]
                , self.cli.cmd ( self.opt['hostname'], 'file.is_chrdev'
                    , [self.opt['device']] )[self.opt['hostname']]
                , self.cli.cmd ( self.opt['hostname'], 'file.directory_exists'
                    , [self.opt['device']] )[self.opt['hostname']]
            ] ) == 1

    def _checkMountpoint(self):
        return self.cli.cmd ( self.opt['hostname'], 'file.directory_exists'
                    , [self.opt['mountpoint']] )[self.opt['hostname']]

    def status(self):
        s = self.cli.cmd ( self.opt ['hostname']
                , 'machineer-mount-helpers.status'
                , kwarg = { 'src': self.opt ['device'], 'tgt': self.opt ['mountpoint'] }
                ) [self.opt ['hostname']]
        return  { 'name': self.opt['name']
                , 'exists': s ['exists']
                , 'isRunning': s ['running']
                , 'isEnabled': s ['enabled']
                , 'description': '{device} on {mountpoint} with {options}' .format(**self.opt)
                }

    def l_create(self):
        if not self._checkDevice():
            self.cli.cmd ( self.opt['hostname'], 'file.mkdir', [self.opt['device']] )
        if not self._checkMountpoint():
            self.cli.cmd ( self.opt['hostname'], 'file.mkdir', [self.opt['mountpoint']] )

    def l_destroy(self):
            self.cli.cmd ( self.opt['hostname'], 'file.rmdir', [self.opt['device']] )
            self.cli.cmd ( self.opt['hostname'], 'file.rmdir', [self.opt['mountpoint']] )


    def l_enable(self):
        self.cli.cmd ( self.opt['hostname'], 'cmd.run',
                [ 'echo'
                    ' {device}\t{mountpoint}'
                    ' > {fstab}'
                    .format (**self.opt) ]
                )
        if ( self.cli.cmd ( self.opt['hostname']
                , 'file.directory_exists'
                , [ self.opt ['device'] ]
                ) [ self.opt ['hostname'] ] and ( 'limit-data' in self.opt .keys() ) ):

            self.cli.cmd ( self.opt ['hostname']
                    , 'cmd.run'
                    , [ 'xfs_quota -x'
                        ' -c "project -s -p {device} {num_id}" {xfs_root}' .format (**self.opt)
                      ]
                )
            self.cli.cmd ( self.opt ['hostname']
                    , 'cmd.run'
                    , [ 'xfs_quota -x'
                        ' -c "limit -p bhard={limit-data} {num_id}" {xfs_root}' .format (**self.opt)
                      ]
                )

    def l_disable(self):
        self.cli.cmd ( self.opt['hostname'], 'cmd.run',
                [ 'rm'
                    ' {fstab}'
                    .format (**self.opt) ]
                )

    def l_start(self):
        self.cli.cmd ( self.opt['hostname'], 'cmd.run',
                [ 'initctl'
                    ' stop'
                    ' machineer-mount'
                    ' device={device}'
                    ' mountpoint={mountpoint}'
                    ' options={options}'
                    .format (**self.opt) ]
                )
        self.cli.cmd ( self.opt['hostname'], 'cmd.run',
                [ 'initctl'
                    ' start'
                    ' machineer-mount'
                    ' device={device}'
                    ' mountpoint={mountpoint}'
                    ' options={options}'
                    .format (**self.opt) ]
                )

    def l_stop(self):
        self.cli.cmd ( self.opt['hostname'], 'cmd.run',
                [ 'initctl'
                    ' stop'
                    ' machineer-mount'
                    ' device={device}'
                    ' mountpoint={mountpoint}'
                    ' options={options}'
                    .format (**self.opt) ]
                )



