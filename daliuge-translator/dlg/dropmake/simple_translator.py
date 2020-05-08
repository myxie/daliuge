#
#    ICRAR - International Centre for Radio Astronomy Research
#    (c) UWA - The University of Western Australia, 2020
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
from datetime import datetime
from time import time

import six

APP = "app"

TEXT = "text"

CATEGORY = "category"
COMMENT_1 = "Comment"
COMPONENT_1 = "Component"
KEY = "key"
LINKS_FROM_ME = "logical_graph_links_from_me"
LINKS_TO_ME = "logical_graph_links_to_me"
MEMORY = "memory"
MEMORY_1 = "Memory"
MKN_1 = "MKN"


class LogicalGraphNode(dict):
    @property
    def key(self):
        return self["key"]


class LogicalGraphLink(dict):
    @property
    def from_node(self):
        return self["from_node"]

    @property
    def from_port(self):
        return self["from_port"]

    @property
    def to_node(self):
        return self["to_node"]

    @property
    def to_port(self):
        return self["to_port"]


def check_must_have_keys(node):
    """
    Are we missing any of the 'must have' keys
    :param node: the node to check
    :return: None or a list of the missing keys
    """
    missing = None
    for key in [CATEGORY, KEY]:
        if key not in node:
            # Create the missing list
            if missing is None:
                missing = list()

            missing.append(key)
    return missing


def build_logical_graph_nodes(node_data_array):
    node_dictionary = dict()
    for node in node_data_array:
        missing_keys = check_must_have_keys(node)
        if missing_keys is not None:
            raise ValueError(
                "The node {} does not have the following keys: {}".format(
                    node, missing_keys
                )
            )

        if node[CATEGORY] == COMMENT_1:
            continue

        node_dictionary[node.key] = LogicalGraphNode(node)

    return node_dictionary


def link_nodes(link_data_array, nodes_dictionary):
    for link in link_data_array:
        logical_graph_link = LogicalGraphLink(
            from_node=nodes_dictionary[link["from"]],
            from_port=link["fromPort"],
            to_node=nodes_dictionary[link["to"]],
            to_port=link["toPort"],
        )
        from_node = logical_graph_link.from_node
        if LINKS_FROM_ME in from_node:
            from_node[LINKS_FROM_ME].append(logical_graph_link)
        else:
            from_node[LINKS_FROM_ME] = [logical_graph_link]

        to_node = logical_graph_link.to_node
        if LINKS_TO_ME in to_node:
            to_node[LINKS_TO_ME].append(logical_graph_link)
        else:
            to_node[LINKS_TO_ME] = [logical_graph_link]


def create_memory_drop(logical_graph_node, timestamp):
    drop = dict(
        oid="{}_{}".format(timestamp, logical_graph_node[KEY]),
        type="plain",
        storage=MEMORY,
        rank=[],
        iid="0",
        lg_key=logical_graph_node[KEY],
        dt=MEMORY,
        nm=MEMORY_1,
    )

    return drop


def get_inputs(logical_graph_node):
    inputs = list()
    if LINKS_TO_ME in logical_graph_node:
        inputs.append()
    return inputs


def get_outputs(logical_graph_node):
    outputs = list()
    if LINKS_FROM_ME in logical_graph_node:
        outputs.append()
    return outputs


def create_component_drop(logical_graph_node, timestamp):
    drop = dict(
        oid="{}_{}".format(timestamp, logical_graph_node[KEY]),
        type=APP,
        app=logical_graph_node,
        storage=MEMORY,
        rank=[],
        iid="0",
        lg_key=logical_graph_node[KEY],
        dt=COMPONENT_1,
        nm=logical_graph_node[TEXT],
    )

    return drop


def create_mkn_drop(logical_graph_node, timestamp):
    drop = dict(oid="{}_{}".format(timestamp, logical_graph_node[KEY]), type=APP,)
    return drop


# Call table
CREATE_DROP = {
    MEMORY: create_memory_drop,
    COMPONENT_1: create_component_drop,
    MKN_1: create_mkn_drop,
}


def build_physical_graph_template_pass1(nodes_dictionary, timestamp):
    drop_dictionary = dict()

    for key, value in six.iteritems(nodes_dictionary):
        drop_dictionary[key] = CREATE_DROP[value[CATEGORY]](value, timestamp)

    return drop_dictionary


def build_physical_graph_template_pass2(nodes_dictionary, drop_dictionary):
    for key, value in six.iteritems(nodes_dictionary):
        drop = drop_dictionary[key]
        # Set up the inputd

    return drop_dictionary


def logical_graph_to_physical_graph_template(logical_graph, timestamp=None):
    """
    Build a physical graph template from a logical graph supplied by EAGLE

    The logical graph is a dictionary of the form:
    {
        "modelData": {
            "fileType": "graph",
            "repoService": "GitHub",
            "repo": "ICRAR/EAGLE_test_repo",
            "filePath": "simple_tests/simple_01_basic.graph",
            "sha": "Dummy",
            "git_url": "Dummy",
        },
        "nodeDataArray": List[Nodes],
        "linkDataArray": List[Links]
    }

    :param logical_graph: the LG from EAGLE
    :param request_form: the request form data
    :param timestamp: the timestamp to use as a basis of the OID. If None now is used.
    :return: the physical graph
    """
    if timestamp is None:
        ts = time()
        timestamp = datetime.fromtimestamp(ts).strftime("%Y-%m-%dT%H:%M:%S")

    nodes_dictionary = build_logical_graph_nodes(logical_graph["nodeDataArray"])
    link_nodes(logical_graph["linkDataArray"], nodes_dictionary)

    # Create the basic nodes
    drop_dictionary = build_physical_graph_template_pass1(nodes_dictionary, timestamp)

    # Add in the links
    drop_dictionary = build_physical_graph_template_pass2(
        nodes_dictionary, drop_dictionary
    )

    physical_graph_template = list()

    return physical_graph_template
