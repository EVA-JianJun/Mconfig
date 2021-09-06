# Mconfig - ModifyConfig

**.py 配置文件！Python最好用的配置文件，没有之一！**

只要写Python，用完Mconfig后，会觉得以前用的什么 yaml、ini、toml、json 之类的配置文件格式都是垃圾.

传统的配置文件有这么几个问题：

* 不易修改：导入前就得提前设定好，不能在程序运行中修改配置文件或者修改特别麻烦.
* 读写风险：同时读写配置造成配置混乱或系统异常.
* 差异化大：一种格式对应一个包，导入进来各种花里胡哨的功能，函数一堆，参数一堆，实际能用到的不多.
* 学习成本：学习成本其实也不多，就额外花点时间学下语法格式，看下数据转换存储，再花点时间看看对应包的使用.

`Mconfig` 解决了上面所有的问题，又对功能做了极大的加强！不是说加了很多函数需要你来学习.

**它没有任何函数，没有任何方法，没有任何属性，只有Python语法！**

让你用着爽，什么都不用管，像写Python一样使用配置文件！

## 安装

    pip install Mconfig

## 使用

    import Mconfig
    mc = Mconfig()

只需要两行代码，就可以得到一个使用简便并且功能强大的配置文件对象.

![Mconfig][1]

* **原生语法支持**：Python 语法直接写配置文件，支持 Python 原生所有数据类型，并支持自定义类；
* **高效简易使用**：增、删、改、查，全部通过 Python 语法实现，没有任何的函数方法，优雅自然；
* **双向自动同步**：文件或者内存配置的修改会双向自动同步，自动修改源代码，自动读取文件更新；
* **全局线程安全**：全线程，全对象，随意操作，全局锁数据不丢失，文件错误自动处理；

配置文件默认为 mconfig.py ，如果不存在会在当前目录下新建默认的 mconfig.py 配置文件：

![Mconfig][2]

支持 **数字、字符串、布尔、列表、元组、字典，自定义类** 数据类型.

其中自定义类的使用相当于是为配置指定了一个域，不同类型的配置可以写在对应的自定义类里，不同类里的变量名可以重名.

也可以手动为Mconfig指定一个参数作为配置文件名称：

    mc = Mconfig("myconfig.py")

## 增删改查

### 增：

    In [1]: mc.new_variable = "i'm a new variable!"

    In [2]: mc.new_variable
    Out[2]: "i'm a new variable!"

### 删：

    In [3]: del mc.M_tuple

    In [4]: del mc.M_num

### 改：

    In [5]: mc.M_bool = False

    In [6]: mc.M_bool
    Out[6]: False

    In [7]: mc.M_bool = True

    In [8]: mc.M_List
    Out[8]: [1, 2, 3]

    In [9]: mc.M_bool = mc.M_List

    In [10]: mc.M_bool
    Out[10]: [1, 2, 3]

### 查：

    In [11]: mc.M_str
    Out[11]: 'Hello Mconfig!'

    In [12]: mc.M_List
    Out[12]: [1, 2, 3]

    In [13]: mc.M_bool
    Out[13]: True

    In [14]: mc.M_dict
    Out[14]: {'a': 1, 'b': 2}

### 对自定义类下的变量操作：

就是多访问了一层，操作和上面一样

    In [15]: mc.M_SomeConfigClass_a.variable_new = "i'm a new class variable!"

    In [16]: del mc.M_SomeConfigClass_a.variable_b

    In [17]: mc.M_SomeConfigClass_a.variable_c = True

    In [18]: mc.M_SomeConfigClass_a.variable_a
    Out[18]: 1

**以上的所有操作只要配置信息发生改变都会同步到 mconfig.py 源文件中**

* 用户修改 mconfig.py 后会自动同步所有的 mc 对象.
* 任意的 mc 对象的改变会自动修改 mconfig.py 源文件.

**无论创建了几个 mc 实例，只要 mc 使用的配置文件一致，当任意配置发生改变，所有的 mc 的配置信息会自动进行同步，并同步修改源文件，所有的 mc 对象指向同一个地址.**

## 使用包

yapf 0.31.0 https://pypi.org/project/yapf/ (不需要安装，已经集成)

## 注意事项

* 在同一进程中具有相同名称但目录位置不同的配置文件会被识别为同一个配置文件，请使用不同的文件名标识不同的配置文件.
* 全局进程锁现在还不支持，因为考虑到使用的情况也不多，且如果增加此功能可能需要调度端口，或者增加一个包的依赖.

## TODO

* 同名文件处理
* 进程锁支持
* 分布式配置文件


  [1]: https://raw.githubusercontent.com/EVA-JianJun/GitPigBed/master/blog_files/img/Mconfig_0.png
  [2]: https://raw.githubusercontent.com/EVA-JianJun/GitPigBed/master/blog_files/img/Mconfig_1.png
