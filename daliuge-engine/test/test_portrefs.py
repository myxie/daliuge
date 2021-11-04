import os
import unittest

from dlg import droputils
from dlg.apps.dynlib import DynlibApp
from dlg.ddap_protocol import DROPStates
from dlg.drop import InMemoryDROP
from test.apps.setp_up import build_shared_library

_libname = "dynlib_named_example"
_libfname = "libdynlib_named_example.so"
_libpath = os.path.join(os.path.dirname(__file__), 'apps', _libfname)
_cfgpath = os.path.join(os.path.dirname(__file__), 'apps', 'data', 'test.in')
_normalpath = "/tmp/.dlg/testdata/normal.out"


@unittest.skipUnless(build_shared_library(_libname, _libpath),
                     "Example dynamic library not available")
class PortReferenceDynlibTests(unittest.TestCase):

    def test_named(self):
        a = InMemoryDROP('a', 'a', filepath=_cfgpath, nm="named_input")
        c = InMemoryDROP('c', 'c', filepath=_normalpath, nm='named_output')
        b = DynlibApp('b', 'b', name="CalcNE", lib=_libpath)
        b.addInput(a)
        b.addOutput(c)
        with droputils.DROPWaiterCtx(self, (a, b, c), 10):
            a.write(os.urandom(32))
            a.setCompleted()
        self.assertEqual(DROPStates.COMPLETED, c.status)
        self.assertEqual(droputils.allDropContents(a), droputils.allDropContents(c))

