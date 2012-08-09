import os
import unittest
import dumptruck
import dumptruck_web

DB = 'dumptruck.db'

class SqliteApi(unittest.TestCase):
    def setUp(self):
        try:
            os.remove(DB)
        except OSError:
            pass
        self.dt = dumptruck.DumpTruck(dbname=DB)

class TestQueries(SqliteApi):
    test_valid_query(self):
        self.dt.insert({'name': 'Aidan', 'color': 'Green'}, 'person')
        observedCode, observedData = dumptruck_web('?q=SELECT+favorite_color+FROM+person')

        self.assertListEqual(json.loads(observedData), [{"name":"Aidan","color":"Green"}])
        self.assertEqual(observedCode, 200)

    test_invalid_query(self):
        observedCode, observedData = dumptruck_web('?q=chainsaw')

        self.assertEqual(observedData, 'SQL error: near "chainsaw": syntax error')
        self.assertEqual(observedCode, 400)

    test_destructive_query(self):
        observedCode, observedData = dumptruck_web('?q=DROP+TABLE+sqlite_master;')

        self.assertEqual(observedData, 'Error: attempt to write a readonly database')
        self.assertEqual(observedCode, 403)

class TestFileness(unittest.TestCase):
    def setUp(self):
        try:
            os.remove(DB)
        except OSError:
            pass

    def test_query_nonexistant(self):
        "When we query a database file that doesn't exist"
        observedCode, observedData = dumptruck_web('?q=SELECT+3+FROM+sqlite_master')

        # File is not created
        self.assertFalse(os.path.isfile(DB))

        # Empty list is returned
        self.assertListEqual(json.loads(observedData), [])

        # All is well.
        self.assertEqual(observedCode, 200)
        

#   test_private_db(self):
#       observedCode, observedData = dumptruck_web('?q=')
#       self.assertEqual(observedCode, 401)

if __name__ == '__main__':
    unittest.main()
