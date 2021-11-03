import os
import unittest

from dlg import droputils
from dlg.apps.dynlib import DynlibApp
from dlg.ddap_protocol import DROPStates
from dlg.drop import FileDROP
from test.apps.setp_up import build_shared_library

_libname = "dynlib_example"
_libfname = "libdynlib_example.so"
_libpath = os.path.join(os.path.dirname(__file__), 'apps', _libfname)
print(_libpath)
_cfgpath = "/tmp/.dlg/testdata/test_basic_imaging.in"
_normalpath = "/tmp/.dlg/testdata/normal.out"


@unittest.skipUnless(build_shared_library(_libname, _libpath),
                     "Example dynamic library not available")
class PortReferenceDynlibTests(unittest.TestCase):

    def test_index_dynlib(self):
        c = FileDROP('c', 'c', filepath=_cfgpath)  # , nm="Config")
        n = FileDROP('n', 'n', filepath=_normalpath, nm='Normal')
        a = DynlibApp('a', 'a', name="CalcNE", lib=_libpath)
        a.addInput(c)
        a.addOutput(n)
        with droputils.DROPWaiterCtx(self, (c, n, a), 5):
            try:
                c.setCompleted()
            except TypeError:  # Just a place-holder to demonstrate the structure of these tests.
                self.fail("Dynlib failed")
        self.assertEqual(DROPStates.COMPLETED, n.status)
        self.assertEqual(droputils.allDropContents(c), droputils.allDropContents(n))
