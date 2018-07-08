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
"""
agent - resources (e.g. machines)
task - the task to be allocated
orders - dict {agent: [tasks-run-on-agent-in-order]}
usages - dict {agent: array-of-usage-at-each-time-step}
taskson - dict {task: agent-on-which-task-is-run}
prec - dict {task: (tasks which directly precede task)}
succ - dict {task: (tasks which directly succeed task)}
compcost - function :: task, agent -> time to compute task on agent
commcost - function :: task, task, agent, agent -> time to transfer results
                       of one task needed by another between two agents
"""

from functools import partial
from collections import namedtuple
from itertools import chain
import itertools as it
#import networkx as nx
import numpy as np


Event = namedtuple('Event', 'task start end')

class res_usage(object):
    """
    Resource usage of a particular machine/agent
    """
    def __init__(self, agent, supply):
        self.agent = agent
        self.supply = supply
        self.edt = -1
        self.arr = None

    def can_allocate_task(self, desired_st_time, duration, demand):
        if (self.edt == -1):
            return True
        dedt = min(desired_st_time + duration, self.edt)
        # each timestep should not exceed supply
        return sum(self.arr[desired_st_time:dedt] + demand > self.supply) == 0

    def add_task(self, event, demand):
        self.edt = max(event.end, self.edt)
        if (self.arr is None):
            self.arr = np.zeros(self.edt)
        elif (self.arr.size < self.edt):
            delt = self.edt - self.arr.size
            self.arr = np.hstack([self.arr, np.zeros(delt)])
        self.arr[event.start:event.end] += demand

def reverse_dict(d):
    """ Reverses direction of dependence dict

    >>> d = {'a': (1, 2), 'b': (2, 3), 'c':()}
    >>> reverse_dict(d)
    {1: ('a',), 2: ('a', 'b'), 3: ('b',)}
    """
    result = {}
    for key in d:
        for val in d[key]:
            result[val] = result.get(val, tuple()) + (key, )
    return result

def find_task_event(task_name, orders_dict):
    for event in it.chain.from_iterable(orders_dict.values()):
        if event.task == task_name:
            return event


def wbar(ni, agents, compcost):
    """ Average computation cost """
    return sum(compcost(ni, agent) for agent in agents) / len(agents)


def cbar(ni, nj, agents, commcost):
    """ Average communication cost """
    n = len(agents)
    if n == 1:
        return 0
    npairs = n * (n - 1)
    return 1. * sum(commcost(ni, nj, a1, a2) for a1 in agents for a2 in agents
                    if a1 != a2) / npairs


def ranku(ni, agents, succ,  compcost, commcost):
    """ Rank of task

    This code is designed to mirror the wikipedia entry.
    Please see that for details

    [1]. http://en.wikipedia.org/wiki/Heterogeneous_Earliest_Finish_Time
    """
    rank = partial(ranku, compcost=compcost, commcost=commcost,
                   succ=succ, agents=agents)
    w = partial(wbar, compcost=compcost, agents=agents)
    c = partial(cbar, agents=agents, commcost=commcost)

    if ni in succ and succ[ni]:
        return w(ni) + max(c(ni, nj) + rank(nj) for nj in succ[ni])
    else:
        return w(ni)


def endtime(task, events):
    """ Endtime of task in list of events """
    for e in events:
        if e.task == task:
            return e.end


def find_first_gap(agent_orders, desired_start_time, duration, supply, demand):
    """Find the first gap in an agent's list of tasks

    Essentially this is equivalent to "sequentialisation"
    But for DAG-preserving, such sequentialisation does not work since the execution
    will be triggered as soon as the `desired_start_time` arrives regardless of
    scheduling decisions (insertion into some gap slots)

    So the actual start time cannot be after the desired_start time, it must be
    at the desired_start_time. This is the main difference from the original HEFT.

    This means if the task cannot run at the desired_start_time (i.e. No gaps found)
    due to resource depletion (e.g. DoP overflow), then the agent has to either
    reject the task or face the consequence of resource over-subscription, or
    ask for creating a new resource unit for that task

    The gap must be after `desired_start_time` and of length at least
    `duration`.
    """
    #TODO change to a "DAG preserved" first gap
    #TODO return an infinite large value if the DoP constraint is not met

    # No tasks: can fit it in whenever the task is ready to run
    if (agent_orders is None) or (len(agent_orders)) == 0:
        return desired_start_time

    # Try to fit it in between each pair of Events, but first prepend a
    # dummy Event which ends at time 0 to check for gaps before any real
    # Event starts.
    a = chain([Event(None, None, 0)], agent_orders[:-1])
    for e1, e2 in zip(a, agent_orders):
        earliest_start = max(desired_start_time, e1.end)
        if e2.start - earliest_start > duration:
            return earliest_start

    # No gaps found: put it at the end, or whenever the task is ready
    return max(agent_orders[-1].end, desired_start_time)


def start_time(task, orders, taskson, prec, commcost, compcost,
               usages, workload, agent):
    """ Earliest time that task can be executed on agent """

    duration = compcost(task, agent)

    if task in prec:
        comm_ready = max([endtime(p, orders[taskson[p]])
                          + commcost(p, task, taskson[p], agent) for p in prec[task]])
    else:
        comm_ready = 0

    return find_first_gap(orders[agent], comm_ready, duration,
                          usages[agent], workload[task])


def allocate(task, orders, taskson, prec, compcost, commcost, usages, workload):
    """ Allocate task to the machine with earliest finish time

    capacity is a dictionary, key is agent id, and value is capacity (integer)
    workload is a dictionary, key is task id, and value is workload (integer)

    """
    st = partial(start_time, task, orders, taskson, prec, commcost, compcost,
                 usages, workload)

    def ft(machine): return st(machine) + compcost(task, machine)

    # 'min()' represents 'earliest' finished time (ft)
    # this is exactly why the allocation policy is considered greedy!
    #TODO the new greediness should be based on "DoP" since all start time will be
    # the same (the desired_start_time). Smaller DoP (or bigger leftover) is better
    agent = min(orders.keys(), key=ft)
    start = st(agent)
    end = ft(agent)
    #assert(end == start + compcost(task, agent))

    orders[agent].append(Event(task, start, end))
    #orders[agent] = sorted(orders[agent], key=lambda e: e.start)
    orders[agent].sort(key=lambda e: e.start)
    # Might be better to use a different data structure to keep each
    # agent's orders sorted at a lower cost.

    taskson[task] = agent


def makespan(orders):
    """ Finish time of last task """
    return max(v[-1].end for v in orders.values() if v)


def schedule(succ, agents, compcost, commcost, capacity, workload):
    """ Schedule computation dag onto worker agents

    inputs:

    succ - DAG of tasks {a: (b, c)} where b, and c follow a
    agents - set of agents that can perform work
    compcost - function :: task, agent -> runtime
    commcost - function :: j1, j2, a1, a2 -> communication time
    """
    rank = partial(ranku, agents=agents, succ=succ,
                   compcost=compcost, commcost=commcost)
    prec = reverse_dict(succ)

    tasks = set(succ.keys()) | set(x for xx in succ.values() for x in xx)
    tasks = sorted(tasks, key=rank)

    orders = {agent: [] for agent in agents}
    usages = {agent: res_usage(agent, supply) for agent, supply in zip(agents, capacity)}
    taskson = dict()
    for task in reversed(tasks):
        allocate(task, orders, taskson, prec, compcost, commcost, usages, workload)

    return orders, taskson