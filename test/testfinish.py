from naga.naga import NagaExit
from naga import naga
from unittest import TestCase

class TestFinish(TestCase):
    def test_ok(self):
        with self.assertRaises(NagaExit) as cm:
            naga.finish('load', 0.1, 'load is good', '')
        self.assertEqual(cm.exception.code, 0)
    def test_warn_cusp(self):
        with self.assertRaises(NagaExit) as cm:
            naga.finish('load', 1.0, 'load is warning', '')
        self.assertEqual(cm.exception.code, 1)
    def test_warn(self):
        with self.assertRaises(NagaExit) as cm:
            naga.finish('load', 1.1, 'load is warning', '')
        self.assertEqual(cm.exception.code, 1)
    def test_crit(self):
        with self.assertRaises(NagaExit) as cm:
            naga.finish('load', 2.0, 'load is warning', '')
        self.assertEqual(cm.exception.code, 2)
    def test_crit_cusp(self):
        with self.assertRaises(NagaExit) as cm:
            naga.finish('load', 2.1, 'load is warning', '')
        self.assertEqual(cm.exception.code, 2)
    def test_ambiguous(self):
        with self.assertRaises(NagaExit) as cm:
            naga.finish('load', 2.0, 'load is warning', '', 
                    warn=1.0, crit=0.9)
        self.assertEqual(cm.exception.code, 1)
    def test_filesystem_81(self):
        with self.assertRaises(NagaExit) as cm:
            naga.finish('filesystem', 0.81, 'load is good', '')
        self.assertEqual(cm.exception.code, 2)
