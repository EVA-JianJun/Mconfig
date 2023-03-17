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

CLASS_SET = {int, float, str, bool, list, tuple, set, dict, datetime}

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

    def __init__(self, config_file: str, manage: object) -> None:

        self._config_file = config_file
        self.manage = manage
        _, all_file = os.path.split(self._config_file)
        self._module_name = all_file.replace(".py", "")

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
        # inheritance MconfigClass
        class_list = FIND_CLASS_PATTON.findall(source)
        for replace_str, class_name in class_list:
            source = source.replace(replace_str, "{0}(MconfigClass)".format(class_name))

        # add datetime
        s_part_1, s_part_2 = source.split('\n', 1)
        if "datetime.datetime" in s_part_2:
            # import datetime
            source = s_part_1 + "\nimport datetime\nfrom Mconfig.core import MconfigClass\n" + s_part_2 + "\ndel datetime\ndel MconfigClass"
        else:
            # from datetime import datetime
            source = s_part_1 + "\nfrom datetime import datetime\nfrom Mconfig.core import MconfigClass\n" + s_part_2 + "\ndel datetime\ndel MconfigClass"

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
            if line.strip().startswith('#') and not line.startswith('# Create Time:'):
                if len(line.strip()) < len(line):
                    class_dict[class_name].append({
                                    "Remark" : line
                                })
                else:
                    variable_list.append(line)
                continue

            # find import
            if line.startswith('import') or line.startswith('from'):
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

                        if type(value) in CLASS_SET:
                            class_dict[class_name].append({
                                    attr : value
                                })
                        else:
                            raise ValueError("Class nesting is not supported!")

                        modify_flag = True
                    else:
                        class_dict[class_name].append({
                                variable_name_strip : eval("module.{0}.{1}".format(class_name, variable_name_strip))
                            })
                else:
                    # normal variable
                    if attr == variable_name and not modify_class_name:
                        if type(value) in CLASS_SET:
                            variable_list.append({
                                attr : value
                            })
                        else:
                            # add name
                            variable_list.append(attr)
                            # add class_dict
                            class_dict[attr] = []
                            for variable_name in dir(value):
                                if not variable_name.startswith('_'):
                                    get_class_variable_value = eval("value.{0}".format(variable_name))
                                    if type(get_class_variable_value) in CLASS_SET:
                                        class_dict[attr].append({
                                                variable_name : get_class_variable_value
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
                if type(value) in CLASS_SET:
                    class_dict[modify_class_name].append({
                            attr : value
                        })
                else:
                    raise ValueError("Class nesting is not supported!")
            else:
                # normal variable
                if attr in all_class_name_list:
                    if type(value) in CLASS_SET:
                        # is class name and value is normal type
                        raise NameError("The variable name is the same as the class name! {0}".format(attr))
                    else:
                        # overwrite old class
                        class_dict[attr] = []
                        for variable_name in dir(value):
                            if not variable_name.startswith('_'):
                                get_class_variable_value = eval("value.{0}".format(variable_name))
                                if type(get_class_variable_value) in CLASS_SET:
                                    class_dict[attr].append({
                                            variable_name : get_class_variable_value
                                    })
                else:
                    if type(value) in CLASS_SET:
                        variable_list.append({
                            attr : value
                        })
                    else:
                        # new class
                        variable_list.append(attr)
                        class_dict[attr] = []
                        for variable_name in dir(value):
                            if not variable_name.startswith('_'):
                                get_class_variable_value = eval("value.{0}".format(variable_name))
                                if type(get_class_variable_value) in CLASS_SET:
                                    class_dict[attr].append({
                                            variable_name : get_class_variable_value
                                    })

        new_source = "# Create Time: {0}\n".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        datetime_flag = False
        for variable in variable_list:
            if isinstance(variable, str):
                if variable.startswith('#') or variable.startswith('import') or variable.startswith('from'):
                    if variable == "from datetime import datetime":
                        datetime_flag = True
                    new_source += variable + '\n'
                else:
                    # class
                    class_name = variable
                    class_variable_list = class_dict[class_name]
                    class_code = "class {0}():\n\n".format(class_name)
                    for variable_dict in class_variable_list:
                        for key, value in variable_dict.items():
                            if datetime_flag and isinstance(value, datetime):
                                class_code += "    {0} = {1}\n\n".format(key, value.__repr__().replace("datetime.datetime", "datetime"))
                            else:
                                if key == "Remark":
                                    class_code += value + '\n'
                                else:
                                    class_code += "    {0} = {1}\n\n".format(key, value.__repr__())

                    new_source += class_code

            elif isinstance(variable, dict):
                for key, value in variable.items():
                    if datetime_flag and isinstance(value, datetime):
                        new_source += "{0} = {1}\n\n".format(key, value.__repr__().replace("datetime.datetime", "datetime"))
                    else:
                        new_source += "{0} = {1}\n\n".format(key, value.__repr__())

        # print(new_source)

        # format
        try:
            new_source = yapf.yapf_api.FormatCode(new_source)[0]
        except Exception as err:
            print(new_source)
            print("Format Error! Please contact the author to submit this bug.")
            raise err

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
            with open(self._config_file, 'w', encoding='utf-8') as fw:
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
            if line.strip().startswith('#') and not line.startswith('# Create Time:'):
                if len(line.strip()) < len(line):
                    class_dict[class_name].append({
                                    "Remark" : line
                                })
                else:
                    variable_list.append(line)
                continue

            # find import
            if line.startswith('import') or line.startswith('from'):
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
        datetime_flag = False
        for variable in variable_list:
            if isinstance(variable, str):
                if variable.startswith('#') or variable.startswith('import') or variable.startswith('from'):
                    if variable == "from datetime import datetime":
                        datetime_flag = True
                    new_source += variable + '\n'
                else:
                    # class
                    class_name = variable
                    class_variable_list = class_dict[class_name]
                    class_code = "class {0}():\n\n".format(class_name)
                    for variable_dict in class_variable_list:
                        for key, value in variable_dict.items():
                            if datetime_flag and isinstance(value, datetime):
                                class_code += "    {0} = {1}\n\n".format(key, value.__repr__().replace("datetime.datetime", "datetime"))
                            else:
                                if key == "Remark":
                                    class_code += value + '\n'
                                else:
                                    class_code += "    {0} = {1}\n\n".format(key, value.__repr__())

                    new_source += class_code

            elif isinstance(variable, dict):
                for key, value in variable.items():
                    if datetime_flag and isinstance(value, datetime):
                        new_source += "{0} = {1}\n\n".format(key, value.__repr__().replace("datetime.datetime", "datetime"))
                    else:
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
                    # print(os.stat(self._config_file).st_mtime, self._config_file_modify_time)
                    # reload
                    # DEBUG
                    self._setattr_lock.acquire()
                    try:
                        print("{0} Reload config: {1}".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), self._config_file))
                        spec, source = self._get_source_code()
                        self._import(spec, source)
                        self.manage.processing(self.manage.processing_func)
                    except SyntaxError as err:
                        print("\033[0;36;41mReload config SyntaxError:\033[0m")
                        traceback.print_exc()
                        print(err)
                    finally:
                        # update fix
                        time.sleep(3)
                        self._config_file_modify_time = os.stat(self._config_file).st_mtime
                        # print("_config_file_modify_time:", self._config_file_modify_time)
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
