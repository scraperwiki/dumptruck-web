import os
import demjson
import unittest
import dumptruck
from dumptruck_web import dumptruck_web
import example

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

        self.assertListEqual(demjson.decode(observedData), [{u"favorite_color": u"Green"}])
        self.assertEqual(observedCode, 200)

    def test_invalid_query(self):
        observedCode, observedData = dumptruck_web({u'q': u'chainsaw'}, DB)

        self.assertEqual(demjson.decode(observedData), u'SQL error: near "chainsaw": syntax error')
        self.assertEqual(observedCode, 400)

    def test_destructive_query(self):
        self.dt.execute('CREATE TABLE important(foo);')
        observedCode, observedData = dumptruck_web({'q': u'DROP TABLE important;'}, DB)

        self.assertEqual(demjson.decode(observedData), u'Error: Not authorized')
        self.assertEqual(observedCode, 403)

    def test_no_query(self):
        observedCode, observedData = dumptruck_web({}, DB)

        self.assertEqual(demjson.decode(observedData), u'Error: No query specified')
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
        self.assertListEqual(demjson.decode(observedData), [])

        # All is well.
        self.assertEqual(observedCode, 200)
        

#   test_private_db(self):
#       observedCode, observedData = dumptruck_web({u'q': u''}, DB)
#       self.assertEqual(observedCode, 401)


class TestCgi(SqliteApi):
    def test_cgi(self):
        'CGI should work.'
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

if __name__ == '__main__':
    unittest.main()
