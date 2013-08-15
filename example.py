import os
import re
import unittest
from functools import wraps

from selenium import webdriver

drivers = (
    lambda: webdriver.Firefox(),
    lambda: webdriver.Chrome(
        executable_path=os.path.join(
            os.path.split(__file__)[0], 'chromedriver'
        )
    ),
)


def insert_driver_wrapper(f, driver):
    @wraps(f)
    def wrapper(*args, **kwargs):
        args[0].driver = driver
        try:
            f(*args, **kwargs)
        except Exception as e:
            if len(e.args) is 1:
                e.args = (': '.join((driver.name, e.args[0])),)
            else:
                e.args += (driver.name, )
            raise
        finally:
            args[0].driver.close()
            del args[0].driver

    return wrapper


class MetaTestCase(type):
    def __new__(mcs, name, bases, dct):
        dct['drivers'] = (x() for x in drivers)
        tests = [f for f in dct if re.match('^test_', f)]
        for test in tests:
            for driver in dct['drivers']:
                dct['_'.join([test, driver.name])] = insert_driver_wrapper(dct[test], driver)
            del dct[test]

        return type.__new__(mcs, name, bases, dct)


class ExampleTestCase(unittest.TestCase):

    __metaclass__ = MetaTestCase

    def test_google(self):
        self.driver.get('http://google.com')
        if self.driver.name == 'firefox':
            raise Exception('Test failed.')