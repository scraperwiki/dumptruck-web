import cgi
import sqlite3
import dumptruck
import demjson

def dumptruck_web(query):
    dt = dumptruck.DumpTruck()

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
        else:
            code = 200

    return code, demjson.encode(data)


if __name__ == "__main__":
    
    # http://docs.python.org/library/cgi.html

    form = cgi.FieldStorage()
    qs = {name: form[name].value for name in form.keys()}

    dumptruck_web(qs)
