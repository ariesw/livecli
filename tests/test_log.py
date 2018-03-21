import unittest

from livecli.logger import Logger
from livecli.compat import is_py2

# Docs says StringIO is suppose to take non-unicode strings
# but it doesn't, so let's use BytesIO instead there...

if is_py2:
    from io import BytesIO as StringIO
else:
    from io import StringIO


class TestSession(unittest.TestCase):
    def setUp(self):
        self.output = StringIO()
        self.manager = Logger()
        self.manager.set_output(self.output)
        self.logger = self.manager.new_module("test")

    def test_level(self):
        self.logger.debug("test")
        self.assertEqual(self.output.tell(), 0)
        self.manager.set_level("debug")
        self.logger.debug("test")
        self.assertNotEqual(self.output.tell(), 0)

        # Test for except ValueError
        with self.assertRaises(AttributeError):
            self.manager.set_level("FalseValue")
            self.logger.FalseValue("test")

    def test_output(self):
        self.manager.set_level("debug")
        self.logger.debug("test")
        self.assertEqual(self.output.getvalue(), "[test][debug] test\n")

    def test_output_error(self):
        self.manager.set_level("error")
        self.logger.error("test")
        self.assertEqual(self.output.getvalue(), "[test][error] test\n")

    def test_output_warning(self):
        self.manager.set_level("warning")
        self.logger.warning("test")
        self.assertEqual(self.output.getvalue(), "[test][warning] test\n")

    def test_prefix(self):
        self.manager.set_prefix("[0]")
        self.manager.set_level("debug")
        self.logger.debug("test")
        self.assertEqual(self.output.getvalue(), "[0][test][debug] test\n")


if __name__ == "__main__":
    unittest.main()
