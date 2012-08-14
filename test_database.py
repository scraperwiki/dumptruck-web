import os
import json
import unittest
import dumptruck
from dumptruck_web import database

# DB = os.path.expanduser('~/dumptruck.db')
DB = 'dumptruck.db'
class Database(unittest.TestCase):
    def setUp(self):
        try:
            os.remove(DB)
        except OSError:
            pass

        self.dt = dumptruck.DumpTruck(dbname=DB)

class TestQueries(Database):
    def test_valid_query(self):
        self.dt.insert({u'name': u'Aidan', u'favorite_color': u'Green'}, 'person')
        observedCode, observedData = database({'q': u'SELECT favorite_color FROM person'}, DB)

        self.assertListEqual(json.loads(observedData), [{u"favorite_color": u"Green"}])
        self.assertEqual(observedCode, 200)

    def test_invalid_query(self):
        observedCode, observedData = database({u'q': u'chainsaw'}, DB)

        self.assertEqual(json.loads(observedData), u'SQL error: near "chainsaw": syntax error')
        self.assertEqual(observedCode, 400)

    def test_destructive_query(self):
        self.dt.execute('CREATE TABLE important(foo);')
        observedCode, observedData = database({'q': u'DROP TABLE important;'}, DB)

        self.assertEqual(json.loads(observedData), u'Database error: not authorized')
        self.assertEqual(observedCode, 403)

    def test_no_query(self):
        observedCode, observedData = database({}, DB)

        self.assertEqual(json.loads(observedData), u'Error: no query specified')
        self.assertEqual(observedCode, 400)

class TestThatFilesAreNotCreated(unittest.TestCase):
    def setUp(self):
        try:
            os.remove(DB)
        except OSError:
            pass

    def test_query_nonexistant(self):
        "When we query a database file that doesn't exist"
        observedCode, observedData = database({'q': u'SELECT 3 FROM sqlite_master'}, DB)

        # File is not created
        self.assertFalse(os.path.isfile(DB))

        # All is well.
        self.assertTrue(observedCode >= 400)


#   test_private_db(self):
#       observedCode, observedData = database({u'q': u''}, DB)
#       self.assertEqual(observedCode, 401)

if __name__ == '__main__':
    unittest.main()
