from naga.naga import NagaExit
from naga import naga
from unittest import TestCase

class TestOptions(TestCase):

    def test_options(self):
        pass 

def run_info(info, name):
    """ Get sample output file and use it for input to naga info method"""
    with open('test/static/%s_%s.txt' % (info, name), 'rb') as outfile:
        out = outfile.read()
        return getattr(naga, info)(out)

class TestCpu(TestCase):
            
    def test_basic(self):
        """Test cpu(..)"""
        level, desc, extra = run_info('cpu', 'basic')
        self.assertEqual(extra, '')
        self.assertAlmostEqual(level, 0.00746268656716)
        self.assertEqual(len(desc), 8)
        
        self.assertEqual(desc[0][0], 'cpu')
        self.assertEqual(desc[1][0], 'user')
        self.assertEqual(desc[2][0], 'nice')
        self.assertEqual(desc[3][0], 'system')
        self.assertEqual(desc[4][0], 'idle')
        self.assertEqual(desc[5][0], 'iowait')
        self.assertEqual(desc[6][0], 'irq')
        self.assertEqual(desc[7][0], 'softirq')

        self.assertAlmostEqual(desc[0][1], 0.00746, 5)
        self.assertAlmostEqual(desc[1][1], 0.00498, 5)
        self.assertAlmostEqual(desc[2][1], 0.0)
        self.assertAlmostEqual(desc[3][1], 0.00249, 5)
        self.assertAlmostEqual(desc[4][1], 0.99254, 5)
        self.assertAlmostEqual(desc[5][1], 0.0)
        self.assertAlmostEqual(desc[6][1], 0.0)
        self.assertAlmostEqual(desc[7][1], 0.0)

class TestDisk(TestCase):

    def test_basic(self):
        """Test disk(..)"""
        level, desc, extra = run_info('disk', 'basic')
        self.assertEqual(level, 10)
        self.assertEqual(desc, 'in_persec=5MB;out_persec=5MB')

class TestFilesystem(TestCase):
    """ Collection of tests for filesystem(..)"""

    def test_basic(self):
        """Test filesystem, basic"""
        level, desc, extra = run_info('filesystem', 'basic')
        self.assertAlmostEqual(level, 0.208, places=3)
        self.assertEqual(len(desc), 4)
        self.assertEqual(extra, 'on /')
        self.assertEqual(desc[0], ("'/'", '/dev/sdd5;115065400;23939856'))
        self.assertEqual(desc[1], ("'/mnt/bigdisk'", "/dev/sdc1;2884152536;1472177232"))
        self.assertEqual(desc[2], ("'/media/david/d5fd6b6e-c3fb-4399-bee7-8ae6bfe985ba'", 
            "/dev/md1;952912348;521857176"))
        self.assertEqual(desc[3], ("'/mnt/backup'", "/dev/md1;952912348;521857176"))

    def test_redhat(self):
        """Test filesystem on redhat"""
        level, desc, extra = run_info('filesystem', 'redhat')
        self.assertAlmostEqual(level, 0.325, places=3)
        self.assertEqual(len(desc), 1)
        self.assertEqual(extra, 'on /')
        self.assertEqual(desc[0], ("'/'", '/dev/sda1;286449848;93215152'))

    def test_hpux(self):
        """Test filesystem on HP-UX"""
        level, desc, extra = run_info('filesystem', 'hpux')
        self.assertEqual(len(desc), 6)

    def test_darwin(self):
        """Test filesystem on darwin / XServe"""
        level, desc, extra = run_info('filesystem', 'darwin')
        self.assertAlmostEqual(level, 0.132, places=3)
        self.assertEqual(len(desc), 2)

class TestLoad(TestCase):
    """ Collection of tests for load(..)"""

    def test_basic(self):
        """Test load(..)"""
        level, desc, extra = run_info('load', 'basic')
        self.assertAlmostEqual(level, 0.095, places=3)
        self.assertEqual(extra, 'x 2 cores')
        self.assertEqual(len(desc), 4)
        self.assertEqual(desc[0], ('load1', '0.19', '', 0, 2))
        self.assertEqual(desc[1], ('load5', '0.22'))
        self.assertEqual(desc[2], ('load15', '0.30'))
        self.assertEqual(desc[3], ('running', '4'))

class TestMemory(TestCase):
    """ Collection of tests for memory(..)"""

    def test_basic(self):
        """Test memory(..)"""
        level, desc, extra = run_info('memory', 'basic')
        self.assertAlmostEqual(level, 0.475, places=3)
        self.assertEqual(extra, '')
        self.assertEqual(len(desc), 6)
        self.assertEqual(desc[0], ('total', 7960))
        self.assertEqual(desc[1], ('used', 3780))
        self.assertEqual(desc[2], ('free', 4180))
        self.assertEqual(desc[3], ('shared', 0))
        self.assertEqual(desc[4], ('buff', 475))
        self.assertEqual(desc[5], ('cache', 2718))

class TestNetwork(TestCase):
    """ Collection of tests for network(..)"""

    def test_basic(self):
        """Test network(..)"""
        level, desc, extra = run_info('network', 'basic')
        self.assertAlmostEqual(level, 0.668, places=3)
        self.assertEqual(extra, 'on eth4')
        self.assertEqual(len(desc), 6)
        self.assertEqual(desc[0], ('eth4_rx', 581222))
        self.assertEqual(desc[1], ('eth4_tx', 118789))
        self.assertEqual(desc[2], ('lo_rx', 536))
        self.assertEqual(desc[3], ('lo_tx', 344))
        self.assertEqual(desc[4], ('rename3_rx', 0))
        self.assertEqual(desc[5], ('rename3_tx', 0))

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

                
class TestFormatNum(TestCase):
    def test_basic(self):
        fmn = naga.format_num
        self.assertEqual(fmn(13), '13')
        self.assertEqual(fmn(123), '123')
        self.assertEqual(fmn(1234), '1234')
        self.assertEqual(fmn('foo'), 'foo')
        self.assertEqual(fmn(0.042642), '0.04')
        self.assertEqual(fmn(13424L), '13424')

    
class TestTimecheck(TestCase):
    def test_timecheck(self):
        pass
        

