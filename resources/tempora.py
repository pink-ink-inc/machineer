

from machineer.resources import *


class Tempora(Resource):

    methods = [ 'create', 'destroy' ]

    def __init__(self, kws): 
        super(type(self), self).__init__(kws)
        self.defineMethods() 
        self.opt['flag'] = False

    def v_create(self):
        return self.opt['flag']

    def l_create(self):
        self.opt['flag'] = True

    def v_destroy(self):
        return not self.opt['flag']

    def l_destroy(self):
        self.opt['flag'] = False
