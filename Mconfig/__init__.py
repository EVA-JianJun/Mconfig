# -*- coding: utf-8 -*-
import sys
"""
Version 0.8.6
"""
__version__ = "0.8.6"

class MyModuleCall(sys.modules[__name__].__class__):
    # module call
    def __call__(self, *args, **kwargs):
        from Mconfig.main import ConfigManage
        return ConfigManage(*args, **kwargs)

sys.modules[__name__].__class__ = MyModuleCall

sys.modules["Mconfig_Context"] = dict()

del sys, MyModuleCall
