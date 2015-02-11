import yaml
import jinja2
import os

import salt.client


# import lxc


confPath = '/etc/machineer/machineer.conf'

class Resource(object):

    def __init__(self, kws):
        self.__opts__ = salt.config.master_config('/etc/salt/master')
        globConf = [ ]
        self.cli = salt.client.LocalClient()
        self.opt = {}
        try: self.opt .update (
                yaml.load ( jinja2.Template(open(confPath).read()).render()
                    ) ['resources'] [type(self).__name__] )
        except KeyError: pass
        self.opt .update ( **kws )
        for key in globConf:
            self.opt[key] = yaml.load (
                    jinja2.Template(open(confPath).read()).render()
                    ) [key]

        def wrap(f):
            def ret(*args, **kws):
                os.sys.stdout.write (
                        'calling function {0[1]}'
                        ' on host {0[0]}'
                        ' with args following:\n' .format  (args)
                        )
                os.sys.stdout.write (str(args))
                os.sys.stdout.write (str(kws))
                s = f (*args, **kws)
                os.sys.stdout.write ('\n' 'Output:' '\n')
                os.sys.stdout.write(str(s) if s else 'No output.')
                os.sys.stdout.write('\n' + '-'*10 + '\n')
                return s
            return ret
        self.cli.cmd = wrap ( self.cli.cmd )

    methods = [ 'create', 'enable', 'start', 'stop', 'disable', 'destroy' ]

    def defineMethods(self):
        [ setattr ( self, f
            , self.wrap ( getattr (self, 'l_'+f), getattr (self, 'v_'+f) )
            ) for f in self.methods ]

    @staticmethod
    def wrap (logic, check):
        def closure():
            print ' -- Entering {l}'.format (l = logic.__name__)
            if '__module__' in dir(logic):
                c = logic.__module__
            elif 'im_self' in dir(logic):
                c = logic.im_self.__class__.__name__
            else:
                c = '...unknown origin...'
            print ' -- closure class :: {}.' .format (c)
            if not check():
                print 'State is not desirable. Will run the logic.'
                logic()
                print 'Logic completed.'
                assert check()
                print 'Desirable state reached.'
            else:
                print 'State is already as desired.'
        return closure

    def v_create  (self) : return bool(self)
    def v_enable  (self) : return self.isEnabled ()
    def v_start   (self) : return self.isRunning ()
    def v_destroy (self) : return not self.v_create ()
    def v_disable (self) : return not self.v_enable ()
    def v_stop    (self) : return not self.v_start  ()


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

wrap_method = Resource.wrap


