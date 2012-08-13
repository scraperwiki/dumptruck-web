import os
import json
import unittest
import dumptruck
from dumptruck_web import api

BOXHOME = os.path.join('/', 'tmp', 'boxtests') 
JACK = os.path.join(BOXHOME, 'jack-in-a')
DB = os.path.join(JACK, 'dumptruck.db')
SW_JSON = os.path.join(JACK, 'sw.json')

def api_test():
    return api(boxhome = BOXHOME)

class TestCgi(unittest.TestCase):
    def setUp(self):
        try:
            os.remove(DB)
        except OSError:
            pass

        if not os.path.isdir(JACK):
            os.makedirs(JACK)

        self.dt = dumptruck.DumpTruck(dbname=DB)

    def test_cgi_400(self):
        'CGI should work.'
        os.environ['QUERY_STRING'] = 'qqqq=SELECT+favorite_color+FROM+person&box=jack-in-a'
        observed = api_test().split('\n')[0]
        expected = 'HTTP/1.1 400 Bad Request'
        self.assertEqual(observed, expected)

    def test_cgi_200(self):
        'CGI should work.'
        os.system('cp fixtures/sw.json.dumptruck.db ' + SW_JSON)
        self.dt.insert({u'name': u'Aidan', u'favorite_color': u'Green'}, 'person')
        os.environ['QUERY_STRING'] = 'q=SELECT+favorite_color+FROM+person&box=jack-in-a'
        # observed = api_test(database_call = lambda q, d: (200, '[]').split('\n')
        observed = api_test().split('\n')
        expected = [
            'HTTP/1.1 200 OK',
            'Content-Type: application/json; charset=utf-8',
            '',
            '[{"favorite_color":"Green"}]',
            '',
        ]
        self.assertEqual(observed, expected)

    def test_http(self):
        'Example script should return these HTTP headers.'
        os.environ['QUERY_STRING'] = 'q=SELECT+*+FROM+sqlite_master+LIMIT+0&box=jack-in-a'
        observed = api_test().split('\n')
        expected = [
            'HTTP/1.1 200 OK',
            'Content-Type: application/json; charset=utf-8',
            '',
            '[]',
            '',
        ]
        self.assertListEqual(observed, expected)

class TestAPI(unittest.TestCase):
    def _q(self, dbname, how_many, check_inness = True):
        """For testing sw.json database file configuration
        By default, check whether how_many is in the output.
        Set check_inness to False to avoid this. Set it to something else to check that."""
        dbname = os.path.expanduser(dbname)
        dt = dumptruck.DumpTruck(dbname)
        dt.drop('bacon', if_exists = True)
        dt.insert({'how_many': how_many}, 'bacon')
        os.environ['QUERY_STRING']='q=SELECT+how_many+FROM+bacon&box=jack-in-a'
        http = api_test()

        if check_inness == True:
            check_inness = how_many
        elif check_inness == False:
            check_inness = None

        if check_inness != None:
            self.assertIn(unicode(check_inness), http)

        os.remove(dbname)

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
        self._q(api_test(), 2938, check_inness = 'no sw.json')

    def test_malformed_json(self):
        "It should raise an error if there is a malformed sw.json"
        os.system("echo '{{{{{' >> " + SW_JSON)
        self._q(api_test(), 293898879, check_inness = 'malformed sw.json')

    def test_no_database_attribute(self):
        "It should raise an error if there is a well-formed sw.json with no database attribute."
        os.system("echo '{}' > " + SW_JSON)
        self._q(api_test(), 29379, check_inness = 'malformed sw.json')

    def test_permissions_error(self):
        '''
        If the database cannot be accessed because of a lack of permission,
        say so rather than just giving the ordinary cryptic message.
        '''
        raise NotImplementedError

    def test_script_can_determine_database_file(self):
        '''
        You must specify the box, and that gets expanded to a path to the appropriate file.

        You specify it like this.
        /made-of-ticky-tacky/sqlite?q=SELECT+foo+FROM+baz

        We could rewrite this to
        /sqlite?q=SELECT+foo+FROM+baz&box=made-of-ticky-tacky

        or do regex matches on the url. The box name gets turned into

        1. Read the 'databases' attribute in /home/knight-box/sw.json
        2. Get the database from there.
        '''
        raise NotImplementedError

if __name__ == '__main__':
    unittest.main()
