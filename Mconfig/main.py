# -*- coding: utf-8 -*-
import os
import sys
import shutil
import traceback
import importlib
from Mconfig.core import ModifyClass


class ConfigManage(object):

    WHITELIST = ["_file", "_file_name", "_modify_core"]

    def __init__(self, file="mconfig.py") -> None:

        self._file = file
        self._file_name = file.replace(".py", "")

        self._modify_core = ModifyClass(file)

        # 'init config file'
        if not os.path.isfile(file):
            shutil.copyfile(__file__.replace("main.py", 'mconfig.py'), file)

        # 'import config(mudule)'
        # 'import self._file_name'
        try:
            # import
            spec = importlib.util.find_spec(self._file_name)
            source = spec.loader.get_source(self._file_name)
            source = self._modify_core._wapper_class(source)
            module = importlib.util.module_from_spec(spec)
            codeobj = compile(source, module.__spec__.origin, 'exec')
            exec(codeobj, module.__dict__)

            # init class
            for verable_str in dir(module):
                if not verable_str.startswith('_'):
                    verable = eval("module.{0}".format(verable_str))
                    if isinstance(verable, type):
                        exec("module.{0} = verable()".format(verable_str))
                        exec("module.{0}._modify_core = self._modify_core".format(verable_str))

            # save
            sys.modules[self._file_name] = module
        except Exception:
            print("\033[0;36;41mSyntaxError:\033[0m")
            traceback.print_exc()

    def __dir__(self):
        """ self. """
        return sys.modules[self._file_name].__dir__()

    def __getattr__(self, attr: str):
        """ redirect """
        return eval("sys.modules[self._file_name].{0}".format(attr))

    def __setattr__(self, attr: str, value) -> None:
        """ set & modify"""
        if attr in self.WHITELIST:
            # this class variable
            return super().__setattr__(attr, value)
        else:
            # config variable
            self._modify_core._setattr(attr, value)

    def __delattr__(self, attr: str) -> None:
        """ del """
        self._modify_core._delattr(attr)