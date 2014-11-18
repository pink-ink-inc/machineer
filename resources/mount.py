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
        return base64.b32encode(h.digest())

    def __init__(self, kws): 
        super(type(self), self).__init__(kws)

        self.opt['name'] = self._mkName()
        self.opt['fstab'] = os.path.join(self.opt['fstab_d'], self.opt['name'])

        self.defineMethods()

    def defineMethods(self):
        [ setattr ( self, f
            , self.wrap ( getattr (self, 'l_'+f), getattr (self, 'v_'+f) )
            ) for f in self.methods ] 

    methods = [ 'create', 'enable', 'start', 'stop', 'disable', 'destroy' ]

    @staticmethod
    def wrap(logic, valid):
        def closure():
            print 'Entering ' + logic.__name__ + ' with ' + valid.__name__
            if not valid():
                print 'State is not desirable. Will run the logic.'
                logic()
                print 'Logic completed.'
                assert valid()
                print 'Desirable state reached.'
            else:
                print 'State is already desirable.'
        return closure

    def identify(self, x):
        return bool (
                self.opt['device'] == x.device and
                self.opt['mountpoint'] == x.mountpoint
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
        return ResourceStatus ( name = self.opt['name']
                , exists = self._checkDevice() and self._checkMountpoint()
                , isRunning = bool ( self._findFirst (self._getListRunning(), self.identify ))
                , isEnabled = bool ( self._findFirst (self._getListEnabled(), self.identify ))
                , descr = '{device} on {mountpoint}'.format(**self.opt)
                )

    def v_create  (self) : return bool(self)
    def v_enable  (self) : return self.isEnabled ()
    def v_start   (self) : return self.isRunning () 
    def v_destroy (self) : return not self.v_create ()
    def v_disable (self) : return not self.v_enable ()
    def v_stop    (self) : return not self.v_start  ()

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

    def l_disable(self):
        self.cli.cmd ( self.opt['hostname'], 'cmd.run',
                [ 'rm'
                    ' {fstab}'
                    .format (**self.opt) ]
                )
    
    def l_start(self):
        self.cli.cmd ( self.opt['hostname'], 'cmd.run',
                [ 'initctl'
                    ' start'
                    ' machineer-mount'
                    ' device={device}'
                    ' mountpoint={mountpoint}'
                    .format (**self.opt) ]
                )
    
    def l_stop(self):
        self.cli.cmd ( self.opt['hostname'], 'cmd.run',
                [ 'initctl'
                    ' stop'
                    ' machineer-mount'
                    ' device={device}'
                    ' mountpoint={mountpoint}'
                    .format (**self.opt) ]
                )
