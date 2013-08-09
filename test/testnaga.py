from naga import naga
import unittest

class TestOptions(unittest.TestCase):

    def test_options(self):
        pass 

class TestCpu(unittest.TestCase):
    def cpu_base(self, name):
        with open('test/stat/%s.txt' % name, 'rb') as outfile:
            out = outfile.read()
            return naga.cpu(0, out, '')
            
    def test_basic(self):
        level, desc, extra = self.cpu_base('basic')
        self.assertEqual(level, 0.007462686567164179)
        self.assertEqual(desc[0], ('user', 2))
        self.assertEqual(desc[1], ('nice', 0))
        self.assertEqual(desc[2], ('system', 1))
        self.assertEqual(desc[3], ('idle', 399))
        self.assertEqual(desc[4], ('iowait', 0))
        self.assertEqual(desc[5], ('irq', 0))
        self.assertEqual(desc[6], ('softirq', 0))

class TestDisk(unittest.TestCase):
    def test_disk(self):
        pass

class TestFilesystem(unittest.TestCase):
    def test_filesystem(self):
        pass

class TestLoad(unittest.TestCase):
    def test_load(self):
        pass

class TestMemory(unittest.TestCase):
    def test_memory(self):
        pass

class TestUtils(unittest.TestCase):
    def test_finish(self):
        pass
    def test_timecheck(self):
        pass
        

