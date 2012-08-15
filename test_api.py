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
        """Result from database() call appears as HTTP Status."""
        os.environ['QUERY_STRING'] = 'qqqq=SELECT+favorite_color+FROM+person&box=jack-in-a'
        import dumptruck_web
        old_database = dumptruck_web.database
        dumptruck_web.database = lambda q, d: (400, 'Blah blah blah')
        try:
            observed = api_helper().split('\n')[0]
        finally:
            dumptruck_web.database = old_database
        expected = 'HTTP/1.1 400 Bad Request'
        self.assertEqual(observed, expected)

    def test_cgi_400_real(self):
        """Bad Requests are bad."""
        os.environ['QUERY_STRING'] = 'qqqq=SELECT+favorite_color+FROM+person&box=jack-in-a'
        observed = api_helper().split('\n')[0]
        expected = 'HTTP/1.1 400 Bad Request'
        self.assertEqual(observed, expected)

    def test_cgi_200(self):
        """OK result."""
        os.system('cp fixtures/sw.json.dumptruck.db ' + SW_JSON)
        self.dt.insert({u'name': u'Aidan', u'favorite_color': u'Green'}, 'person')
        os.environ['QUERY_STRING'] = 'q=SELECT+favorite_color+FROM+person&box=jack-in-a'
        observed = api_helper().split('\n')
        expected = [
            'HTTP/1.1 200 OK',
            'Content-Type: application/json; charset=utf-8',
            '',
            '[{"favorite_color": "Green"}]',
            '',
        ]
        self.assertEqual(observed, expected)

    def test_http(self):
        'Example script should return these HTTP headers.'
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
    def _q(self, dbname, how_many, check_inness = True, check_code = None):
        """For testing sw.json database file configuration
        By default, check whether how_many is in the output.
        Set check_inness to False to avoid this. Set it to something else to check that."""

        try:
            os.remove(dbname)
        except OSError:
            pass

        if not os.path.isdir(JACK):
            os.makedirs(JACK)

        if check_inness == True:
            check_inness = how_many
        elif check_inness == False:
            check_inness = None

        if check_inness != None:
            dbname = os.path.join(JACK, os.path.expanduser(dbname))
            dt = dumptruck.DumpTruck(dbname)
            dt.drop('bacon', if_exists = True)
            dt.insert({'how_many': how_many}, 'bacon')

        os.environ['QUERY_STRING']='q=SELECT+how_many+FROM+bacon&box=jack-in-a'
        os.environ['REQUEST_METHOD'] = 'GET'
        http = api_helper()

        if check_inness != None:
            self.assertIn(unicode(check_inness), http)

        if check_code != None:
            self.assertIn(unicode(check_code), http.split('\n')[0])

        # The body should be valid JSON
        body = '\n\n'.join(http.split('\n\n')[1:])
        json.loads(body)

        try:
            os.remove(dbname)
        except OSError:
            pass

    def test_dumptruck(self):
        os.system('cp fixtures/sw.json.dumptruck.db ' + SW_JSON)
        self._q('dumptruck.db', 2124)

    def test_home_dumptruck(self):
        os.system('cp fixtures/sw.json.home-dumptruck.db ' + SW_JSON)
        self._q('~/dumptruck.db', 3824)

    def test_scraperwiki(self):
        os.system('cp fixtures/sw.json.scraperwiki.sqlite ' + SW_JSON)
        self._q('scraperwiki.sqlite', 9804)
        
    def test_no_sw_json(self):
        "It should raise an error if there is no sw.json"
        os.system('rm -f ' + SW_JSON)
        self._q(':memory:', 2938, check_inness = 'No sw.json', check_code = 500)

    def test_malformed_json(self):
        "It should raise an error if there is a malformed sw.json"
        os.system("echo '{{{{{' >> " + SW_JSON)
        self._q(':memory:', 293898879, check_inness = 'Malformed sw.json')

    def test_no_database_attribute(self):
        "It should raise an error if there is a well-formed sw.json with no database attribute."
        os.system("echo '{}' > " + SW_JSON)
        self._q(':memory:', 29379, check_inness = 'No \\"database\\" attribute')

    def test_report_if_database_does_not_exist(self):
        '''
        As a user who knows languages other than SQL and probably doesn't
            want to run SQL on an empty database,
        I want the web SQLite API to respond with an error if the database
            specified in sw.json doesn't exist
        So that I can figure out why my queries are returning nothing.
        '''
        os.system('rm -f ' + os.path.join(JACK, '*'))
        os.system('cp fixtures/sw.json.scraperwiki.sqlite ' + SW_JSON)
        os.environ['QUERY_STRING'] = 'q=SELECT+favorite_color+FROM+person&box=jack-in-a'
        http = api_helper()
        self.assertIn('500', http.split('\n')[0])
        self.assertIn('Error: database file does not exist', http)

    def test_permissions_error(self):
        '''
        If the database cannot be accessed because of a lack of permission,
        say so rather than just giving the ordinary cryptic message.
        '''
        dbname = os.path.join(JACK, 'scraperwiki.sqlite')
        os.system('cp fixtures/sw.json.scraperwiki.sqlite ' + SW_JSON)
        os.system('touch ' + dbname)
        os.system('chmod 000 ' + dbname)
        http = api_helper()
        self.assertIn(u'(Check that the file exists and is readable by everyone.)', http)
        os.system('chmod 600 ' + dbname)
        os.system('rm -f ' + dbname)

#   def test_script_can_determine_database_file(self):
#       '''
#       You must specify the box, and that gets expanded to a path to the appropriate file.

#       You specify it like this.
#       /jack-in-the/sqlite?q=SELECT+foo+FROM+baz

#       The web server rewrites this to
#       /sqlite?q=SELECT+foo+FROM+baz&box=made-of-ticky-tacky

#       The CGI script (this repository) reads that query string and should
#       read the 'databases' attribute in /home/jack-in-the/sw.json
#       '''
#       raise NotImplementedError

if __name__ == '__main__':
    unittest.main()
