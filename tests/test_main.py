import unittest

from app.main import APP_NAME, greeting


class GreetingTest(unittest.TestCase):
    def test_names_the_demo(self):
        self.assertIn(APP_NAME, greeting())

    def test_mentions_the_connector(self):
        self.assertIn("Harness Git connector", greeting())


if __name__ == "__main__":
    unittest.main()
