"""
Utilites for accessing the Captricity APIs

NOTE: Methods which start with an underscore (_) are for internal use only and WILL change.
      Do not write your code against them.

"""
import new
import types
import random
import urllib
import httplib 
import urlparse
import traceback
import mimetypes
import simplejson as json
from hashlib import sha256
from urllib import urlencode
from datetime import datetime

API_TOKEN_HEADER_NAME = 'X_API_TOKEN'
API_VERSION_HEADER_NAME = 'X_API_VERSION'
CLIENT_VERSION = '0.01'
USER_AGENT = 'Captricity Python Client %s' % CLIENT_VERSION

def generate_request_access_signature(parameters, secret_key):
    """
    Generate the parameter signature used during third party access requests
    """
    # pull out the parameter keys
    keys = parameters.keys()

    # alphanumerically sort the keys in place
    keys.sort()

    # create an array of url encoded key:value pairs
    encoded_pairs = [urlencode({key:parameters[key]}) for key in keys] 

    # create the serialized parameters in a single, URL style string
    serialized_parameters = '&'.join(encoded_pairs)

    # create the string with the secret key and the parameters which will be hashed
    string_to_hash = '%s:%s' % (secret_key, serialized_parameters)

    # return the hex digest of the hashed string
    return sha256(string_to_hash).hexdigest()

class Client(object):
    """
    A network client for the Captricity third-party API.
    This class will fetch the API description from the endpoint URL and dynamically create methods for accessing the API.
    So, once you instantiate the Client you will be able to call cliend.read_job() even though you won't see that method defined below.

    To see a list of all of the api related methods that this client offers, do the following:
    client = Client('http://host/api/backbone/schreddr', 'your api token')
    client.print_help()
    """
    def __init__(self, endpoint, api_token):
        """
        endpoint must be the full url to the API schema document, like `http://127.0.0.1:8000/api/backbone/schema'
        api_token is the unique string associated with your account's profile which allows API access
        """
        self.api_token = api_token
        self.endpoint = endpoint
        self.parsed_endpoint = urlparse.urlparse(self.endpoint)
        self.api_version = None
        self.schema = self._getJSON(self.parsed_endpoint.path, version=None)
        self.api_version = self.schema['version']

        for resource in self.schema['resources']:
            read_callable = _generate_read_callable(resource['name'], resource['arguments'], resource['regex'], resource['doc'], resource['supported'])
            setattr(self, read_callable.__name__, new.instancemethod(read_callable, self, self.__class__))
            update_callable = _generate_update_callable(resource['name'], resource['arguments'], resource['regex'], resource['doc'], resource['supported'])
            setattr(self, update_callable.__name__, new.instancemethod(update_callable, self, self.__class__))

    def print_help(self):
        """Prints the api method info to stdout for debugging."""
        for resource in dir(self):
            r = getattr(self, resource)
            if not hasattr(r, 'is_api_call'): continue
            if not r.is_api_call: continue
            if not r.is_supported_api: continue
            print r.__name__
            if r.__doc__: print '\t', r.__doc__.strip()

    def _getJSON(self, url, version=None):
        """
        GETs the resource at url, parses it as JSON, and returns the resulting data structure
        """
        if not version: version = self.api_version
        if self.parsed_endpoint.scheme == 'https':
            conn = httplib.HTTPSConnection(self.parsed_endpoint.netloc)
        else:
            conn = httplib.HTTPConnection(self.parsed_endpoint.netloc)
        head = {
            "Accept" : "application/json",
            "User-Agent": USER_AGENT,
            API_TOKEN_HEADER_NAME: self.api_token,
        }
        if version: head[API_VERSION_HEADER_NAME] = version
        conn.request("GET", url, "", head)
        resp = conn.getresponse()
        if resp.status != 200: raise IOError('GET response from %s was %s' % (url, resp.status))
        return json.loads(resp.read())

    def _getData(self, url, version=None, accept=None):
        """
        GETs the resource at url and returns the raw response
        If the accept parameter is not None, the request passes is as the Accept header
        """
        if not version: version = self.api_version
        if self.parsed_endpoint.scheme == 'https':
            conn = httplib.HTTPSConnection(self.parsed_endpoint.netloc)
        else:
            conn = httplib.HTTPConnection(self.parsed_endpoint.netloc)
        head = {
            "User-Agent": USER_AGENT,
            API_TOKEN_HEADER_NAME: self.api_token,
        }
        if accept: head['Accept'] = accept
        if version: head[API_VERSION_HEADER_NAME] = version
        conn.request("GET", url, "", head)
        resp = conn.getresponse()
        if resp.status != 200: raise IOError('GET response from %s was %s' % (url, resp.status))
        return resp.read()

    def _putMultipart(self, url, data):
        """
        encodes the data as a multipart form and PUTs to the url
        the response is parsed as JSON and the returns the resulting data structure
        """
        fields = []
        files = []
        for key, value in data.items():
            if type(value) == file:
                files.append((key, value.name, value.read()))
            else:
                fields.append((key, value))
        content_type, body = _encode_multipart_formdata(fields, files)
        if self.parsed_endpoint.scheme == 'https':
            h = httplib.HTTPS(self.parsed_endpoint.netloc)
        else:
            h = httplib.HTTP(self.parsed_endpoint.netloc)
        h.putrequest('PUT', url)
        h.putheader('Content-Type', content_type)
        h.putheader('Content-Length', str(len(body)))
        h.putheader('Accept', 'application/json')
        h.putheader('User-Agent', USER_AGENT)
        h.putheader(API_TOKEN_HEADER_NAME, self.api_token)
        h.putheader(API_VERSION_HEADER_NAME, self.api_version)
        h.endheaders()
        h.send(body)
        errcode, errmsg, headers = h.getreply()
        if errcode != 200: raise IOError('PUT response from %s was %s' % (url, errcode))
        return json.loads(h.file.read())

    def _putJSON(self, url, data):
        """
        urlencodes the data and PUTs it to the url
        the response is parsed as JSON and the resulting data type is returned
        """
        if self.parsed_endpoint.scheme == 'https':
            conn = httplib.HTTPSConnection(self.parsed_endpoint.netloc)
        else:
            conn = httplib.HTTPConnection(self.parsed_endpoint.netloc)
        head = {
            "Content-Type" : "application/x-www-form-urlencoded",
            "Accept" : "application/json",
            "User-Agent": USER_AGENT,
            API_TOKEN_HEADER_NAME: self.api_token,
            API_VERSION_HEADER_NAME: self.api_version,
        }
        conn.request("PUT", url, urllib.urlencode(data), head)
        resp = conn.getresponse()
        if resp.status != 200: raise IOError('PUT response from %s was %s' % (url, resp.status))
        return json.loads(resp.read())

    def _generate_url(self, regex, arguments):
        """
        Uses the regex (of the type defined in Django's url patterns) and the arguments to return a relative URL
        For example, if the regex is '^/api/shreddr/job/(?P<id>[\d]+)$' and arguments is ['23'] then return would be '/api/shreddr/job/23'
        """
        regex_tokens = _split_regex(regex)
        result = ''
        for i in range(len(arguments)):
            result = result + str(regex_tokens[i]) + str(arguments[i])
        if len(regex_tokens) > len(arguments): result += regex_tokens[-1]
        return result
        #return '%s://%s/%s' % (self.parsed_endpoint.scheme, self.parsed_endpoint.netloc, result)

