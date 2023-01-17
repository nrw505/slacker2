Slacker
=======

This application is a tool used by Marketplacer to allocate GitHub
Pull Request reviews to peers.


Service dependencies
--------------------

    $ docker-compose up -d

Setup
-----

    $ python -mvenv .venv
    $ . .venv/bin/activate
    $ pip install pypoetry
    $ poetry install

Running the slack bot
---------------------

    $ ??

Running the web app
-------------------

    $ FLASK_APP=slacker.webapp flask run

It runs on localhost:5000

Credentials
-----------

The bot (and the webapp) access github PR data by using a "Personal
Access Token". You should generate your own and put it in `.env`. You
will need to select the scopes `repo`, `read:project` and `read:user`
