# -*- coding: utf-8 -*-
import os
import re
from setuptools import setup, find_namespace_packages

# Get README and remove badges.
README = open('README.rst').read()
README = re.sub('----.*marker', '----', README, flags=re.DOTALL)

DESCRIPTION = 'Multi-EAR modules and services for Raspberry Pi OS (32-bit)'

NAME = 'multi-ear'

setup(
    name=NAME,
    python_requires='>=3.6.0',
    description=DESCRIPTION,
    long_description=README,
    author='Olivier den Ouden, Pieter Smets and others',
    maintainer = 'Olivier den Ouden, Pieter Smets',
    maintainer_email='mail@pietersmets.be',
    url='https://github.com/Multi-EAR/Multi-EAR-software',
    download_url='https://github.com/Multi-EAR/Multi-EAR-software',
    license='GNU General Public License v3 (GPLv3)',
    license_file = 'LICENSE',
    platforms = 'ARMv7',
    packages=find_namespace_packages(include=['multi_ear.*']),
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Science/Research',
        'Intended Audience :: Education',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: Unix',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Topic :: Education',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
        'Topic :: Scientific/Engineering :: Atmospheric Science',
        'Topic :: Scientific/Engineering :: Physics',
    ],
    project_urls={
        'Source': 'https://github.com/Multi-EAR/Multi-EAR-software',
        'Tracker': 'https://github.com/Multi-EAR/Multi-EAR-software/issues',
    },
    keywords=[
        'multi-ear', 'mems', 'gpio', 'raspberry pi', 'timeseries', 'waveforms',
    ],
    entry_points={
        'console_scripts': [f'{NAME}-uart=multi_ear.uart.uart_readout'],
    },
    scripts=[
        'multi-ear/wifi/enable_wifi_access_point.sh',
        'multi-ear/wifi/disable_wifi_access_point.sh',
    ],
    install_requires=[
        'pyserial>=3.5',
        'gpiozero>=1.6',
        'uwsgi>=2.0',
        'flask>=2.0',
        'numpy>=1.18',
        'influxdb-client>=1.20',
    ],
    use_scm_version={
        'root': '.',
        'relative_to': __file__,
        'write_to': os.path.join('multi-ear', 'version.py'),
    },
    setup_requires=['setuptools_scm', 'flake8'],
)