def parse_date_string(date_string):
    """Converts the date strings created by the API (e.g. '2012-04-06T19:11:33.032') and returns an equivalent datetime instance."""
    return datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%S.%f")


def _encode_multipart_formdata(fields, files):
    """
    Create a multipart encoded form for use in PUTing and POSTing.

    fields is a sequence of (name, value) elements for regular form fields.
    files is a sequence of (name, filename, value) elements for data to be uploaded as files
    Return (content_type, body) ready for httplib.HTTP instance
    """
    BOUNDARY = '----------A_vEry_UnlikelY_bouNdary_$'
    CRLF = '\r\n'
    L = []
    for (key, value) in fields:
        L.append('--' + BOUNDARY)
        L.append('Content-Disposition: form-data; name="%s"' % key)
        L.append('')
        L.append(value)
    for (key, filename, value) in files:
        L.append('--' + BOUNDARY)
        L.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename))
        L.append('Content-Type: %s' % get_content_type(filename))
        L.append('')
        L.append(value)
    L.append('--' + BOUNDARY + '--')
    L.append('')
    body = CRLF.join(L)
    content_type = 'multipart/form-data; boundary=%s' % BOUNDARY
    return content_type, body

def get_content_type(filename):
    """Use the python mimetypes to determine a mime type, or return application/octet-stream"""
    return mimetypes.guess_type(filename)[0] or 'application/octet-stream'

def _generate_read_callable(name, arguments, regex, doc, supported):
    """Returns a callable which conjures the URL for the resource and GETs a response"""
    def f(self, *args, **kwargs):
        url = self._generate_url(regex, args)
        if 'params' in kwargs: url += "?" + urllib.urlencode(kwargs['params'])
        if 'accept' in kwargs: return self._getData(url, accept=kwargs['accept'])
        return self._getJSON(url)
    f.__name__ = 'read_%s' % name
    f.__doc__ = doc
    f.is_api_call = True
    f.is_supported_api = supported
    return f

def _generate_update_callable(name, arguments, regex, doc, supported):
    """Returns a callable which conjures the URL for the resource and PUTs data"""
    def f(self, *args, **kwargs):
        for key, value in args[-1].items():
            if type(value) == file:
                return self._putMultipart(self._generate_url(regex, args[:-1]), args[-1])
        return self._putJSON(self._generate_url(regex, args[:-1]), args[-1])
    f.__name__ = 'update_%s' % name
    f.__doc__ = doc
    f.is_api_call = True
    f.is_supported_api = supported
    return f

def _split_regex(regex):
    """
    Return an array of the URL split at each regex match like (?P<id>[\d]+)
    Call with a regex of '^/foo/(?P<id>[\d]+)/bar/$' and you will receive ['/foo/', '/bar/']
    """
    if regex[0] == '^': regex = regex[1:]
    if regex[-1] == '$': regex = regex[0:-1]
    results = []
    line = ''
    for c in regex:
        if c == '(':
            results.append(line)
            line = ''
        elif c == ')':
            line = ''
        else:
            line = line + c
    if len(line) > 0: results.append(line)
    return results
