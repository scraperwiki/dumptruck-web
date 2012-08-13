#!/usr/bin/env python2

import sys
from dumptruck_web import dumptruck_web, HEADERS, CODE_MAP
import urllib2

def app(environ, start_response):
    dbname = sys.argv[1]
    print dbname
#   query = environ.get('q', 'select+3+from+sqlite_master;')
    code, data = dumptruck_web(environ, dbname)
    headers = [('Content-Type', 'application/json; charset=utf-8')]
    start_response(CODE_MAP[code], headers)
    return data

if __name__ == "__main__":
    from wsgiref.simple_server import make_server
    port = int(sys.argv[2])
    print "server on port: %i" % port
    make_server('', port, app).serve_forever()
