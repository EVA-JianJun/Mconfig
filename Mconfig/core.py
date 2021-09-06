# -*- coding: utf-8 -*-
import os
import re
import sys
import time
import threading
import importlib
import traceback
from datetime import datetime
from Mconfig import yapf

FIND_CLASS_PATTON = re.compile("\nclass\s+((.+?)\([object]*\)):")
FIND_CLASS_NAME_PATTON = re.compile("\nclass\s+(.+?)\([object]*\):")
FIND_CLASS_NAME_LINE_PATTON = re.compile("class\s+(.+?)\([object]*\):")
FIND_VARIABLE_PATTON = re.compile("(.+)?\s+=")

class MconfigClass(object):

    _WHITELIST = ["WHITELIST", "_modify_core"]

    def __setattr__(self, attr: str, value) -> None:
        """ set & modify"""
        if attr in self._WHITELIST:
            # this class variable
            return super().__setattr__(attr, value)
        else:
            # config variable
            self._modify_core._setattr(attr, value, self.__class__.__name__)

    def __delattr__(self, name: str) -> None:
        """ del """
        self._modify_core._delattr(name, self.__class__.__name__)

class ModifyClass():
    """ Modify config and Save config """

    def __init__(self, config_file: str) -> None:

        self._config_file = config_file
        self._module_name = config_file.replace(".py", "")

        self._config_file_modify_time = os.stat(self._config_file).st_mtime

        try:
            self._setattr_lock = sys.modules["Mconfig_Context"][self._config_file]
        except KeyError:
            lock = threading.RLock()
            sys.modules["Mconfig_Context"][self._config_file] = lock
            self._setattr_lock = lock

        # start daemon
        self._config_load_daemon_server()

    def _wapper_class(self, source: str) -> str:
        """ overwrite class """
        class_list = FIND_CLASS_PATTON.findall(source)
        for replace_str, class_name in class_list:
            source = source.replace(replace_str, "{0}(MconfigClass)".format(class_name))
        s_part_1, s_part_2 = source.split('\n', 1)
        source = s_part_1 + "\nfrom Mconfig.core import MconfigClass\n" + s_part_2 + "del MconfigClass"
        return source

    def _setattr(self,  attr: str, value, modify_class_name=None) -> None:
        """ modify & import """
        self._setattr_lock.acquire()
        try:
            # DEBUG
            # print("set:", attr, "value:", value, "modify_class_name:", modify_class_name)
            spec, source = self._get_source_code()
            new_source = self._modify(source, attr, value, modify_class_name)
            self._import(spec, new_source)
        finally:
            self._setattr_lock.release()

    def _modify(self, source: str, attr: str, value, modify_class_name: str) -> str:
        """ modify config """
        all_class_name_list = FIND_CLASS_NAME_PATTON.findall(source)

        # load module
        module = sys.modules[self._module_name]

        variable_list = []
        class_dict = {}
        modify_flag = False
        for line in  source.split('\n'):
            # find annotation
            if line.startswith('#') and not line.startswith('# Create Time:'):
                variable_list.append(line)

            # find class
            class_name_list = FIND_CLASS_NAME_LINE_PATTON.findall(line)
            if class_name_list:
                class_name = class_name_list[0]
                variable_list.append(class_name)
                class_dict[class_name] = []

            # find veriable
            veriable_lsit = FIND_VARIABLE_PATTON.findall(line)
            if veriable_lsit:
                variable_name = veriable_lsit[0]

                variable_name_strip = variable_name.strip()
                if len(variable_name_strip) < len(variable_name):
                    # class variable
                    if modify_class_name == class_name and attr == variable_name_strip:
                        class_dict[class_name].append({
                                attr : value
                            })
                        modify_flag = True
                    else:
                        class_dict[class_name].append({
                                variable_name_strip : eval("module.{0}.{1}".format(class_name, variable_name_strip))
                            })
                else:
                    # normal variable
                    if attr == variable_name and not modify_class_name:
                        variable_list.append({
                            attr : value
                        })
                        modify_flag = True
                    else:
                        variable_list.append({
                            variable_name : eval("module.{0}".format(variable_name))
                        })

        if not modify_flag:
            # add variable
            if modify_class_name:
                # class variable
                class_dict[modify_class_name].append({
                        attr : value
                    })
            else:
                # normal variable
                if attr in all_class_name_list:
                    raise NameError("The variable name is the same as the class name! {0}".format(attr))

                variable_list.append({
                    attr : value
                })

        new_source = "# Create Time: {0}\n".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        for variable in variable_list:
            if isinstance(variable, str):
                if variable.startswith('#'):
                    new_source += variable + '\n'
                else:
                    # class
                    class_name = variable
                    class_variable_list = class_dict[class_name]
                    class_code = "class {0}():\n\n".format(class_name)
                    for variable_dict in class_variable_list:
                        for key, value in variable_dict.items():
                            class_code += "    {0} = {1}\n\n".format(key, value.__repr__())

                    new_source += class_code

            elif isinstance(variable, dict):
                for key, value in variable.items():
                    new_source += "{0} = {1}\n\n".format(key, value.__repr__())

        # format
        try:
            new_source = yapf.yapf_api.FormatCode(new_source)[0]
        except Exception as err:
            raise err("Format Error! Please contact the author to submit this bug.")

        # print(new_source)

        return new_source

    def _import(self, spec, source):

        try:
            # overwrite class
            overwrite_source = self._wapper_class(source)

            # import
            module = importlib.util.module_from_spec(spec)
            codeobj = compile(overwrite_source, module.__spec__.origin, 'exec')
            exec(codeobj, module.__dict__)

            # init class
            for verable_str in dir(module):
                if not verable_str.startswith('_'):
                    verable = eval("module.{0}".format(verable_str))
                    if isinstance(verable, type):
                        exec("module.{0} = verable()".format(verable_str))
                        exec("module.{0}._modify_core = self".format(verable_str))

            # save
            sys.modules[self._module_name] = module

            # save file
            with open(self._config_file, 'w') as fw:
                fw.write(source)

            # update
            self._config_file_modify_time = os.stat(self._config_file).st_mtime

        except Exception as err:
            print("Compilation failed! Please contact the author to submit this bug.")
            traceback.print_exc()
            print(err)
            raise err

    def _get_source_code(self):

        spec = importlib.util.find_spec(self._module_name)
        source = spec.loader.get_source(self._module_name)

        return spec, source

    def _delattr(self, attr: str, del_class_name=None) -> None:
        """ del """
        self._setattr_lock.acquire()
        try:
            # DEBUG
            # print("del:", attr, "del_class_name:", del_class_name)
            spec, source = self._get_source_code()
            new_source = self._del_source(source, attr, del_class_name)
            self._import(spec, new_source)
        finally:
            self._setattr_lock.release()

    def _del_source(self, source: str, attr: str, del_class_name: str) -> str:
        """ del source """
        # load module
        module = sys.modules[self._module_name]

        variable_list = []
        class_dict = {}
        for line in  source.split('\n'):
            # find annotation
            if line.startswith('#') and not line.startswith('# Create Time:'):
                variable_list.append(line)

            # find class
            class_name_list = FIND_CLASS_NAME_LINE_PATTON.findall(line)
            if class_name_list:
                class_name = class_name_list[0]
                if attr == class_name:
                    # del class
                    pass
                else:
                    variable_list.append(class_name)
                class_dict[class_name] = []

            # find veriable
            veriable_lsit = FIND_VARIABLE_PATTON.findall(line)
            if veriable_lsit:
                variable_name = veriable_lsit[0]

                variable_name_strip = variable_name.strip()
                if len(variable_name_strip) < len(variable_name):
                    # class variable
                    if del_class_name != class_name:
                        # not need del class variable
                        class_dict[class_name].append({
                                variable_name_strip : eval("module.{0}.{1}".format(class_name, variable_name_strip))
                            })
                    else:
                        # is this class variable
                        if not attr == variable_name_strip:
                            class_dict[class_name].append({
                                    variable_name_strip : eval("module.{0}.{1}".format(class_name, variable_name_strip))
                                })
                else:
                    # normal variable
                    if not attr == variable_name:
                        variable_list.append({
                            variable_name : eval("module.{0}".format(variable_name))
                        })

        new_source = "# Create Time: {0}\n".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        for variable in variable_list:
            if isinstance(variable, str):
                if variable.startswith('#'):
                    new_source += variable + '\n'
                else:
                    # class
                    class_name = variable
                    class_variable_list = class_dict[class_name]
                    class_code = "class {0}():\n\n".format(class_name)
                    for variable_dict in class_variable_list:
                        for key, value in variable_dict.items():
                            class_code += "    {0} = {1}\n\n".format(key, value.__repr__())

                    new_source += class_code

            elif isinstance(variable, dict):
                for key, value in variable.items():
                    new_source += "{0} = {1}\n\n".format(key, value.__repr__())

        # format
        try:
            new_source = yapf.yapf_api.FormatCode(new_source)[0]
        except Exception as err:
            raise err("Format Error! Please contact the author to submit this bug.")

        # print(new_source)

        return new_source

    def _config_load_daemon_server(self):
        """ Configure and modify the daemon service """
        def sub():
            while True:
                time.sleep(5)
                if os.stat(self._config_file).st_mtime != self._config_file_modify_time:
                    # reload
                    # DEBUG
                    self._setattr_lock.acquire()
                    try:
                        print("{0} Reload config: {1}".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), self._config_file))
                        spec, source = self._get_source_code()
                        self._import(spec, source)
                    except SyntaxError as err:
                        print("\033[0;36;41mReload config SyntaxError:\033[0m")
                        traceback.print_exc()
                        print(err)
                        # update fix
                        self._config_file_modify_time = os.stat(self._config_file).st_mtime
                    finally:
                        self._setattr_lock.release()

        self._setattr_lock.acquire()
        try:
            try:
                run_flag = sys.modules["Mconfig_Context"]["daemon_th"]
            except KeyError:
                run_flag = False

            if not run_flag:
                # DEBUG
                # print("daemon run..")
                daemon_th = threading.Thread(target=sub, name='LoopThread')
                daemon_th.setDaemon(True)
                daemon_th.start()
                sys.modules["Mconfig_Context"]["daemon_th"] = True
        finally:
            self._setattr_lock.release()
