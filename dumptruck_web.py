import cgi
import dumptruck
import demjson

def dumptruck_web(query):
    dt = dumptruck.DumpTruck()

    if "q" not in query:
        data = 'Error: No query specified'
        code = 400
    else:
        sql = query['q']

        try:
            data = dt.execute(sql)
        except:
            raise
        else:
            code = 200

    return code, demjson.encode(data)


if __name__ == "__main__":
    
    # http://docs.python.org/library/cgi.html

    form = cgi.FieldStorage()
    qs = {name: form[name].value for name in form.keys()}

    dumptruck_web(qs)
