#!/usr/bin/env python

import os
import json
from nose.tools import *
import unittest

import dumptruck
from dumptruck_web import sql, meta

# Directory in which boxes are created.
BOXHOME = os.path.join('/', 'tmp', 'boxtests') 
# The directory for a particular box.
JACK = os.path.join(BOXHOME, 'jack-in-a')
try:
    os.makedirs(JACK)
except OSError:
    # Directory exists; that's okay.
    pass
os.environ['HOME'] = JACK
DB = os.path.join(JACK, 'dumptruck.db')
SW_JSON = os.path.join(JACK, 'box.json')

def sql_helper(*args, **kwargs):
    if 'boxhome' not in kwargs:
        kwargs['boxhome'] = BOXHOME
    return sql(*args, **kwargs)

def meta_helper(*args, **kwargs):
    if 'boxhome' not in kwargs:
        kwargs['boxhome'] = BOXHOME
    return meta(*args, **kwargs)


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
            observed = sql_helper().split('\n')[0]
        finally:
            dumptruck_web.execute_query = old_fn
        expected = 'HTTP/1.1 400 Bad Request'
        self.assertEqual(observed, expected)

    def test_cgi_400_real(self):
        """Invalid CGI query parameters give Bad Status Code."""
        os.environ['QUERY_STRING'] = 'qqqq=SELECT+favorite_color+FROM+person&box=jack-in-a'
        observed = sql_helper().split('\n')[0]
        expected = 'HTTP/1.1 400 Bad Request'
        self.assertEqual(observed, expected)

    def test_cgi_200(self):
        """Good query gives good result."""
        os.system('cp fixtures/sw.json.dumptruck.db ' + SW_JSON)
        self.dt.insert({u'name': u'Aidan', u'favorite_color': u'Green'}, 'person')
        os.environ['QUERY_STRING'] = 'q=SELECT+favorite_color+FROM+person&box=jack-in-a'
        # Split into headers, which are checked against a literal string,
        # and a body which is checked via JSON decoding.
        observed = sql_helper().split('\n\n', 1)
        expected = ('HTTP/1.1 200 OK\n' +
            'Status: 200 OK\n' +
            'Content-Type: application/json; charset=utf-8')
        self.assertEqual(observed[0], expected)
        expected = [{"favorite_color": "Green"}]
        self.assertEqual(json.loads(observed[1]), expected)

    def test_doubled_up_q(self):
        """Not harmful to specify q=... twice."""
        os.environ['QUERY_STRING'] = 'q=SELECT+7&q=SELECT+3&box=jack-in-a'
        observed = sql_helper().split('\n')[0]
        expected = 'HTTP/1.1 400 Bad Request'
        self.assertEqual(observed, expected)

    def test_doubled_up_box(self):
        """Not harmful to specify box=... twice."""
        os.environ['QUERY_STRING'] = 'q=SELECT+7&box=jack-in-a&box=bob'
        observed = sql_helper().split('\n')[0]
        expected = 'HTTP/1.1 400 Bad Request'
        self.assertEqual(observed, expected)

    def test_http(self):
        """A complete example, including HTTP response headers."""
        os.environ['QUERY_STRING'] = 'q=SELECT+*+FROM+sqlite_master+LIMIT+0&box=jack-in-a'
        observed = sql_helper().split('\n')
        expected = [
            'HTTP/1.1 200 OK',
            'Status: 200 OK',
            'Content-Type: application/json; charset=utf-8',
            '',
            '[]',
            '',
        ]
        self.assertListEqual(observed, expected)

    def testMetaSimple(self):
        """Test the metadata endpoint."""

        os.system('cp fixtures/sw.json.dumptruck.db ' + SW_JSON)

        os.environ['QUERY_STRING'] = 'box=jack-in-a'
        header,body =  meta_helper().split('\n\n', 1)
        expected = ('HTTP/1.1 200 OK\n' +
            'Status: 200 OK\n' +
            'Content-Type: application/json; charset=utf-8')
        self.assertEqual(header, expected)
        # we expect an empty database.
        expected = {"table": {}, "databaseType": "sqlite3"}
        self.assertEqual(json.loads(body), expected)

    def testNotExist(self):
        """Test that when the database file doesn't exist
        the sql endpoint has statusCode 404."""

        try:
            os.remove(DB)
        except OSError:
            pass

        # os.system('cp fixtures/sw.json.dumptruck.db ' + SW_JSON)

        os.environ['QUERY_STRING'] = 'box=jack-in-a&q=SELECT*FROM+sqlite_master'
        header,body =  sql_helper().split('\n\n', 1)

        expected = ('HTTP/1.1 404 Not Found\n' +
            'Status: 404 Not Found\n' +
            'Content-Type: application/json; charset=utf-8')
        self.assertEqual(header, expected)
        # The body should be a JSON object with an 'error' key.
        bodyJSON = json.loads(body)
        self.assertIn('error', bodyJSON.keys())

    def testMetaNotExist(self):
        """Test that when the database file doesn't exist
        the metadata endpoint still returns something sensible."""

        # os.system('cp fixtures/sw.json.dumptruck.db ' + SW_JSON)

        os.environ['QUERY_STRING'] = 'box=jack-in-a'
        header,body =  meta_helper().split('\n\n', 1)
        expected = ('HTTP/1.1 200 OK\n' +
            'Status: 200 OK\n' +
            'Content-Type: application/json; charset=utf-8')
        self.assertEqual(header, expected)
        # we expect an empty database.
        expected = {"table": {}, "databaseType": "none"}
        # self.assertEqual(json.loads(body), expected)

    def testMetaTableListed(self):
        """The table is listed in the metadata."""

        os.system('cp fixtures/sw.json.dumptruck.db ' + SW_JSON)

        # The sql/meta endpoint returns something like:
        """
        {
          "table": {
            "first_table_name": {
              "type": "table",
              "columnNames": ["column1", "column2"]
            },
            "a_view": {
              "type": "view",
              "columnNames": ["blah blah", "blah"]
            },
          },
          "databaseType": "sqlite"
        }
        # With future expansion for columns that are typed:
            "columns": [{"name":"column1","type":"Number"}]
        # and tables with unique keys.
            "uniqueKeys": ["col1", "col2"}
        """

        os.environ['QUERY_STRING'] = 'box=jack-in-a'
        self.dt.insert({'akey': 'avalue'}, "newtable")
        self.dt.execute(
          "CREATE VIEW aview AS SELECT 1 as cola, 2 as colb",
          commit=False)
        os.environ['QUERY_STRING'] = 'box=jack-in-a'
        header,body =  meta_helper().split('\n\n', 1)
        jbody = json.loads(body)

        # check table is listed
        self.assertIn("newtable", jbody['table'])
        self.assertEqual(jbody['table']['newtable']['type'], "table")

        # check column_names are listed:
        n = jbody['table']['newtable']
        self.assertIn("columnNames", n)
        self.assertEqual(n['columnNames'], ["akey"])

        # check view is listed
        self.assertIn("aview", jbody['table'])
        self.assertEqual(jbody['table']['aview']['type'], "view")

        # check column_names are listed:
        n = jbody['table']['aview']
        self.assertIn("columnNames", n)
        self.assertEqual(n['columnNames'], ["cola", "colb"])

