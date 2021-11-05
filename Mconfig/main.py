# -*- coding: utf-8 -*-
import os
import sys
import shutil
import traceback
import importlib
from Mconfig.core import ModifyClass

class Save(object):
    pass

class ConfigManage(object):

    WHITELIST = ["_file", "_file_name", "_modify_core", "processing_func", "_save"]

    def __init__(self, file="mconfig.py", processing_func=None) -> None:

        self._file = file

        file_path, all_file = os.path.split(self._file)
        if file_path:
            sys.path.append(file_path)

        self._file_name = all_file.replace(".py", "")

        # 'init config file'
        if not os.path.isfile(file):
            shutil.copyfile(__file__.replace("main.py", 'mconfig.py'), file)

        self._modify_core = ModifyClass(self._file)

        self.processing_func = processing_func

        self._save = Save()

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

            # processing
            self.processing(self.processing_func)
        except Exception:
            print("\033[0;36;41mSyntaxError:\033[0m")
            traceback.print_exc()

    def processing(self, processing_func):
        """ processing """
        """
        def processing_func(mc, save):
            save.my_num = mc.M_num * 2
        """
        if processing_func:
            try:
                processing_func(self, self._save)
            except Exception as err:
                print("processing err!")
                traceback.print_exc()
                print(err)

    def __dir__(self):
        """ self. """
        return sys.modules[self._file_name].__dir__() + self._save.__dir__()

    def __getattr__(self, attr: str):
        """ redirect """
        if attr in self.WHITELIST:
            return eval("self.{0}".format(attr))
        try:
            return eval("self._save.{0}".format(attr))
        except AttributeError:
            return eval("sys.modules[self._file_name].{0}".format(attr))

    def __setattr__(self, attr: str, value) -> None:
        """ set & modify"""
        if attr in self.WHITELIST:
            # this class variable
            return super().__setattr__(attr, value)
        else:
            # config variable
            self._modify_core._setattr(attr, value)
            self.processing(self.processing_func)

    def __delattr__(self, attr: str) -> None:
        """ del """
        self._modify_core._delattr(attr)
        self.processing(self.processing_func)
