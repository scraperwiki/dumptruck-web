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
      fastcgi_param DOCUMENT_ROOT /var/www/dumptruck-web/;
      fastcgi_param SCRIPT_NAME dumptruck_web.py;
      fastcgi_param SCRIPT_FILENAME /var/www/dumptruck-web/dumptruck_web.py;
      fastcgi_pass unix:/var/run/fcgiwrap.socket;  
      
      # Fill in the gaps. This does not overwrite previous settings,
      # so it goes last
      include /etc/nginx/fastcgi_params;
     }

This depends on `/var/www/dumptruck_web.py` being a cgi script file that www-data
can execute.
 
If you're installing this as part of cobalt, the configuration is 

    location ~ ^\/([^\s/]+)\/sqlite\/?$ {
        fastcgi_param DOCUMENT_ROOT /var/www/dumptruck-web/;
        fastcgi_param SCRIPT_NAME dumptruck_web.py;
        fastcgi_param SCRIPT_FILENAME /var/www/dumptruck-web/dumptruck_web.py;

        # Fill in the gaps. This does not overwrite previous settings,
        # so it goes last
        include /etc/nginx/fastcgi_params;
        fastcgi_pass unix:/var/run/fcgiwrap.socket;
    }


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

An API call looks like this,

    /jack-in-the/sqlite?q=SELECT+foo+FROM+baz

but the CGI script expects this,

    /sqlite?q=SELECT+foo+FROM+baz&box=made-of-ticky-tacky

so the Nginx needs to rewrite the URL.

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
      --wsgi-file foobar.py \
      --socket 127.0.0.1:3031 \
      --callable application \
      --processes 20

Use some high number of processes because they block.

We'll have to adjust the api script so that it works with uWSGI;
once we do, add this to the nginx site. (Try `/etc/nginx/sites-enabled/default`.)

    location /path/to/sqlite {
        include uwsgi_params;
        uwsgi_pass 127.0.0.1:3031;
    }

Restart nginx.

    service nginx restart

Test

    curl localhost/path/to/sqlite?q=SELECT+42+FROM+sqlite_master&boxname=jack-in-the

An example (simple) script would be

    def application(env, start_response):
        start_response('200 OK', [('Content-Type','text/html')])
        return "Hello World"

## Add later
Gzip responses.

## SQLite errors
The SQLite errors are normally pretty good, so an api call with that raises a
SQLite error normally displays the error messages. This includes

* Locked databases
* Ungrammatical SQL

Some of these errors aren't great, like

* Database that the user doesn't have permission to read

We also treat some things as errors that SQLite doesn't:

* Databases that don't exist
