#!/usr/bin/env python3
from distutils.core import setup
files = []

setup(name='shorn',
	version='0.3.1',
	description='git-wrapper',
	url='zoerb.cc',
	author='Dominic Zoerb',
	author_email='dominic@zoerb.cc',
	packages=['package'],
	scripts=['runner'],
	package_data={'package' : files}
	)
