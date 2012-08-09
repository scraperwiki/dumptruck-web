import os
import demjson
import unittest
import dumptruck
from dumptruck_web import dumptruck_web

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
        observedCode, observedData = dumptruck_web({'q': u'SELECT favorite_color FROM person'})

        self.assertListEqual(demjson.decode(observedData), [{u"favorite_color": u"Green"}])
        self.assertEqual(observedCode, 200)

    def test_invalid_query(self):
        observedCode, observedData = dumptruck_web({u'q': u'chainsaw'})

        self.assertEqual(demjson.decode(observedData), u'SQL error: near "chainsaw": syntax error')
        self.assertEqual(observedCode, 400)

    def test_destructive_query(self):
        self.dt.execute('CREATE TABLE important(foo);')
        observedCode, observedData = dumptruck_web({'q': u'DROP TABLE important;'})

        self.assertEqual(demjson.decode(observedData), u'Error: Not authorized')
        self.assertEqual(observedCode, 403)

    def test_no_query(self):
        observedCode, observedData = dumptruck_web({})

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
        observedCode, observedData = dumptruck_web({'q': u'SELECT 3 FROM sqlite_master'})

        # File is not created
        self.assertFalse(os.path.isfile(DB))

        # Empty list is returned
        self.assertListEqual(demjson.decode(observedData), [])

        # All is well.
        self.assertEqual(observedCode, 200)
        

#   test_private_db(self):
#       observedCode, observedData = dumptruck_web({u'q': u''})
#       self.assertEqual(observedCode, 401)

if __name__ == '__main__':
    unittest.main()
