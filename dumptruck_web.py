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
}

def _authorizer_readonly(action_code, tname, cname, sql_location, trigger):
    "SQLite authorize to prohibit destructive SQL commands"
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
        dt = dumptruck.DumpTruck(dbname)

    else:
        # Use a memory database if there is no dumptruck.db
        dt = dumptruck.DumpTruck(':memory:')

    dt.connection.set_authorizer(_authorizer_readonly)

    if "q" not in query:
        data = u'Error: No query specified'
        code = 400

    else:
        sql = query['q']

        try:
            data = dt.execute(sql)

        except sqlite3.OperationalError, e:
            data = u'SQL error: ' + e.message
            code = 400

        except sqlite3.DatabaseError, e:
            if e.message == u"not authorized":
                data = u'Error: Not authorized'
                code = 403
            else:
                data = u'Database error: ' + e.message
                code = 400

        else:
            code = 200

    return code, json.dumps(data)

def api():
    """
    It takes a query string like

        q=SELECT+foo+FROM+bar&boxname=screwdriver

    Currently, q and boxname are the only parameters.
    """
    form = cgi.FieldStorage()
    qs = {name: form[name].value for name in form.keys()}
    # Use the database file specified by the "database" field in ~/sw.json

    path = os.path.expanduser(os.path.join('/', 'home', qs['box'], 'sw.json'))
    try:
        sw_json = open(path).read()
    except IOError:
        raise 

    try:
        dbname = os.path.expanduser(json.loads(sw_json)['database'])
    except:
        raise
        
    # Run the query
    code, body = dumptruck_web(qs, dbname)
    headers = HEADERS % CODE_MAP[code]
    return headers + '\n\n' + body + '\n'

if __name__ == '__main__':
    api()
