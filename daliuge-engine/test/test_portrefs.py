import os
import unittest

from dlg import droputils
from dlg.apps.dynlib import DynlibApp
from dlg.ddap_protocol import DROPStates
from dlg.drop import InMemoryDROP
from test.apps.setp_up import build_shared_library


def _gen_libfname(libname):
    return f"lib{libname}.so"


_libname_single = "dynlib_named_example"
_libfname_single = _gen_libfname(_libname_single)
_libpath_single = os.path.join(os.path.dirname(__file__), 'apps', _libfname_single)

_libname_double = "dynlib_namedmultiple_example"
_libfname_double = _gen_libfname(_libname_double)
_libpath_double = os.path.join(os.path.dirname(__file__), 'apps', _libfname_double)


@unittest.skipUnless(build_shared_library(_libname_single, _libpath_single),
                     "Example dynamic library not available")
@unittest.skipUnless(build_shared_library(_libname_double, _libpath_double),
                     "Second example dynamic library not available")
class PortReferenceDynlibTests(unittest.TestCase):

    def _run_simple_chain(self, a, b, c):
        b.addInput(a)
        b.addOutput(c)
        with droputils.DROPWaiterCtx(self, (a, b, c), 10):
            a.write(os.urandom(32))
            a.setCompleted()

    def test_previous_example(self):
        """
        This example relies on the pre-existing port finding behaviour.
        This test is here during development to see precisely when the old behaviour is broken.
        """
        a = InMemoryDROP('a', 'a', nm="named_input")
        c = InMemoryDROP('c', 'c', nm="named_output")
        b = DynlibApp('b', 'b', name="Test", lib=_libpath_single)
        self._run_simple_chain(a, b, c)
        self.assertEqual(DROPStates.COMPLETED, c.status)
        self.assertEqual(droputils.allDropContents(a), droputils.allDropContents(c))

    def test_previous_example_multiple_ports(self):
        """
        This example relies on the pre-existing port finding behaviour.
        However, this test uses two out-of-order input/output ports
        """
        a1 = InMemoryDROP('a1', 'a1', nm="named_first_input")
        a2 = InMemoryDROP('a2', 'a2', nm="named_second_input")
        c1 = InMemoryDROP('c1', 'c1', nm="named_first_output")
        c2 = InMemoryDROP('c2', 'c2', nm="named_second_output")
        b = DynlibApp('b', 'b', name="Test", lib=_libpath_double)
        b.addInput(a2)
        b.addInput(a1)
        b.addOutput(c1)
        b.addOutput(c2)
        with droputils.DROPWaiterCtx(self, (a1, a2, b, c1, c2), 10):
            first_data = os.urandom(32)
            second_data = os.urandom(32)
            while first_data == second_data:
                second_data = os.urandom(32)
            a1.write(first_data)
            a1.setCompleted()
            a2.write(second_data)
            a2.setCompleted()
        self.assertEqual(DROPStates.COMPLETED, c1.status)
        self.assertEqual(DROPStates.COMPLETED, c2.status)
        self.assertNotEqual(first_data, second_data)
        self.assertEqual(droputils.allDropContents(a1), droputils.allDropContents(c1))
        self.assertEqual(droputils.allDropContents(a2), droputils.allDropContents(c2))
