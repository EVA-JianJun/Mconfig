#!/usr/bin/env python
# coding: utf-8
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fd:
    long_description = fd.read()

setup(
    name = 'Mconfig',
    version = '1.1.4',
    author = 'jianjun',
    author_email = '910667956@qq.com',
    url = 'https://github.com/EVA-JianJun/Mconfig',
    description = u'.py 配置文件！Python最好用的配置文件！',
    long_description = long_description,
    long_description_content_type = "text/markdown",
    packages = find_packages(),
    install_requires = [],
    entry_points = {
    }
)