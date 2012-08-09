from dumptruck_web import sqlite_api

def main():
    # Settings
    # import demjson
    # DB = demjson.decode(open('../sw.json').read())['database']

    return sqlite_api('dumptruck.db')

if __name__ == "__main__":
    http = main()
    print http
