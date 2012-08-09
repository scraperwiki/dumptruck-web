from dumptruck_web import query

def main():
    # Settings
    # import demjson
    # DB = demjson.decode(open('../sw.json').read())['database']

    query('dumptruck.db')

if __name__ == "__main__":
    main()
