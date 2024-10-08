#
#    ICRAR - International Centre for Radio Astronomy Research
#    (c) UWA - The University of Western Australia, 2015
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

try:
    from importlib.resources import files, as_file
except ModuleNotFoundError:
    from importlib_resources import files

def get_lg_fpath(type, f_name):
    """
    Get the test data file path based on the logical graph name and type of file we want
    :param type: str, type of test data (logical_graph, pickle, pg_spec) we are comparing
    :param f_name: name of the original logical graph created in Eagle
    :return: str, full path of the file
    """
    f_dir = '../../test/dropmake/'

    if type == 'pickle':
        f_name = f_name.split('.')[0] + '.pkl'
        f_dir += type
    elif type == 'pg_spec':
        f_name = f_name.split('.')[0] + '.json'
        f_dir += type
    else:
        f_dir += 'logical_graphs'

    return str(files(__package__) / f"{f_dir}/{f_name}")