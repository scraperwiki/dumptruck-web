import os
from dumptruck_web import sqlite_api

def main():
    # Settings
    import demjson
    sw_json = open(os.path.expanduser('~/sw.json')).read()
    db = os.path.expanduser(demjson.decode(sw_json)['database'])

    return sqlite_api(db)

if __name__ == "__main__":
    http = main()
    print http
