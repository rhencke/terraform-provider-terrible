import sys
import subprocess
import unittest
from pathlib import Path


class ExampleScriptTest(unittest.TestCase):
    FILE = Path("/tmp/ansible_provider_example.txt")

    def setUp(self):
        if self.FILE.exists():
            self.FILE.unlink()

    def test_run_example_creates_expected_file(self):
        subprocess.check_call([sys.executable, "examples/run_example.py"])        
        self.assertTrue(self.FILE.exists(), "Example output file was not created")
        content = self.FILE.read_text()
        self.assertIn("Managed by the terrible Ansible Terraform provider example", content)

    def tearDown(self):
        if self.FILE.exists():
            self.FILE.unlink()


if __name__ == "__main__":
    unittest.main()
