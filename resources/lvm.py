import time
import collections
import copy

from machineer.resources import *


class LVM(Resource):

    RawStatus = collections.namedtuple (
              'RawStatus'
            , ['LV', 'VG', 'Attr', 'LSize', 'Pool', 'Origin', 'Data', 'Meta', 'Move'
                , 'Log', 'CpySync', 'Convert']
            )
    nameFormat = '{VG}/{LV}'
    methods = [ 'groupinit', 'create', 'enable', 'start', 'stop', 'disable', 'destroy', 'snap' ] 
    options = [ 'VG', 'Pool', 'Origin', 'LV' ]

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
        return self.nameFormat.format(VG = self.opt['VG'], LV = self.opt['LV'])

    def status(self):
        matches = [ x for x in self._getRawStatusList()
                if self.opt['LV'] == x.LV and self.opt['VG'] == x.VG ]
        if len(matches) != 0: print matches[0]
        else: print ('No matches')
        if len(matches) == 0: return ResourceStatus()
        else: return self._resolveRawStatus(matches[0])

    def list(self):
        return [ self._resolveRawStatus(x) for x in self._getRawStatusList() ]

    def __init__(self, kws): 
        super(type(self), self).__init__(kws) 
        self.defineMethods()

    def v_groupinit(self):
        pool = LVM({'LV': self.opt['Pool']}) 
        status = pool.status()
        return bool (status.exists and status.isPool)

    def l_groupinit(self):
        self.cli.cmd ( self.opt['hostname'], 'cmd.run', 
            [ 'lvcreate'
                ' --size {PoolSize}'
                ' --name {Pool}'
                ' {VG}'
                .format (**self.opt) ]
            )
        self.cli.cmd ( self.opt['hostname'], 'cmd.run',
            [ 'lvcreate'
                ' --size {PoolMetaSize}'
                ' --name {Pool}_meta'
                ' ngw'
                .format (**self.opt) ]
            )
        self.cli.cmd ( self.opt['hostname'], 'cmd.run',
            [ 'yes | lvconvert'
                ' --thinpool {VG}/{Pool}'
                ' --poolmetadata {VG}/{Pool}_meta'
                .format (**self.opt) ]
            )
        self.cli.cmd ( self.opt['hostname'], 'cmd.run',
            [ 'lvcreate'
                ' --name {Pool}_zero'
                ' --virtualsize 2G'
                ' --thinpool {VG}/{Pool}'
                .format (**self.opt) ]
            )

    def l_create(self):
        print ( 'command: ' 'lvcreate'
                ' --type thin'
                ' --name {LV}'
                ' --snapshot {Origin}'
                ' --thinpool {VG}/{Pool}'
                .format (**self.opt) )
        print self.cli.cmd ( self.opt['hostname'], 'cmd.run',
            [ 'lvcreate'
                ' --type thin'
                ' --name {LV}'
                ' --snapshot {Origin}'
                ' --thinpool {VG}/{Pool}'
                .format (**self.opt) ]
            )

    def l_destroy(self):
        self.cli.cmd ( self.opt['hostname'], 'cmd.run',
            # [ 'lvremove'
            #     ' --force'
            #     ' {VG}/{LV}'
            #     .format (**self.opt) ]
            [ 'lvrename'
                ' {VG}'
                ' {LV}'
                ' {LV}_destroyed_{time}'
                .format (time = time.time(), **self.opt) ]
            )
        
    def l_enable(self):
        print self.cli.cmd ( self.opt['hostname'], 'cmd.run',
            [ 'lvchange'
                ' --setactivationskip n'
                ' --permission rw'
                ' {VG}/{LV}'
                .format (**self.opt) ]
            )

    def l_disable(self):
        self.cli.cmd ( self.opt['hostname'], 'cmd.run',
            [ 'lvchange'
                ' --setactivationskip y'
                ' --permission r'
                ' {VG}/{LV}'
                .format (**self.opt) ]
            )

    def l_start(self):
        print self.cli.cmd ( self.opt['hostname'], 'cmd.run',
            [ 'lvchange'
                ' --activate y'
                ' {VG}/{LV}'
                .format (**self.opt) ]
            )

    def l_stop(self):
        self.cli.cmd ( self.opt['hostname'], 'cmd.run',
            [ 'lvchange'
                ' --activate n'
                ' {VG}/{LV}'
                .format (**self.opt) ]
            )

    def v_snap (self):
        try:
            return LVM (self.opt_snap) .status() .exists
        except (AttributeError, KeyError):
            return False


    def l_snap (self): 
        self.opt_snap = copy.deepcopy (self.opt)
        self.opt_snap['SnapTime'] = time.time()
        self.opt_snap['LV'] = '{0[LV]}_snap_{1[SnapTime]}'.format (self.opt, self.opt_snap)
        self.opt_snap['Origin'] = self.opt['LV']
        print self.opt_snap
        LVM (self.opt_snap) .create()
        

