import os
import re
import unittest
from functools import wraps

from selenium import webdriver

from status import set_test_status


def remote_test(desired_capabilities):
    """ Given a dict of desired capabilities, return a WebDriver instance of
    that type.

    Note that capabilities lists may be found in
    ``selenium.webdriver.DesiredCapabilities``.
    """
    cfg = desired_capabilities
    cfg['platform'] = 'Windows 7'
    cfg['name'] = 'Selenium-Multi Test'
    cfg['command-timeout'] = 15

    wd = webdriver.Remote(
        desired_capabilities=cfg,
        command_executor="http://{user}:{key}@{host}/wd/hub".format(
            user=os.environ['saucelabs_user'],
            key=os.environ['saucelabs_key'],
            host='ondemand.saucelabs.com:80'
        )
    )
    wd._is_sauce = True

    return wd


def remote_chrome():
    return remote_test(webdriver.DesiredCapabilities.CHROME)


def remote_firefox():
    return remote_test(webdriver.DesiredCapabilities.FIREFOX)


def remote_ie():
    return remote_test(webdriver.DesiredCapabilities.INTERNETEXPLORER)

# The list of drivers to iterate over for each test.
# Note that the ``.name`` of each driver must be unique, in order to generate
# an appropriate test name.
drivers = (
    # These are specified as lambdas because we need to create a new one for
    # each test.
    # lambda: webdriver.Firefox(),
    # lambda: webdriver.Chrome(
    #     executable_path=os.path.join(
    #         os.path.split(__file__)[0], 'chromedriver'
    #     )
    # ),
    remote_chrome,
    remote_firefox,
    remote_ie,
)


def insert_driver_wrapper(f, driver):
    """ Decorator for test cases to inject the passed driver to the test's
    parent class, prior to the test being run.

    Note that when this is applied, it effectively acts as an additional
    ``setUp()`` and ``tearDown()`` method for the test.

    :param f: the callable to be wrapped
    :param driver: the driver to assign to the ``driver`` attribute of the
        ``self`` argument to ``f``

    :return: decorated callable
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        # TODO: Allow the end user to specify their own driver_setUp() and
        #   driver_tearDown() to use in place of the default logic here.

        # ``self`` is always going to be the first argument passed to the test
        # method.

        # set self.driver of the callable to an instance of the driver
        args[0].driver = driver()
        try:
            # execute the test method
            f(*args, **kwargs)
            # If this is a Sauce driver, tell them it passed.
            if args[0].driver.__dict__.get('_is_sauce'):
                set_test_status(args[0].driver.session_id, True)
        except Exception as e:
            # if an exception is raised, modify the message to include
            if len(e.args) is 1:
                e.args = (': '.join((args[0].driver.name, e.args[0])),)
            else:
                e.args += (args[0].driver.name, )
            # If this is a Sauce driver, tell them it failed.
            if args[0].driver.__dict__.get('_is_sauce'):
                set_test_status(args[0].driver.session_id, False)
            raise
        finally:
            args[0].driver.quit()
            del args[0].driver
    return wrapper


class MetaTestCase(type):
    """Metaclass for ``unittest.Testcase`` objects.

    Iterates over defined tests and creates new test methods for each of the
    drivers specified

    """
    def __new__(mcs, name, bases, dct):
        dct['drivers'] = drivers
        # get all callable attributes named beginning with "test_"
        tests = [f for f in dct if re.match('^test_', f) and callable(dct[f])]
        for test in tests:
            for idx, driver in enumerate(dct['drivers']):
                suffix = str(idx)
                # try:
                #     suffix = str(driver.name)
                # except AttributeError:
                #     suffix = str(idx)
                name = str('_'.join([test, suffix]))
                dct[name] = insert_driver_wrapper(dct[test], driver)
                dct[name].__name__ = name
            del dct[test]

        return type.__new__(mcs, name, bases, dct)


class MultiDriverTestCase(unittest.TestCase):

    __metaclass__ = MetaTestCase

    _multiprocess_can_split_ = True

    def test_google(self):
        self.driver.get('http://google.com')
        # if self.driver.name == 'firefox':
        #     raise Exception('Test failed.')
        self.assertTrue(True)

if __name__ == '__main__':
    unittest.main()