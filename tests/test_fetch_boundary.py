"""Offline regression tests for the extraction-only client boundary."""
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import main


class FetchBoundaryTests(unittest.TestCase):
    def test_help_only_exposes_fetch(self):
        result = subprocess.run([sys.executable, str(ROOT / 'main.py'), '--help'],
                                cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn('fetch', result.stdout)
        self.assertNotIn('predict', result.stdout)

    def test_prediction_command_is_rejected(self):
        result = subprocess.run([sys.executable, str(ROOT / 'main.py'), 'predict', 'ltv'],
                                cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)

    def test_fetch_still_calls_engine_and_exporter(self):
        engine = Mock()
        engine.fetch.return_value = [{'header': ['value'], 'rows': [[1]]}]
        with patch.object(main, 'get_engine', return_value=engine), \
             patch.object(main, 'export_data', return_value=['offline.csv']) as export, \
             patch.object(main, 'send_emails') as mail:
            result = main.run_fetch_task({'name': 'offline', 'engine': 'ta',
                'region': 'global', 'sql': 'SELECT 1 AS value', 'formats': ['csv'],
                'show': False, 'mailto': ''})
            engine.fetch.assert_called_once_with('SELECT 1 AS value', headless=True)
            export.assert_called_once()
            mail.assert_not_called()
            self.assertIs(result, engine.fetch.return_value)


if __name__ == '__main__':
    unittest.main()
