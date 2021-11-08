# -*- coding: utf-8 -*-
import sys

__version__ = "1.1.2"

class MyModuleCall(sys.modules[__name__].__class__):
    # module call
    def __call__(self, *args, **kwargs):
        from Mconfig.main import ConfigManage
        return ConfigManage(*args, **kwargs)

sys.modules[__name__].__class__ = MyModuleCall

sys.modules["Mconfig_Context"] = dict()

del sys, MyModuleCall
