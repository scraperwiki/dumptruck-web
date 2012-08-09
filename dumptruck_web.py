import dumptruck
import demjson

def dumptruck_web(querystring):
    dt = dumptruck.DumpTruck()

    # http://docs.python.org/library/cgi.html
    form = cgi.FieldStorage()
    if "q" not in form:
        print 'Error: No query specified'

    try:
        data = dt.execute(form['q'])
    except:
        raise
    else:
        code = 200

    return code, demjson.encode(data)



if __name__ == "__main__":
    
    dumptruck_web(querystring)
