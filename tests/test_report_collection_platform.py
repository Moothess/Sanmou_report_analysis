import importlib
import unittest


class ReportCollectionPlatformTest(unittest.TestCase):
    def test_non_windows_platform_has_clear_error(self):
        module = importlib.import_module("sanmou_report_analysis.report_collection")
        with self.assertRaises(RuntimeError) as ctx:
            module.ensure_capture_supported_platform("darwin")
        self.assertIn("Windows", str(ctx.exception))
        self.assertIn("report_analysis", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
