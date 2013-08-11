from naga.naga import NagaExit
from naga import naga
from unittest import TestCase

class TestOptions(TestCase):

    def test_options(self):
        pass 

class TestCpu(TestCase):
    def cpu_base(self, name):
        with open('test/static/cpu_%s.txt' % name, 'rb') as outfile:
            out = outfile.read()
            return naga.cpu(0, out, '')
            
    def test_basic(self):
        """Test cpu(..)"""
        level, desc, extra = self.cpu_base('basic')
        self.assertEqual(level, 0.007462686567164179)
        self.assertEqual(desc[0], ('user', 2))
        self.assertEqual(desc[1], ('nice', 0))
        self.assertEqual(desc[2], ('system', 1))
        self.assertEqual(desc[3], ('idle', 399))
        self.assertEqual(desc[4], ('iowait', 0))
        self.assertEqual(desc[5], ('irq', 0))
        self.assertEqual(desc[6], ('softirq', 0))
        self.assertEqual(extra, '')

class TestDisk(TestCase):
    def disk_base(self, name):
        """ Get sample output file and use it for input to disk(..)"""
        with open('test/static/disk_%s.txt' % name, 'rb') as outfile:
            out = outfile.read()
            return naga.disk(0, out, '')

    def test_basic(self):
        """Test disk(..)"""
        level, desc, extra = self.disk_base('basic')
        self.assertEqual(level, 10)
        self.assertEqual(desc, 'mb_in=5;mb_out=5')

class TestFilesystem(TestCase):
    def test_filesystem(self):
        pass

class TestLoad(TestCase):
    def test_load(self):
        pass

class TestMemory(TestCase):
    def test_memory(self):
        pass

class TestFinish(TestCase):
    def test_ok(self):
        with self.assertRaises(NagaExit) as cm:
            naga.finish('load', 0.1, 'load is good', '')
        self.assertEqual(cm.exception.status, 0)
    def test_warn_cusp(self):
        with self.assertRaises(NagaExit) as cm:
            naga.finish('load', 1.0, 'load is warning', '')
        self.assertEqual(cm.exception.status, 1)
    def test_warn(self):
        with self.assertRaises(NagaExit) as cm:
            naga.finish('load', 1.1, 'load is warning', '')
        self.assertEqual(cm.exception.status, 1)
    def test_crit(self):
        with self.assertRaises(NagaExit) as cm:
            naga.finish('load', 2.0, 'load is warning', '')
        self.assertEqual(cm.exception.status, 2)
    def test_crit_cusp(self):
        with self.assertRaises(NagaExit) as cm:
            naga.finish('load', 2.1, 'load is warning', '')
        self.assertEqual(cm.exception.status, 2)
    def test_ambiguous(self):
        with self.assertRaises(NagaExit) as cm:
            naga.finish('load', 2.0, 'load is warning', '', 
                    warn=1.0, crit=0.9)
        self.assertEqual(cm.exception.status, 1)

                
    
class TestTimecheck(TestCase):
    def test_timecheck(self):
        pass
        

