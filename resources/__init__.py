import yaml
import jinja2

import salt.client


# import lxc


confPath = '/etc/machineer/machineer.conf'


class Resource(object):

    def __init__(self, kws):
        self.cli = salt.client.LocalClient() 
        self.opt = dict(
                yaml.load(
                      jinja2.Template(open(confPath).read()).render()
                    ) [type(self).__name__], **kws)

    def create(self): pass

    def status(self):
        return ResourceStatus()

    def list(self):
        return [ResourceStatus()]

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

    def name(self):
        return self.status().name


class ResourceStatus(object): 

    def __init__(self, **kws):

        arg_vals = {
                  'exists': False
                , 'isEnabled': False
                , 'isRunning': False
                , 'descr': ''
                }

        arg_vals.update(kws)
        for kw,arg in arg_vals.iteritems():
            setattr(self, kw, arg)


