import configparser


# import lxc


confPath = '/etc/machineer/machineer.conf'


conf = configparser.ConfigParser()
conf.read(confPath)


class Resource(object):
    def __init__(self): pass

    def create(self): pass

    def status(self):
        return ResourceStatus()

    def enable(self): pass

    def disable(self): pass

    def start(self): pass

    def stop(self): pass

    def isRunning(self):
        return self.status().isRunning

    def isEnabled(self):
        return self.status().isEnabled

    def __nonzero__(self):
        return self.status().exists


class ResourceStatus(object): 

    def __init__(self, **kws):

        arg_vals = {
                  'exists': False
                , 'isEnabled': False
                , 'isRunning': False
                , 'statusDescription': ''
                }

        arg_vals.update(kws)
        for kw,arg in arg_vals.iteritems():
            setattr(self, kw, arg)


