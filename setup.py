"""A setuptools based setup module.

See:
https://packaging.python.org/guides/distributing-packages-using-setuptools/
https://github.com/pypa/sampleproject
"""

# Always prefer setuptools over distutils
import os
import re
from setuptools import setup, find_namespace_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()

# Get the long description from the README file and remove badges
README = open('multi_ear_services/README.rst').read_text(encoding='utf-8')
README = re.sub('----.*marker', '----', README, flags=re.DOTALL)


setup(
    name='multi_ear_services',
    python_requires='>=3.6.0',
    description='Multi-EAR system services for the host Raspberry Pi OS LITE (32-bit) with sensorboard.',
    long_description=README,
    long_description_content='text/x-rst',
    url='https://github.com/Multi-EAR/Multi-EAR-services',
    author='Olivier den Ouden, Pieter Smets and others',
    maintainer = 'Olivier den Ouden, Pieter Smets',
    maintainer_email='mail@pietersmets.be',
    download_url='https://github.com/Multi-EAR/Multi-EAR-services',
    license='GNU General Public License v3 (GPLv3)',
    license_file = 'LICENSE',
    packages=find_namespace_packages(include=['multi-ear-services.*']),
    include_package_data=True,
    zip_safe=False,
    platforms = 'ARMv7',
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
        'Source': 'https://github.com/Multi-EAR/Multi-EAR-services',
        'Tracker': 'https://github.com/Multi-EAR/Multi-EAR-services/issues',
    },
    keywords='multi-ear, raspberry pi, mems, gpio, timeseries, waveforms',
    entry_points={
        'console_scripts': ['multi-ear-uart=multi_ear_services.uart:uart_readout'],
    },
    scripts=[
        'multi_ear_services/wifi/multi-ear-wifi',
    ],
    # package_data={
    #     'sample': ['package_data.dat'],
    # },
    data_files=[
        ('multi-ear-services', ['multi_ear_services/ctrl/uwsgi.ini',
                                'multi_ear_services/uart/influxdb.ini'])
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
        'write_to': os.path.join('multi_ear_services', 'version.py'),
    },
    setup_requires=['setuptools_scm', 'flake8'],
)
