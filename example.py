def main():
    import demjson
    import os
    from dumptruck_web import sqlite_api

    # Settings
    sw_json = open(os.path.expanduser('~/sw.json')).read()
    db = os.path.expanduser(demjson.decode(sw_json)['database'])

    # Go
    return sqlite_api(db)

if __name__ == "__main__":
    print(main())
