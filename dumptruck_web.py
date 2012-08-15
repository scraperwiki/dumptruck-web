#!/usr/bin/env python
import os
import cgi
import sqlite3
import dumptruck
import json

HEADERS = '''HTTP/1.1 %s
Content-Type: application/json; charset=utf-8'''

CODE_MAP = {
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

def database(query, dbname):
    """
    Given an SQL query and a SQLite database name, return an HTTP status code
    and the JSON-encoded response from the database.
    """
    if os.path.isfile(dbname):
        # Check for the database file
        try:
            dt = dumptruck.DumpTruck(dbname)
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

    if "q" not in query:
        data = u'Error: no query specified'
        code = 400
        return code, data

    sql = query['q']

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

def api(boxhome = os.path.join('/', 'home')):
    """
    It takes a query string like

        q=SELECT+foo+FROM+bar&boxname=screwdriver

    Currently, q and boxname are the only parameters.
    """
    form = cgi.FieldStorage()
    qs = {name: form[name].value for name in form.keys()}
    # Use the database file specified by the "database" field in ~/sw.json

    code = None
    path = os.path.join(boxhome, qs['box'], 'sw.json')

    # Rewrite this with with.
    try:
        sw_json = open(path).read()
    except IOError:
        if code == None:
            code = 500
            body = 'No sw.json file'

    try:
        sw_data = json.loads(sw_json)
    except:
        if code == None:
            code = 500
            body = 'Malformed sw.json file'

    try:
        dbname = os.path.join(boxhome, qs['box'], os.path.expanduser(sw_data['database']))
    except:
        if code == None:
            code = 500
            body = 'No "database" attribute in sw.json'
        
    # Run the query
    if code == None:
        code, body = database(qs, dbname)
    body = json.dumps(body)

    headers = HEADERS % CODE_MAP[code]
    return headers + '\n\n' + body + '\n'

if __name__ == '__main__':
    print api()
