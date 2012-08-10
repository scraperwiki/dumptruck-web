Foo bar
==============

## Running on Nginx

### CGI
Here's an Nginx FastCGI configuration for Ubuntu based on the
[Arch Linux Wiki](https://wiki.archlinux.org/index.php/Nginx#FastCGI).

Install.

    apt-get install fcgiwrap nginx

Configure the nginx site. (Try `/etc/nginx/sites-enabled/default`.)
                                                  
    location / {                                               
        fastcgi_param DOCUMENT_ROOT /var/www/;
        fastcgi_param SCRIPT_NAME sqlite_api.py;
        fastcgi_pass unix:/var/run/fcgiwrap.socket;
    }

This depends on `/var/www/sqlite_api.py` being a cgi script file that www-data
can execute.

Specify some high number of processes in `/etc/init.d/fcgiwrap` like so.

    FCGI_CHILDREN="9001"

You could also try something less extreme.

Then (re)start the daemons.

    service fcgiwrap restart
    service nginx restart

If this doesn't work, read `/etc/init.d/fcgiwrap`.

An example (simple) script would be

    #!/usr/bin/env python
    
    print '''HTTP/1.1 200
    Content-Type: text/plain
    
    Hello world
    '''

### uWSGI
Here's a configuration based on the
[uWSGI quickstart](http://projects.unbit.it/uwsgi/wiki/Quickstart) 

Also see [uWSGI on nginx page](http://projects.unbit.it/uwsgi/wiki/RunOnNginx),
for reference but note that this explains a configuration that may be
unnecessarily complicated.

Install these.

    apt-get install uwsgi nginx uwsgi-plugin-{http,python}  

Run this (preferably as a daemon).

    uwsgi \
      --plugins http,python \
      --wsgi-file sqlite_api.py \
      --socket 127.0.0.1:3031 \
      --callable application \
      --processes 20

Use some high number of processes because they block.

We'll have to adjust the api script so that it works with uWSGI;
`sqlite_api.py` is that.

Add this to the nginx site. (Try `/etc/nginx/sites-enabled/default`.)

    location /path/to/sqlite {
        include uwsgi_params;
        uwsgi_pass 127.0.0.1:3031;
    }

Restart nginx.

    service nginx restart

Test

    curl localhost/path/to/sqlite?q=SELECT+42+FROM+sqlite_master

An example (simple) script would be

    def application(env, start_response):
        start_response('200 OK', [('Content-Type','text/html')])
        return "Hello World"

## Add later
Gzip responses.