class TestAPI(unittest.TestCase):
    """API"""
    def _q(self, dbname, p, output_check=None, code_check=None):
        """For testing box.json database file configuration.  Runs
        some query on the database *dbname*, using *p* as a parameter.
        Normally the output will be inspected to see if it contains *p*
        but if *output_check* is specified, then that
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
        http = sql_helper()

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
        """Raises an error if there is no box.json."""
        os.system('rm -f ' + SW_JSON)
        self._q(':memory:', 2938, output_check='No box.json', code_check=500)

    def test_malformed_json(self):
        """Raises an error if there is a malformed box.json."""
        os.system("echo '{{{{{' >> " + SW_JSON)
        self._q(':memory:', 293898879, output_check='Malformed box.json')

    def test_no_database_attribute(self):
        """Raises an error if there is a well-formed box.json with no database attribute."""
        os.system("echo '{}' > " + SW_JSON)
        self._q(':memory:', 29379, output_check='No \\"database\\" attribute')

    def test_report_if_database_does_not_exist(self):
        """Raises an error if the database specified in box.json doesn't exist."""

        os.system('rm -f ' + os.path.join(JACK, '*'))
        os.system('cp fixtures/sw.json.scraperwiki.sqlite ' + SW_JSON)
        os.environ['QUERY_STRING'] = 'q=SELECT+favorite_color+FROM+person&box=jack-in-a'
        http = sql_helper()
        self.assertIn('404', http.split('\n')[0])
        self.assertIn('database file does not exist', http)

    def test_permissions_error(self):
        """Raises an error if access to the database is not permitted."""

        dbname = os.path.join(JACK, 'scraperwiki.sqlite')
        os.system('cp fixtures/sw.json.scraperwiki.sqlite ' + SW_JSON)
        os.system('touch ' + dbname)
        os.system('chmod 000 ' + dbname)
        http = sql_helper()
        self.assertIn(u'(Check that the file exists and is readable by everyone.)', http)
        os.system('chmod 600 ' + dbname)
        os.system('rm -f ' + dbname)

if __name__ == '__main__':
    unittest.main()
