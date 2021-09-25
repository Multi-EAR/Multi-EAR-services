# -*- coding: utf-8 -*-
import os
import re
from setuptools import setup, find_namespace_packages

# Get README and remove badges.
README = open('README.rst').read()
README = re.sub('----.*marker', '----', README, flags=re.DOTALL)

DESCRIPTION = ''

NAME = 'multi-ear-services'

setup(
    name=NAME,
    python_requires='>=3.7.0',
    description=DESCRIPTION,
    long_description=README,
    author='Pieter Smets',
    author_email='mail@pietersmets.be',
    url='https://github.com/Multi-EAR/Multi-EAR-software',
    download_url='https://github.com/Multi-EAR/Multi-EAR-software',
    license='GNU General Public License v3 (GPLv3)',
    packages=find_namespace_packages(include=['multi-ear-services.*']),
    keywords=[
        'multi-ear', 'timeseries', 'waveforms',
    ],
    entry_points={
        'console_scripts': [],
    },
    scripts=[],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'Intended Audience :: Developers',
        ('License :: OSI Approved :: '
         'GNU General Public License v3 (GPLv3)'),
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    install_requires=[
        'pyserial>=3.5',
        'uwsgi>=2.0',
        'flask>=2.0',
        'numpy>=1.18',
        'influxdb-client>=1.20',
    ],
    use_scm_version={
        'root': '.',
        'relative_to': __file__,
        'write_to': os.path.join('multi-ear-services', 'version.py'),
    },
    setup_requires=['setuptools_scm'],
)
