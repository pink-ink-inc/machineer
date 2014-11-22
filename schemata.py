import yaml
import jinja2
import json
import redis
import os


from machineer.resources import lxc, lvm, mount 


confPath = '/etc/machineer/machineer.conf'


class Instance(object):

    def __init__(self, kws):
        self.opt = dict (
                  yaml.load (
                        jinja2.Template (
                              open(confPath).read()
                            ) .render()
                      )
                , **kws )
        self.store = redis.StrictRedis (host = self.opt['schemata']['redis-server']['hostname'])

    resources = []

    def options(self):
        return dict ( [ (r.__name__, r.options) for r in self.resources ] )

    def create(self):
        pass

class I_Machineer(Instance):

    resources = [ lxc.LXC, lvm.LVM, mount.Mount ]
    methods = [ 'create', 'enable', 'start', 'stop', 'disable', 'destroy' ]

    def __init__(self, kws):
        super(type(self), self).__init__(kws)
        for r in self.resources:
            if r.__name__ not in self.opt.keys():
                self.opt.update ({r.__name__: {}})

        self.opt['resources']['LVM']['Origin'
                ] = '{0[param][InstanceClass]}.{0[param][Project]}'.format(self.opt) 
        self.opt['resources']['LVM']['LV'
                ] = '{0[param][InstanceID]}.{0[param][Project]}'.format(self.opt)
        self.opt['resources']['LXC']['container'
                ] = '{0[param][InstanceID]}.{0[param][Project]}'.format(self.opt)

        self.dev_blockdev = lvm.LVM (self.opt['resources']['LVM'])

        self.dev_mount = mount.Mount ( {
                    'device': os.path.join (
                            '/dev/mapper'
                          , '{0[resources][LVM][VG]}-'.format(self.opt)
                              + self._dmEscape('{0[resources][LVM][LV]}'.format(self.opt))
                          )
                  , 'mountpoint': os.path.join (
                              '{0[resources][LXC][root]}'.format(self.opt)
                            , '{0[resources][LXC][container]}'.format(self.opt)
                            , 'rootfs'
                            )
                  } ) 

        self.dev_container = lxc.LXC ( self.opt['resources']['LXC'] )


    def create(self): 

        [ getattr(o,a)()
                for o in [ self.dev_blockdev, self.dev_mount, self.dev_container ]
                for a in [ 'create', 'enable', 'start' ] ]
        return self._jsonConvert ( { 'Status': 'Ok' } )

    def destroy(self):
        [ f() for f in [ getattr(o,a)
                for o in reversed ( [ self.dev_blockdev, self.dev_mount, self.dev_container ] )
                for a in [ 'stop', 'disable', 'destroy' ] ] ]


    def missingKeys(self):
        m = dict ( filter (
                          lambda x: len(x[1]) > 0
                        , [ (r.__name__, list (
                                            set(r.options)
                                          ^ set(self.opt[r.__name__].keys())
                                          )
                            ) for r in self.resources ] ) )
        return self._jsonConvert ( { 'Status': 'missingKeys', 'missingKeys': m } )

    @staticmethod
    def _jsonConvert(d):
        return json.dumps ( d
                , indent = 2
                )

    @staticmethod
    def _dmEscape(s):
        return ''.join([ l + l if l == '-' else l for l in list(s) ] )

    # def create(self):
    #     print self.options()
    #     lvm.LVM(self.opt['LVM']).create()
    #     lxc.LXC(self.opt['LXC']).create()
