sql=$(mktemp)
python2 -c 'import os,urllib2;print(urllib2.urlparse.parse_qs(os.environ["QUERY_STRING"])["q"][0])' > $sql
sqlite3 dumptruck.db $sql
