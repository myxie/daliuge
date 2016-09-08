#!/usr/bin/python
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
"""
Examples on how to interact with the Drop Island Manager.

This program first converts a logical graph into a physical graph, and then
create a session, appends the physical graph, and deploys the session to execute
the converted physical graph in the Drop Island.
"""

import json
import optparse
import sys

import pkg_resources, logging

from dfms import droputils
from dfms.dropmake.pg_generator import LG, MySarkarPGTP, MetisPGTP
from dfms.manager.client import DataIslandManagerClient


logger = logging.getLogger(__name__)

lgnames = ['lofar_std.json', 'chiles_two.json', 'test_grpby_gather.json', #2
'chiles_two_dev1.json', 'chiles_simple.json', 'mwa_gleam.json', #5
'mwa_gleam_simple.json', 'lofar_std_large.json', 'chiles_two_dev2.json',#8
'lofar_test_2x4.json', 'lofar_test_4x4.json', 'lofar_test_4x8.json',#11
'lofar_test_8x8.json', 'lofar_test_8x16.json', 'lofar_test_16x16.json',#14
'lofar_test_16x32.json', 'lofar_test_32x32.json', 'lofar_test_32x64.json',#17
'lofar_test_64x64.json', 'lofar_test_64x128.json', 'lofar_test_128x128.json',#20
'simple_test_500.json', 'simple_test_1000.json', 'simple_test_2000.json']#23


class MonitorClient(object):

    apps = (
        "test.graphsRepository.SleepApp",
        "test.graphsRepository.SleepAndCopyApp",
    )

    def __init__(self,
                 mhost, mport, timeout=10,
                 algo='sarkar',
                 output=None,
                 zerorun=False,
                 app=None):

        self._host = mhost
        self._port = mport
        self._dc = DataIslandManagerClient(mhost, mport)
        self._algo = algo
        self._zerorun = zerorun
        self._output = output
        self._app = MonitorClient.apps[app] if app else None

    def get_physical_graph(self, graph_id):

        lgn = lgnames[graph_id]
        fp = pkg_resources.resource_filename('dfms.dropmake', 'web/{0}'.format(lgn))  # @UndefinedVariable
        lg = LG(fp)
        logger.info("Start to unroll {0}".format(lgn))
        drop_list = lg.unroll_to_tpl()
        logger.info("Unroll completed for {0} with # of Drops: {1}".format(lgn, len(drop_list)))
        node_list = self._dc.nodes()

        if 'sarkar' == self._algo:
            pgtp = MySarkarPGTP(drop_list, len(node_list), merge_parts=True)
        else:
            pgtp = MetisPGTP(drop_list, len(node_list))

        # Trigering something...
        logger.info("Start to translate {0}".format(lgn))
        pgtp.to_gojs_json(string_rep=False)
        logger.info("Translation completed for {0}".format(lgn))

        pg_spec = pgtp.to_pg_spec(node_list, ret_str=False)
        logger.info("PG spec is calculated!")

        if self._zerorun:
            for dropspec in pg_spec:
                if 'sleepTime' in dropspec:
                    dropspec['sleepTime'] = 0
        app = self._app
        if app:
            for dropspec in pg_spec:
                if 'app' in dropspec['type']:
                    dropspec['app'] = app

        return lgn, lg, pg_spec

    def submit_single_graph(self, graph_id, deploy=False, zerorun=False):

        lgn, lg, pg_spec = self.get_physical_graph(graph_id)

        if self._output:
            with open(self._output, 'w') as f:
                json.dump(pg_spec, f, indent=2)

        def uid_for_drop(dropSpec):
            if 'uid' in dropSpec:
                return dropSpec['uid']
            return dropSpec['oid']

        logger.info("About to compute roots")
        completed_uids = [uid_for_drop(x) for x in droputils.get_roots(pg_spec)]
        logger.info("Len of completed_uids is {0}".format(len(completed_uids)))
        ssid = "{0}-{1}".format(lgn.split('.')[0], lg._session_id)
        self._dc.create_session(ssid)
        logger.info("session {0} created".format(ssid))
        self._dc.append_graph(ssid, pg_spec)
        logger.info("graph {0} appended".format(ssid))

        if (deploy):
            ret = self._dc.deploy_session(ssid, completed_uids=completed_uids)
            logger.info("session {0} deployed".format(ssid))
            return ret

    def write_physical_graph(self, graph_id, tgt="/tmp"):

        lgn, _, pg_spec = self.get_physical_graph(graph_id)

        tof = self._output
        if (self._output is None):
            tof = '{0}/sar_{1}_pgspec.json'.format(tgt, lgn.split('.')[0])

        with open(tof, 'w') as f:
            f.write(pg_spec)


if __name__ == '__main__':

    parser = optparse.OptionParser()
    parser.add_option("-H", "--host", action="store",
                      dest="host", help="The host where the graph will be deployed", default="localhost")
    parser.add_option("-a", "--action", action="store",
                      dest="act", help="action, either 'submit' or 'print'", default="submit")
    parser.add_option("-A", "--algorithm", action="store",
                      dest="algo", help="algorithm used to do the LG --> PG conversion, either 'metis' or 'sarkar'", default="sarkar")
    parser.add_option("-p", "--port", action="store", type="int",
                      dest="port", help="The port we connect to to deploy the graph", default=8001)
    parser.add_option("-g", "--graph-id", action="store", type="int",
                      dest="graph_id", help="The graph to deploy (0 - 7)", default=None)
    parser.add_option("-o", "--output", action="store", type="string",
                      dest="output", help="Where to dump the general physical graph", default=None)
    parser.add_option("-z", "--zerorun", action="store_true",
                      dest="zerorun", help="Generate a physical graph that takes no time to run", default=False)
    parser.add_option("--app", action="store", type="int",
                      dest="app", help="The app to use in the PG. 0=SleepApp (default), 1=SleepAndCopy", default=0)

    (opts, args) = parser.parse_args(sys.argv)

    if opts.graph_id is None:
        parser.error("Missing -g")
    if opts.graph_id >= len(lgnames):
        parser.error("-g must be between 0 and %d" % (len(lgnames),))

    mc = MonitorClient(opts.host, opts.port, output=opts.output)
    if ('submit' == opts.act):
        mc.submit_single_graph(opts.graph_id, deploy=True)
    elif ('print' == opts.act):
        mc.write_physical_graph(opts.graph_id)
    else:
        raise Exception('Unknown action: {0}'.format(opts.act))
