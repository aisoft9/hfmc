#!/usr/bin/python3
#-*- encoding: UTF-8 -*-

from setuptools import setup, find_packages

"""
打包的用的setup必须引入，
"""

VERSION = '0.0.1'

setup(name='hffs',
      version=VERSION,
      description="a tiny cli and server use p2p accelerate hugging face model download!",
      long_description=open("README.md", "r").read(),
      long_description_content_type="text/markdown",
      classifiers=["Topic :: Software Development", "Development Status :: 3 - Alpha",
                   "Programming Language :: Python :: 3.11"],
      # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='hffs python hugging face download accelerate',
      author='9#',
      author_email='953175531@qq.com',
      url='https://github.com/madstorage-dev/hffs',
      license='',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=True,
      install_requires=open('requirements.txt', 'r') .read().splitlines(),
      python_requires=">=3.11",
      entry_points={
          'console_scripts': [
              'hffs = hffs.hffs:main'
          ]
      },
      setup_requires=['setuptools', 'wheel']
      )

# usage:
# requires:
# pip3 install twine
# clean:
# rm -rf build/ dist/ hffs.egg-info/
# build:
# python3 setup.py sdist bdist_wheel
# upload:
# twine upload dist/hffs*
