import unittest

import machineer.resources.lxc


class TestResourceLXC(unittest.TestCase):

    def setUp(self):
        self.o = machineer.resources.lxc.LXC({'InstanceID':'tempora','ClusterName':'machineer'})

    def test(self):
        self.assertFalse (self.o)
        self.o.create()
        self.assertIn ( self.o.name(), [ x.name for x in self.o.list() ] )
        self.assertTrue (self.o)
        self.assertTrue (self.o.isEnabled())
        self.o.disable()
        self.assertFalse (self.o.isEnabled())
        self.o.enable()
        self.assertTrue (self.o.isEnabled())
        self.o.destroy()
        self.assertFalse (self.o)

if __name__ == '__main__':
    unittest.main()

