import os
import json
import unittest
import dumptruck
from dumptruck_web import api

BOXHOME = os.path.join('/', 'tmp', 'boxtests') 
JACK = os.path.join(BOXHOME, 'jack-in-a')
try:
    os.makedirs(JACK)
except OSError:
    # Directory exists; that's okay.
    pass
os.environ['HOME'] = JACK
DB = os.path.join(JACK, 'dumptruck.db')
SW_JSON = os.path.join(JACK, 'sw.json')

def api_helper(*args, **kwargs):
    if 'boxhome' not in kwargs:
        kwargs['boxhome'] = BOXHOME
    return api(*args, **kwargs)

class TestCGI(unittest.TestCase):
    """CGI"""
    def setUp(self):
        try:
            os.remove(DB)
        except OSError:
            pass

        if not os.path.isdir(JACK):
            os.makedirs(JACK)

        self.dt = dumptruck.DumpTruck(dbname=DB)

    def test_cgi_400_fake(self):
        """Result from execute_query() call appears as HTTP Status."""
        os.environ['QUERY_STRING'] = 'qqqq=SELECT+favorite_color+FROM+person&box=jack-in-a'
        import dumptruck_web
        old_fn = dumptruck_web.execute_query
        dumptruck_web.execute_query = lambda q, d: (400, 'Blah blah blah')
        try:
            observed = api_helper().split('\n')[0]
        finally:
            dumptruck_web.execute_query = old_fn
        expected = 'HTTP/1.1 400 Bad Request'
        self.assertEqual(observed, expected)

    def test_cgi_400_real(self):
        """Invalid CGI query parameters give Bad Status Code."""
        os.environ['QUERY_STRING'] = 'qqqq=SELECT+favorite_color+FROM+person&box=jack-in-a'
        observed = api_helper().split('\n')[0]
        expected = 'HTTP/1.1 400 Bad Request'
        self.assertEqual(observed, expected)

    def test_cgi_200(self):
        """Good query gives good result."""
        os.system('cp fixtures/sw.json.dumptruck.db ' + SW_JSON)
        self.dt.insert({u'name': u'Aidan', u'favorite_color': u'Green'}, 'person')
        os.environ['QUERY_STRING'] = 'q=SELECT+favorite_color+FROM+person&box=jack-in-a'
        # Split into headers, which are checked against a literal string,
        # and a body which is checked via JSON decoding.
        observed = api_helper().split('\n\n', 1)
        expected = ('HTTP/1.1 200 OK\n' +
            'Content-Type: application/json; charset=utf-8')
        self.assertEqual(observed[0], expected)
        expected = [{"favorite_color": "Green"}]
        self.assertEqual(json.loads(observed[1]), expected)
    
    def test_doubled_up_q(self):
        """Not harmful to specify q=... twice."""
        os.environ['QUERY_STRING'] = 'q=SELECT+7&q=SELECT+3&box=jack-in-a'
        observed = api_helper().split('\n')[0]
        expected = 'HTTP/1.1 400 Bad Request'
        self.assertEqual(observed, expected)
    
    def test_doubled_up_box(self):
        """Not harmful to specify box=... twice."""
        os.environ['QUERY_STRING'] = 'q=SELECT+7&box=jack-in-a&box=bob'
        observed = api_helper().split('\n')[0]
        expected = 'HTTP/1.1 400 Bad Request'
        self.assertEqual(observed, expected)

    def test_http(self):
        """A complete example, including HTTP response headers."""
        os.environ['QUERY_STRING'] = 'q=SELECT+*+FROM+sqlite_master+LIMIT+0&box=jack-in-a'
        observed = api_helper().split('\n')
        expected = [
            'HTTP/1.1 200 OK',
            'Content-Type: application/json; charset=utf-8',
            '',
            '[]',
            '',
        ]
        self.assertListEqual(observed, expected)

class TestAPI(unittest.TestCase):
    """API"""
    def _q(self, dbname, p, output_check=None, code_check=None):
        """For testing sw.json database file configuration.  Runs some query on the
        database *dbname*, using *p* as a parameter.  Normally the output will be
        inspected to see if it contains *p* but if *output_check* is specified, then that
        value will be checked for in the output instead.

        *code_check* is used to check the status code.
        """

        try:
            os.remove(dbname)
        except OSError:
            pass

        if not os.path.isdir(JACK):
            os.makedirs(JACK)

        dbname = os.path.join(JACK, os.path.expanduser(dbname))
        dt = dumptruck.DumpTruck(dbname)
        dt.drop('bacon', if_exists=True)
        dt.insert({'p': p}, 'bacon')

        os.environ['QUERY_STRING']='q=SELECT+p+FROM+bacon&box=jack-in-a'
        os.environ['REQUEST_METHOD'] = 'GET'
        http = api_helper()

        if output_check:
            self.assertIn(unicode(output_check), http)

        if code_check:
            self.assertIn(unicode(code_check), http.split('\n')[0])

        # The body should be valid JSON
        body = '\n\n'.join(http.split('\n\n')[1:])
        json.loads(body)

        try:
            os.remove(dbname)
        except OSError:
            pass

    def test_dumptruck(self):
        """Works with ordinary file."""
        os.system('cp fixtures/sw.json.dumptruck.db ' + SW_JSON)
        self._q('dumptruck.db', 2124)

    def test_home_dumptruck(self):
        """Uses database found in home directory."""
        os.system('cp fixtures/sw.json.home-dumptruck.db ' + SW_JSON)
        self._q('~/dumptruck.db', 3824)

    def test_scraperwiki(self):
        """Can use other popular database filenames."""
        os.system('cp fixtures/sw.json.scraperwiki.sqlite ' + SW_JSON)
        self._q('scraperwiki.sqlite', 9804)
        
    def test_no_sw_json(self):
        """Raises an error if there is no sw.json."""
        os.system('rm -f ' + SW_JSON)
        self._q(':memory:', 2938, output_check='No sw.json', code_check=500)

    def test_malformed_json(self):
        """Raises an error if there is a malformed sw.json."""
        os.system("echo '{{{{{' >> " + SW_JSON)
        self._q(':memory:', 293898879, output_check='Malformed sw.json')

    def test_no_database_attribute(self):
        """Raises an error if there is a well-formed sw.json with no database attribute."""
        os.system("echo '{}' > " + SW_JSON)
        self._q(':memory:', 29379, output_check='No \\"database\\" attribute')

    def test_report_if_database_does_not_exist(self):
        """Raises an error if the database specified in sw.json doesn't exist."""

        os.system('rm -f ' + os.path.join(JACK, '*'))
        os.system('cp fixtures/sw.json.scraperwiki.sqlite ' + SW_JSON)
        os.environ['QUERY_STRING'] = 'q=SELECT+favorite_color+FROM+person&box=jack-in-a'
        http = api_helper()
        self.assertIn('500', http.split('\n')[0])
        self.assertIn('Error: database file does not exist', http)

    def test_permissions_error(self):
        """Raises an error if access to the database is not permitted."""

        dbname = os.path.join(JACK, 'scraperwiki.sqlite')
        os.system('cp fixtures/sw.json.scraperwiki.sqlite ' + SW_JSON)
        os.system('touch ' + dbname)
        os.system('chmod 000 ' + dbname)
        http = api_helper()
        self.assertIn(u'(Check that the file exists and is readable by everyone.)', http)
        os.system('chmod 600 ' + dbname)
        os.system('rm -f ' + dbname)

if __name__ == '__main__':
    unittest.main()
