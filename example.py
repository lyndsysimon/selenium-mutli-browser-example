import os
import re
import unittest
from functools import wraps

from selenium import webdriver


def gotchya(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        self = args[0]
        for d in self.drivers:
            self.driver = d
            f(*args, **kwargs)

    return wrapper


class MetaTestCase(type):
    def __new__(mcs, name, bases, dct):
        tests =  [f for f in dct if re.match('^test_', f)]
        for test in tests:
            dct[test] = gotchya(dct[test])

        return type.__new__(mcs, name, bases, dct)


class ExampleTestCase(unittest.TestCase):

    __metaclass__ = MetaTestCase

    def setUp(self):
        self.drivers = (
            webdriver.Firefox(),
            webdriver.Chrome(
                executable_path=os.path.join(
                    os.path.split(__file__)[0], 'chromedriver'
                )
            ),
        )

    def tearDown(self):
        for driver in self.drivers:
            driver.close()

    def test_google(self):
        self.driver.get('http://google.com')
        import time; time.sleep(1)