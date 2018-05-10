#
#    ICRAR - International Centre for Radio Astronomy Research
#    (c) UWA - The University of Western Australia, 2016
#    Copyright by UWA (in the framework of the ICRAR)
#    All rights reserved
#
#    This library is free software; you can redistribute it and/or
#    modify it under the terms of the GNU Lesser General Public
#    License as published by the Free Software Foundation; either
#    version 2.1 of the License, or (at your option) any later version.
#
#    This library is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#    Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public
#    License along with this library; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston,
#    MA 02111-1307  USA
#

import os
import subprocess
import sys

from setuptools import find_packages
from setuptools import setup


# Version information
# We do like numpy: we have a major/minor/patch hand-written version written
# here. If we find the git commit (either via "git" command execution or in a
# dlg/version.py file) we append it to the VERSION later.
# The RELEASE flag allows us to create development versions properly supported
# by setuptools/pkg_resources or "final" versions.
MAJOR   = 0
MINOR   = 4
PATCH   = 0
RELEASE = True
VERSION = '%d.%d.%d' % (MAJOR, MINOR, PATCH)
VERSION_FILE = 'dlg/version.py'

def get_git_version():
    out = subprocess.check_output(['git', 'rev-parse', 'HEAD'])
    return out.strip().decode('ascii')

def get_version_info():
    git_version = 'Unknown'
    if os.path.exists('.git'):
        git_version = get_git_version()
    full_version = VERSION
    if not RELEASE:
        full_version = '%s.dev0+%s' % (VERSION, git_version[:7])
    return full_version, git_version

def write_version_info():
    tpl = """
# THIS FILE IS GENERATED BY DALIUGE'S SETUP.PY
# DO NOT MODIFY BY HAND
version = '%(version)s'
git_version = '%(git_version)s'
full_version = '%(full_version)s'
is_release = %(is_release)s

if not is_release:
    version = full_version
"""
    full_version, git_version = get_version_info()
    with open(VERSION_FILE, 'w') as f:
        info = tpl % {'version': VERSION,
                      'full_version': full_version,
                      'git_version': git_version,
                      'is_release': RELEASE}
        f.write(info.strip())

# Every time we overwrite the version file
write_version_info()

# HACK - HACK - HACK - HACK
#
# We externally make sure that numpy is installed because spead2 needs it there
# at compile time (and therefore at runtime too).

# An initial solution for this problem was to add numpy to the setup_requires
# argument of spead2's setup invocation. This solves the problem of compiling
# numpy, but requires some extra code to make numpy's include directory
# (which isn't installed in a standard location, and therefore must be queried
# to numpy itself via numpy.include_dir()) available to spead2's setup in order
# to build its C extensions correctly. The main drawback from this solution is
# that numpy's egg location remains inside the spead2's source code tree (in the
# root of the tree when using setuptools < 7, inside the .eggs/ directory when
# using setuptools>=7). This was reported in setuptool issues #209 and #391, but
# still remains an issue. Although one could live with such an installation, it
# doesn't sound ideal at all since the software is not installed when one would
# expect it to be; also permissions-based problems could arise.
#
# For the time being I'm choosing instead to simply install numpy via a pip
# command-line invocation. It will avoid any numpy mingling by spead2, and will
# return quickly if it has been already installed
#
# HACK - HACK - HACK - HACK
try:
    subprocess.check_call(['pip','install','numpy'])
except subprocess.CalledProcessError:
    try:
        subprocess.check_call(['easy_install','numpy'])
    except subprocess.CalledProcessError:
        raise Exception("Couldn't install numpy manually, sorry :(")

# Core requirements of DALiuGE
# Keep alpha-sorted PLEASE!
install_requires = [
    "boto3",
    "bottle",
    "configobj",
    "crc32c",
    "dill",
    "docker",
    "lockfile",
    "metis>=0.2a3",
    # 0.10.6 builds correctly with old (<=3.10) Linux kernels
    "netifaces>=0.10.6",
    "paramiko",
    "psutil",
    "pyswarm",
    "python-daemon",
    "pyzmq",
    "scp",
    # 1.10 contains an important race-condition fix on lazy-loaded modules
    'six>=1.10',
    # 0.6 brings python3 support plus other fixes
    "zerorpc >= 0.6"
]
# Keep alpha-sorted PLEASE!

# Python 3.6 is only supported in NetworkX 2 and above
if sys.version_info >= (3, 6, 0):
    install_requires.append("networkx>=2.0")
else:
    install_requires.append("networkx")

# Python 2 support has been dropped in zeroconf 0.20.
# Also, 0.19.0 requires netifaces < 0.10.5, exactly the opposite of what *we* need
if sys.version_info[:2] == (2, 7):
    install_requires.append("zeroconf == 0.19.1")
else:
    install_requires.append("zeroconf >= 0.19.1")

# Packages that need to be installed from somewhere different than PyPI
dependency_links = [
    # None at the moment
]

# Extra requirements that are not needed by your every day daliuge installation
extra_requires = {
    # spead is required only for a specific app and its test, which we
    # skip anyway if spead is not found
    'spead': ["spead2==0.4.0"],

    # Pyro4 and RPyC are semi-supported RPC alternatives
    # (while zerorpc is the default)
    'pyro': ['Pyro4>=4.47'], # 4.47 contains a fix we contributed
    'rpyc': ['rpyc'],

    # drive-casa is used by some manual tests under test/integrate
    'drive-casa': ["drive-casa>0.7"],

    # MPI support (MPIApp drops and HPC experiments) requires mpi4py
    'MPI': ['mpi4py']
}

setup(
      name='daliuge',
      version=get_version_info()[0],
      description=u'Data Activated \uF9CA (flow) Graph Engine - DALiuGE',
      long_description = "The SKA-SDK prototype for the Execution Framework component",
      author='ICRAR DIA Group',
      author_email='dfms_prototype@googlegroups.com',
      url='https://github.com/ICRAR/daliuge',
      license="LGPLv2+",
      packages=find_packages(exclude=('test', 'test.*')),
      package_data = {
        'dlg.apps' : ['dlg_app.h'],
        'dlg.manager' : ['web/*.html', 'web/static/css/*.css', 'web/static/fonts/*', 'web/static/js/*.js', 'web/static/js/d3/*'],
        'dlg.dropmake': ['web/lg_editor.html', 'web/*.css', 'web/*.js', 'web/*.json', 'web/*.map',
                          'web/img/jsoneditor-icons.png', 'web/pg_viewer.html', 'web/matrix_vis.html',
                          'lib/libmetis.*'],
        'test.dropmake': ['logical_graphs/*.json'],
        'test.apps' : ['dynlib_example.c']
      },
      install_requires=install_requires,
      dependency_links=dependency_links,
      extras_require=extra_requires,
      test_suite="test",
      entry_points= {
          'console_scripts':[
              'dlg=dlg.tool:run', # One tool to rule them all
          ],
      }
)
