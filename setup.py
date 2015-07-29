# -*- coding: utf-8 -*-
from distutils.core import setup

setup(
    name='lxc',
    version='0.1.0',
    author='François Ménabé',
    author_email='francois.menabe@gmail.com',
    py_modules=['lxc'],
    description='An API for managing LXC containers.',
    long_description=open('README.rst').read()
)
