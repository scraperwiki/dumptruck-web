Foo bar
==============









## Running on Nginx

### CGI
http://nginx.localdomain.pl/wiki/FcgiWrap
http://wiki.codemongers.com/NginxFcgiExample
https://wiki.archlinux.org/index.php/Nginx#CGI_implementation
http://stackoverflow.com/questions/7048057/running-python-through-fastcgi-for-nginx

    apt-get install fcgiwrap nginx

### uWSGI
Here's a configuration based on the
[uWSGI quickstart]h(ttp://projects.unbit.it/uwsgi/wiki/Quickstart)

Install these.

    apt-get install uwsgi nginx uwsgi-plugin-{http,python}  

Run this (preferably as a daemon).

    uwsgi \
      --plugins http,python \
      --wsgi-file sqlite_api.py \
      --socket 127.0.0.1:3031 \
      --callable application \
      --processes 20

We'll have to adjust the api script so that it works with uWSGI;
`sqlite_api.py` is that.

Add this to the nginx site. (Try /etc/nginx/sites-enabled/default)

    location /path/to/sqlite {
        include uwsgi_params;
        uwsgi_pass 127.0.0.1:3031;
    }

Restart nginx.

    service nginx restart

Test

    curl localhost/path/to/sqlite?q=SELECT+42+FROM+sqlite_master

## Add later
Gzip responses.
