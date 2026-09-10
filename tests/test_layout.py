"""Executable contract for the public source tree and module entry point."""
from pathlib import Path
import subprocess
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]


class Layout(unittest.TestCase):
    def test_application_sources_and_entrypoint(self):
        self.assertEqual(list(ROOT.glob('*.py')),[])
        self.assertTrue((ROOT/'src/__init__.py').is_file())
        result=subprocess.run([sys.executable,'-m','src.app','--help'],cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn('--data-dir',result.stdout)
