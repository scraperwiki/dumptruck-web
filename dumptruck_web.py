#!/usr/bin/env python

import cgi
import json
import os
import sqlite3

import dumptruck

# For fastcgi at least, the HTTP status code must be specified
# as a 'Status:' header.  See http://www.fastcgi.com/docs/faq.html#httpstatus
HEADERS = '''HTTP/1.1 %(status)s
Status: %(status)s
Content-Type: application/json; charset=utf-8'''

LONG_STATUS = {
    200: '200 OK',
    301: '301 Moved permanently',
    302: '302 Found',
    303: '303 See Other',
    400: '400 Bad Request',
    401: '401 Unauthorized',
    403: '403 Forbidden',
    404: '404 Not Found',
    500: '500 ',
}

class QueryError(Exception):
    """Exception during query processing."""
    def __init__(self, msg, code, **k):
        """Code which catches these exceptions, expects to find an HTTP Status code in
        code.
        """
        self.code = code
        super(QueryError, self).__init__(msg, **k)

def _authorizer_readonly(action_code, tname, cname, sql_location, trigger):
    """SQLite callback that we use to prohibit any SQL commands that could change a
    database; effectively making it readonly.

    Copied from scraperwiki.com sources.
    """

    readonlyops = [
        sqlite3.SQLITE_SELECT,
        sqlite3.SQLITE_READ,
        sqlite3.SQLITE_DETACH,

        # 31=SQLITE_FUNCTION missing from library.
        # codes: http://www.sqlite.org/c3ref/c_alter_table.html
        31,
    ]
    if action_code in readonlyops:
        return sqlite3.SQLITE_OK

    if action_code == sqlite3.SQLITE_PRAGMA:
        tnames_ok = {
            "table_info",
            "index_list",
            "index_info",
            "page_size",
            "synchronous"
        }
        if tname in tnames_ok:
            return sqlite3.SQLITE_OK

    # SQLite FTS (full text search) requires this permission even when reading,
    # and this doesn't let ordinary queries alter sqlite_master because of
    # PRAGMA writable_schema
    if action_code == sqlite3.SQLITE_UPDATE and tname == "sqlite_master":
        return sqlite3.SQLITE_OK

    return sqlite3.SQLITE_DENY

def execute_query(sql, dbname):
    """
    Given an SQL query and a SQLite database name, return an HTTP status code
    and the JSON-encoded response from the database.
    """
    if os.path.isfile(dbname):
        # Check for the database file
        try:
            dt = dumptruck.DumpTruck(dbname, adapt_and_convert = False)
        except sqlite3.OperationalError, e:
            if e.message == 'unable to open database file':
                data = e.message + ' (Check that the file exists and is readable by everyone.)'
                code = 500
                return code, data
    else:
        data = 'Error: database file does not exist.'
        code = 500
        return code, data

    dt.connection.set_authorizer(_authorizer_readonly)

    try:
        data = dt.execute(sql)
        code = 200
    except sqlite3.OperationalError, e:
        data = u'SQL error: ' + e.message
        code = 400
    except sqlite3.DatabaseError, e:
        data = u'Database error: ' + e.message
        if e.message == u"not authorized":
            # Writes are not authorized.
            code = 403
        else:
            code = 500
    except Exception, e:
        data = u'Error: ' + e.message
        code = 500

    return code, data

def api(boxhome=os.path.join('/', 'home')):
    """
    Implements a CGI interface for SQL queries to boxes.

    It takes a query string like

        q=SELECT+foo+FROM+bar&boxname=screwdriver

    Currently, *q* and *boxname* are the only parameters.
    """

    try:
        sql,box = parse_query_string()
        dbname = get_database_name(boxhome, box)
        code,body = execute_query(sql, dbname)
    except QueryError as e:
        code = e.code
        body = e.message
    body = json.dumps(body)

    headers = HEADERS % dict(status=LONG_STATUS[code])
    return headers + '\n\n' + body + '\n'

def parse_query_string():
    """Return sql,box as a pair.  Extracted from the CGI parameters."""
    form = cgi.FieldStorage()
    qs = form.getlist('q')
    boxs = form.getlist('box')
    if len(qs) != 1:
        raise QueryError('Error: exactly one q= parameter should be specified', code=400)
    if len(boxs) != 1:
        raise QueryError('Error: exactly one box= parameter should be specified', code=400)

    sql = qs[0]
    box = boxs[0]
    return sql, box

def get_database_name(boxhome, box):
    """Use the database file specified by the "database" field in ~/box.json."""

    path = os.path.join(boxhome, box, 'box.json')
    if not os.path.exists(path):
        path = os.path.join(boxhome, box, 'scraperwiki.json')

    try:
        with open(path) as f:
            sw_json = f.read()
    except IOError:
        raise QueryError('Error: No box.json file', code=500)

    try:
        sw_data = json.loads(sw_json)
    except ValueError:
        raise QueryError('Malformed box.json file', code=500)

    try:
        dbname = os.path.join(boxhome, box, os.path.expanduser(sw_data['database']))
    except KeyError:
        raise QueryError('No "database" attribute in box.json', code=500)

    return dbname

if __name__ == '__main__':
    print api()
