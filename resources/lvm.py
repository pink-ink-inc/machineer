import time
import collections

from machineer.resources import *


class LVM(Resource):

    RawStatus = collections.namedtuple (
              'RawStatus'
            , ['LV', 'VG', 'Attr', 'LSize', 'Pool', 'Origin', 'Data', 'Meta', 'Move'
                , 'Log', 'CpySync', 'Convert']
            )
    nameFormat = '{VG}/{LV}'
    methods = [ 'groupinit', 'create', 'enable', 'start', 'stop', 'disable', 'destroy' ] 

    def _getRawStatusList(self):
        default = self.RawStatus(** dict(zip(
              self.RawStatus._fields
            , list(' '*len(self.RawStatus._fields))
            )))

        return [ default._replace(** dict(zip(self.RawStatus._fields
            , line.lstrip().split(' ')))) for line in self.cli.cmd (
                  self.opt['hostname']
                , 'cmd.run'
                , ['lvs --noheadings --separator " "']
                ) [self.opt['hostname']] .splitlines() [1:] ]

    @staticmethod
    def _resolveRawStatus(s):
        return ResourceStatus(
              name = LVM.nameFormat.format(**s._asdict())
            , exists = True # Presumably.
                            # A status can only be generated from an existing instance.
            , isRunning = s.Attr[4] == 'a'  # Active. Enabled for mounting.
            , isEnabled  = ( s.Attr[1] == 'w'  # Writable. Not read-only.
                and s.Attr[9] != 'k' )  # Activation skip mark is unset.
                                        # I.e. the volume will be activated at start-up.
            , isPool = s.Attr[0] == 't'
            , descr = '{Pool}/{Origin} {Data}%{LSize}'.format(**s._asdict())
            )

    def _mkName(self):
        return self.nameFormat.format(VG = self.opt['group'], LV = self.opt['name'])

    def status(self):
        matches = [ x for x in self._getRawStatusList()
                if self.opt['name'] == x.LV and self.opt['group'] == x.VG ]
        if len(matches) != 0: print matches[0]
        else: print ('No matches')
        if len(matches) == 0: return ResourceStatus()
        else: return self._resolveRawStatus(matches[0])

    def list(self):
        return [ self._resolveRawStatus(x) for x in self._getRawStatusList() ]

    def __init__(self, kws): 
        super(type(self), self).__init__(kws)

        [ setattr ( self, f
            , self.wrap ( getattr (self, 'l_'+f), getattr (self, 'v_'+f) )
            ) for f in self.methods ]

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

    def v_create  (self) : return bool(self)
    def v_enable  (self) : return self.isEnabled ()
    def v_start   (self) : return self.isRunning () 
    def v_destroy (self) : return not self.v_create ()
    def v_disable (self) : return not self.v_enable ()
    def v_stop    (self) : return not self.v_start  ()

    def v_groupinit(self):
        pool = LVM({'name': self.opt['pool']}) 
        status = pool.status()
        return bool (status.exists and status.isPool)

    def l_groupinit(self):
        self.cli.cmd ( self.opt['hostname'], 'cmd.run', 
            [ 'lvcreate'
                ' --size {poolsize}'
                ' --name {pool}'
                ' {group}'
                .format (**self.opt) ]
            )
        self.cli.cmd ( self.opt['hostname'], 'cmd.run',
            [ 'lvcreate'
                ' --size {poolmetasize}'
                ' --name {pool}_meta'
                ' ngw'
                .format (**self.opt) ]
            )
        self.cli.cmd ( self.opt['hostname'], 'cmd.run',
            [ 'yes | lvconvert'
                ' --thinpool {group}/{pool}'
                ' --poolmetadata {group}/{pool}_meta'
                .format (**self.opt) ]
            )
        self.cli.cmd ( self.opt['hostname'], 'cmd.run',
            [ 'lvcreate'
                ' --name zero'
                ' --virtualsize 2G'
                ' --thinpool ngw/machineer'
                .format (**self.opt) ]
            )

    def l_create(self):
        self.cli.cmd ( self.opt['hostname'], 'cmd.run',
            [ 'lvcreate'
                ' --type thin'
                ' --name {name}'
                ' --snapshot {image}'
                ' --thinpool {group}/{pool}'
                .format (**self.opt) ]
            )

    def l_destroy(self):
        self.cli.cmd ( self.opt['hostname'], 'cmd.run',
            # [ 'lvremove'
            #     ' --force'
            #     ' {group}/{name}'
            #     .format (**self.opt) ]
            [ 'lvrename'
                ' {group}'
                ' {name}'
                ' {name}_destroyed_{time}'
                .format (time = time.time(), **self.opt) ]
            )
        
    def l_enable(self):
        self.cli.cmd ( self.opt['hostname'], 'cmd.run',
            [ 'lvchange'
                ' --setactivationskip n'
                ' --permission rw'
                ' {group}/{name}'
                .format (**self.opt) ]
            )

    def l_disable(self):
        self.cli.cmd ( self.opt['hostname'], 'cmd.run',
            [ 'lvchange'
                ' --setactivationskip y'
                ' --permission r'
                ' {group}/{name}'
                .format (**self.opt) ]
            )

    def l_start(self):
        self.cli.cmd ( self.opt['hostname'], 'cmd.run',
            [ 'lvchange'
                ' --activate y'
                ' {group}/{name}'
                .format (**self.opt) ]
            )

    def l_stop(self):
        self.cli.cmd ( self.opt['hostname'], 'cmd.run',
            [ 'lvchange'
                ' --activate n'
                ' {group}/{name}'
                .format (**self.opt) ]
            )

