import os
import json
import unittest
import dumptruck
from dumptruck_web import dumptruck_web
import example

# DB = os.path.expanduser('~/dumptruck.db')
DB = 'dumptruck.db'
class SqliteApi(unittest.TestCase):
    def setUp(self):
        try:
            os.remove(DB)
        except OSError:
            pass

        self.dt = dumptruck.DumpTruck(dbname=DB)

class TestQueries(SqliteApi):
    def test_valid_query(self):
        self.dt.insert({u'name': u'Aidan', u'favorite_color': u'Green'}, 'person')
        observedCode, observedData = dumptruck_web({'q': u'SELECT favorite_color FROM person'}, DB)

        self.assertListEqual(json.loads(observedData), [{u"favorite_color": u"Green"}])
        self.assertEqual(observedCode, 200)

    def test_invalid_query(self):
        observedCode, observedData = dumptruck_web({u'q': u'chainsaw'}, DB)

        self.assertEqual(json.loads(observedData), u'SQL error: near "chainsaw": syntax error')
        self.assertEqual(observedCode, 400)

    def test_destructive_query(self):
        self.dt.execute('CREATE TABLE important(foo);')
        observedCode, observedData = dumptruck_web({'q': u'DROP TABLE important;'}, DB)

        self.assertEqual(json.loads(observedData), u'Error: Not authorized')
        self.assertEqual(observedCode, 403)

    def test_no_query(self):
        observedCode, observedData = dumptruck_web({}, DB)

        self.assertEqual(json.loads(observedData), u'Error: No query specified')
        self.assertEqual(observedCode, 400)

class TestFileness(unittest.TestCase):
    def setUp(self):
        try:
            os.remove(DB)
        except OSError:
            pass

    def test_query_nonexistant(self):
        "When we query a database file that doesn't exist"
        observedCode, observedData = dumptruck_web({'q': u'SELECT 3 FROM sqlite_master'}, DB)

        # File is not created
        self.assertFalse(os.path.isfile(DB))

        # Empty list is returned
        self.assertListEqual(json.loads(observedData), [])

        # All is well.
        self.assertEqual(observedCode, 200)
        

#   test_private_db(self):
#       observedCode, observedData = dumptruck_web({u'q': u''}, DB)
#       self.assertEqual(observedCode, 401)


class TestCgi(SqliteApi):
    def test_cgi(self):
        'CGI should work.'
        os.system('cp fixtures/sw.json.dumptruck.db ~/sw.json')
        self.dt.insert({u'name': u'Aidan', u'favorite_color': u'Green'}, 'person')
        os.environ['QUERY_STRING'] = 'q=SELECT+favorite_color+FROM+person'
        observed = example.main().split('\n')
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
        os.environ['QUERY_STRING'] = 'q=SELECT+*+FROM+sqlite_master+LIMIT+0'
        observed = example.main().split('\n')
        expected = [
            'HTTP/1.1 200 OK',
            'Content-Type: application/json; charset=utf-8',
            '',
            '[]',
            '',
        ]
        self.assertListEqual(observed, expected)

class TestExampleScraperwikiJson(unittest.TestCase):
    def _q(self, dbname, how_many, check_inness = True):
        "For testing sw.json database file configuration"
        dbname = os.path.expanduser(dbname)
        dt = dumptruck.DumpTruck(dbname)
        dt.drop('bacon', if_exists = True)
        dt.insert({'how_many': how_many}, 'bacon')
        os.environ['QUERY_STRING']='q=SELECT+how_many+FROM+bacon'
        http = example.main()

        if check_inness:
            self.assertIn(unicode(how_many), http)

        os.remove(dbname)

    def test_dumptruck(self):
        os.system('cp fixtures/sw.json.dumptruck.db ~/sw.json')
        self._q('dumptruck.db', 2124)

    def test_home_dumptruck(self):
        os.system('cp fixtures/sw.json.home-dumptruck.db ~/sw.json')
        self._q('~/dumptruck.db', 3824)

    def test_scraperwiki(self):
        os.system('cp fixtures/sw.json.scraperwiki.sqlite ~/sw.json')
        self._q('scraperwiki.sqlite', 9804)

    def test_blank(self):
        "It should raise an error if \"database\" is not specified in the sw.json"
        os.system('cp fixtures/sw.json.blank ~/sw.json')
        with self.assertRaises(Exception):
            self._q(example.main(), 312123, check_inness = False)
        
    def test_no_sw_json(self):
        "It should raise an error if there is no sw.json"
        os.system('rm -f ~/sw.json')
        with self.assertRaises(Exception):
            self._q(example.main(), 2938, check_inness = False)

class TestExample(unittest.TestCase):
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
        /knight-box/sqlite?q=SELECT+foo+FROM+baz

        We could rewrite this to
        /sqlite?q=SELECT+foo+FROM+baz&box=knight-box

        or do regex matches on the url. The box name gets turned into

        1. Read the 'databases' attribute in /home/knight-box/sw.json
        2. Get the database from there.
        '''

if __name__ == '__main__':
    unittest.main()
