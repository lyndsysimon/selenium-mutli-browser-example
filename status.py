#
# https://gist.github.com/santiycr/1644439

import httplib
import base64
try:
    import json
except ImportError:
    import simplejson as json

config = {"username": "LyndsySimon",
          "access-key": "fe40508d-0102-46a1-81a3-b2a039132527"}

base64string = base64.encodestring('%s:%s' % (config['username'], config['access-key']))[:-1]

def set_test_status(jobid, passed=True):
    body_content = json.dumps({"passed": passed})
    connection =  httplib.HTTPConnection("saucelabs.com")
    connection.request('PUT', '/rest/v1/%s/jobs/%s' % (config['username'], jobid),
                       body_content,
                       headers={"Authorization": "Basic %s" % base64string})
    result = connection.getresponse()
    return result.status == 200