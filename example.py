def main():
    import demjson
    import os
    from dumptruck_web import sqlite_api

    # Use the database file specified by the "database" field in ~/sw.json
    sw_json = open(os.path.expanduser('~/sw.json')).read()
    db = os.path.expanduser(demjson.decode(sw_json)['database'])

    # Run the cgi script on that database.
    return sqlite_api(db)

if __name__ == "__main__":
    print(main())
