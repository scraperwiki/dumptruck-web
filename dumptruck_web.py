import cgi
import sqlite3
import dumptruck
import demjson

def authorizer_readonly(action_code, tname, cname, sql_location, trigger):
    readonlyops = [ sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ, sqlite3.SQLITE_DETACH, 31 ]  # 31=SQLITE_FUNCTION missing from library.  codes: http://www.sqlite.org/c3ref/c_alter_table.html
    if action_code in readonlyops:
        return sqlite3.SQLITE_OK

    if action_code == sqlite3.SQLITE_PRAGMA:
        if tname in ["table_info", "index_list", "index_info", "page_size", "synchronous"]:
            return sqlite3.SQLITE_OK

    # SQLite FTS (full text search) requires this permission even when reading, and
    # this doesn't let ordinary queries alter sqlite_master because of PRAGMA writable_schema
    if action_code == sqlite3.SQLITE_UPDATE and tname == "sqlite_master":
        return sqlite3.SQLITE_OK

    return sqlite3.SQLITE_DENY


def dumptruck_web(query):
    dt = dumptruck.DumpTruck()
    dt.connection.set_authorizer(authorizer_readonly)

    if "q" not in query:
        data = u'Error: No query specified'
        code = 400
    else:
        sql = query['q']

        try:
            data = dt.execute(sql)
        except sqlite3.OperationalError, e:
            data = u'SQL error: ' + unicode(e)
            code = 400
        except sqlite3.DatabaseError, e:
            if e.message == u"not authorized":
                data = u'Error: Not authorized'
                code = 403
            else:
                data = u'Database error: ' + unicode(e)
                code = 400
        else:
            code = 200

    return code, demjson.encode(data)


if __name__ == "__main__":
    # http://docs.python.org/library/cgi.html

    form = cgi.FieldStorage()
    qs = {name: form[name].value for name in form.keys()}

    dumptruck_web(qs)
