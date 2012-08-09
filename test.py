import unittest
import dumptruck
import dumptruck_web

class SqiteApi(unittest.TestCase):
    def setUp(self):
        try:
            os.remove('dumptruck.db')
        except OSError:
            pass
        self.dt = dumptruck.DumpTruck(dbname="dumptruck.db")

class TestQueries(SqliteApi):
    test_valid_query(self):
        self.dt.insert({'name': 'Aidan', 'color': 'Green'}, 'person')
        observedCode, observedData = dumptruck_web('?q=SELECT+favorite_color+FROM+person')

        self.assertListEqual(json.loads(observedData), [{"name":"Aidan","color":"Green"}])
        self.assertEqual(observedCode, 200)

if __name__ == '__main__':
    unittest.main()
