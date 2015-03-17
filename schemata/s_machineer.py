'''

'''

import os
import machineer.resources.lxc
import machineer.resources.mount
import machineer.resources.lvm
import machineer.resources.saltkey

import yaml
import jinja2

import machineer.generic
import machineer.registry 

def _options (opt):
    opt = machineer.generic._tree_merge ( [ yaml.load ( jinja2.Template (
        open (machineer.generic.conf_path) .read() ) .render() )
                  , opt ] )

    opt = machineer.generic._tree_merge ( [ opt,
            { 'resources':
                { 'LVM': 
                    { 'Origin': '{0[param][InstanceClass]}.{0[param][Project]}' .format (opt)
                    , 'LV': '{0[param][InstanceID]}.{0[param][Project]}' .format (opt)
                    , 'Pool': '{0[param][Master]}' .format (opt)
                    }
                , 'LXC': 
                    { 'container': '{0[param][InstanceID]}.{0[param][Project]}'.format (opt)
                    , 'group': '{0[param][Project]}' .format (opt)
                    , 'cpu_shares': '{0[param][cpu.shares]}' .format (opt)
                    , 'blkio_weight': '{0[param][blkio.weight]}' .format (opt)
                    , 'memory_soft_limit_in_bytes': '{0[param][memory.soft_limit_in_bytes]}' .format (opt)
                    , 'memory_limit_in_bytes': '{0[param][memory.limit_in_bytes]}' .format (opt)
                    }
                }
            } ]
        )

    opt = machineer.generic._tree_merge ( [ opt,
            { 'resources':
                { 'Mount':
                    { 'device': os.path.join (
                          '/dev/mapper'
                        , '{}-{}' .format (
                              machineer.generic._device_mapper_path_escape (
                                '{0[resources][LVM][VG]}' .format(opt) )
                            , machineer.generic._device_mapper_path_escape (
                                '{0[resources][LVM][LV]}' .format(opt) )
                            )
                        )
                    , 'mountpoint': os.path.join (
                          '{0[resources][LXC][root]}' .format (opt)
                        , '{0[resources][LXC][container]}' .format (opt)
                        , 'rootfs'
                        )
                    }
                , 'SaltKey': 
                    { 'minion_id': '{0[param][InstanceID]}.{0[param][Project]}' .format (opt)
                    }
                }
            } ]
        )

    return opt

def _resources (opt):
    return  { 'LXC': machineer.resources.lxc.LXC ( _options (opt) ['resources']['LXC'] )
            , 'Mount': machineer.resources.mount.Mount ( _options (opt) ['resources']['Mount'] )
            , 'LVM': machineer.resources.lvm.LVM ( _options (opt) ['resources']['LVM'] )
            , 'SaltKey': machineer.resources.saltkey.SaltKey ( _options (opt) ['resources'] ['SaltKey'] )
            }

def opt (opt):
    ret = _options (opt)
    machineer.registry.write_instance_subkey (opt, 'opt', ret)
    return ret

def status (opt):
    resources = _resources (opt)
    ret =   { key: resources [key] .status ()
            for key in 
            resources .keys()
            }
    machineer.registry.write_instance_subkey (opt, 'status', ret)
    return ret


def create (opt):
    machineer.registry.add_blueprint (opt)
    resources = _resources (opt)
    resources ['LVM'] .create ()
    resources ['LVM'] .enable ()
    resources ['LVM'] .start ()
    resources ['Mount'] .create ()
    resources ['Mount'] .enable ()
    resources ['Mount'] .start ()
    resources ['LXC'] .create ()
    resources ['SaltKey'] .create ()

    return status (opt)

def enable (opt):
    create (opt)
    resources = _resources ( _options (opt) )
    resources ['SaltKey'] .enable ()
    resources ['LXC'] .enable ()

    return status (opt)

def start (opt):
    enable (opt)
    resources = _resources ( _options (opt) )
    resources ['SaltKey'] .start ()
    resources ['LXC'] .start ()

    return status (opt)

def destroy(opt):
    resources = _resources (opt)
    resources ['LXC'] .stop ()
    resources ['LXC'] .disable ()
    resources ['LXC'] .destroy ()
    resources ['SaltKey'] .stop ()
    resources ['SaltKey'] .disable ()
    resources ['SaltKey'] .destroy ()
    resources ['Mount'] .stop ()
    resources ['Mount'] .disable ()
    resources ['Mount'] .destroy ()
    resources ['LVM'] .stop ()
    resources ['LVM'] .disable ()
    resources ['LVM'] .destroy ()

    return status (opt)

def forget (opt):
    machineer.registry.del_blueprint (opt)
    return True

