import unittest

import machineer.resources.lxc as lxc


class TestResourceLXC(unittest.TestCase):

    def setUp(self):
        pass
        # self.o = machineer.resources.lxc.LXC()

    def test_status(self):
        self.assertTrue(lxc.LXC({'InstanceID':'salt'}).status().isRunning) 

    def test_list(self):
        self.assertTrue (len([ x.descr for x in lxc.LXC({}).list() ])) 

if __name__ == '__main__':
    unittest.main()

