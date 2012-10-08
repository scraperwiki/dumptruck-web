import os
import cgi
import sqlite3
import dumptruck
import demjson

def authorizer_readonly(action_code, tname, cname, sql_location, trigger):
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

def dumptruck_web(query, dbname):
    """
    Given an SQL query and a SQLitedatabase name, return an HTTP status code
    and the JSON-encoded response from the database.
    """
    if os.path.isfile(dbname):
        # Check for the database file
        dt = dumptruck.DumpTruck(dbname, adapt_and_convert = False)

    else:
        # Use a memory database if there is no dumptruck.db
        dt = dumptruck.DumpTruck(':memory:')

    dt.connection.set_authorizer(authorizer_readonly)

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

    return code, demjson.encode(data)

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
def sqlite_api(dbname):
    """
    This CGI function takes the $QUERY_STRING and database name as input, so
    you can create a SQLite HTTP API by importing and calling this function.

    It takes a query string like

        q=SELECT+foo+FROM+bar

    Currently, q the only parameter.
    """
    form = cgi.FieldStorage()
    qs = {name: form[name].value for name in form.keys()}
    code, body = dumptruck_web(qs, dbname)
    headers = HEADERS % CODE_MAP[code]
    return headers + '\n\n' + body + '\n'
