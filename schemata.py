import types

import jinja2
import json
import yaml
import redis
import os
import copy


from machineer.resources import lxc, lvm, mount


confPath = '/etc/machineer/machineer.conf'

machineer = { 'create': lambda x: I_Machineer(x).create()
            , 'enable': lambda x: I_Machineer(x).enable()
            , 'start': lambda x: I_Machineer(x).start()
            , 'destroy': lambda x: I_Machineer(x).destroy()
            , 'test': lambda x: I_Machineer(x).test()
            , 'list': lambda x: list_(x)
            , 'status': lambda x: I_Machineer(x).status()
            , 'get_status': lambda x: I_Machineer(x).get_status()
            }

nextgisweb =    { 'create': lambda x: I_NextGISWeb(x) .create()
                , 'destroy': lambda x: I_NextGISWeb(x) .destroy()
                , 'status': lambda x: I_NextGISWeb(x) .status()
                , 'get_status': lambda x: I_NextGISWeb(x) .get_status()
                }

api =   { 'machineer': machineer 
        , 'nextgisweb': nextgisweb
        }

def list_(project = None):
    opt = dict ( yaml.load ( jinja2.Template ( open(confPath).read()) .render() ) )
    store = redis.StrictRedis (host = opt['schemata']['redis-server']['hostname'])
    return filter ( lambda x: x[0]
            , [
                  ( project
                    , [ json.loads (key) for key in
                        store.smembers ( 'schemata-project-param:{project}'
                            .format(project = project) ) ] )
                , ( True
                    , list (store.smembers ( 'schemata-projects' ) ) )
              ]

            ) [0] [1]


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
        self.store_key = ( 'schemata-instance:{0[param][InstanceID]}'
                '.{0[param][Project]}'.format(self.opt) )
        self.store.sadd ('schemata-projects', self.opt['param']['Project'])
        self.store.sadd ('schemata-project:{0[param][Project]}'.format(self.opt)
                , self.store_key)
        self.store.sadd ('schemata-project-param:{0[param][Project]}'.format(self.opt)
                , self._jsonConvert(self.opt['param']) )
        self.store.set (self.store_key + ':opt', self._jsonConvert (self.opt))

        self.dev = {}

    resources = []

    def wrapFork(self, f):
        pid = os.fork()
        if (pid == 0):
            f()
        else:
            return _jsonConvert ( {'Status': 'Ok'} )

    def options(self):
        return dict ( [ (r.__name__, r.options) for r in self.resources ] )

    def create(self):
        pass

    def status(self):
        s = self._in_status()
        self.store.set (self.store_key, self._jsonConvert (s))
        self.store.set (self.store_key + ':status', self._jsonConvert (s))
        return s

    def get_status(self):
        return yaml.load ( self.store.get(self.store_key) )

    @staticmethod
    def _jsonConvert(d):
        return json.dumps ( d
                , indent = 2
                )


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
        self.opt['resources']['LVM']['Pool'
                ] = '{0[param][Master]}'.format(self.opt)
        self.opt['resources']['LXC']['container'
                ] = '{0[param][InstanceID]}.{0[param][Project]}'.format(self.opt)
        self.opt['resources']['LXC']['group'
                ] = '{0[param][Project]}' .format(self.opt)

        self.dev_blockdev = lvm.LVM (self.opt['resources']['LVM'])

        self.dev_mount = mount.Mount ( {
                    'device': os.path.join (
                            '/dev/mapper'
                          , self._dmEscape('{0[resources][LVM][VG]}'.format(self.opt))
                              + '-' + self._dmEscape('{0[resources][LVM][LV]}'.format(self.opt))
                          )
                  , 'mountpoint': os.path.join (
                              '{0[resources][LXC][root]}'.format(self.opt)
                            , '{0[resources][LXC][container]}'.format(self.opt)
                            , 'rootfs'
                            )
                  } )

        self.dev_container = lxc.LXC ( self.opt['resources']['LXC'] )

        self.dev ['LXC'] = self.dev_container
        self.dev ['Mount'] = self.dev_mount
        self.dev ['LVM'] = self.dev_blockdev

    def test(self):
        return (self.opt)

    def _in_status(self):
        status =  { key: self.dev [key] .status()
                for key in self.dev.keys()
                }
        dicts = { key:
                        { dee: str (getattr (status [key], dee) )
                        for dee in dir (status [key])
                        if dee[0:1] != '_' }

                for key in status.keys() }
        return dicts
        # return \
        #         { 'status': {
        #               'LXC':
        #             { 'running': self.dev_container.status().isRunning
        #             , 'autostart' : self.dev_container.status().isEnabled
        #             , 'ip': self.dev_container.status().descr }
        #             if self.dev_container.status().exists
        #             else False
        #             , 'LVM':
        #             { 'enabled': self.dev_blockdev.status().isRunning
        #             , 'writable' : self.dev_blockdev.status().isEnabled }
        #             if self.dev_blockdev.status().exists
        #             else False
        #             , 'Mount':
        #             { 'mounted': self.dev_mount.status().isRunning
        #             , 'automount' : self.dev_mount.status().isEnabled }
        #             if self.dev_mount.status().exists
        #             else False
        #         } }

    def create(self):
        [ getattr(o,a)()
                for o in [ self.dev_blockdev]
                for a in [ 'create', 'enable', 'start'] ]
        [ getattr(o,a)()
                for o in [ self.dev_mount, self.dev_container ]
                for a in [ 'create'] ]
        return self.status()

    def enable(self):
        [ getattr(o,a)()
                for o in [ self.dev_blockdev]
                for a in [ 'create', 'enable', 'start'] ]
        [ getattr(o,a)()
                for o in [ self.dev_mount, self.dev_container ]
                for a in [ 'create', 'enable'] ]
        return self.status()

    def start(self):
        [ getattr(o,a)()
                for o in [ self.dev_blockdev]
                for a in [ 'create', 'enable', 'start'] ]
        [ getattr(o,a)()
                for o in [ self.dev_mount, self.dev_container ]
                for a in [ 'create', 'enable', 'start'] ]
        return self.status()

    def destroy(self):
        [ f() for f in [ getattr(o,a)
                for a in [ 'stop', 'disable', 'destroy' ]
                for o in reversed ( [ self.dev_blockdev, self.dev_mount, self.dev_container ] ) ] ]
        return self.status()

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
    def _dmEscape(s):
        return ''.join([ l + l if l == '-' else l for l in list(s) ] )


class I_NextGISWeb(Instance):
    def __init__(self, kws):
        super(type(self), self).__init__(kws)
        self.prototype_opt = copy.deepcopy(self.opt)
        self.prototype = I_Machineer(self.prototype_opt)

    def create(self):
        self.prototype_status = self.prototype.create()
        return self.prototype_status

    def destroy(self):
        self.prototype_status = self.prototype.destroy()
        return self.prototype_status

    def _in_status(self):
        return self.prototype._in_status()

