Slacker
=======

This application is a tool used by Marketplacer to allocate GitHub
Pull Request reviews to peers.


Service dependencies
--------------------

    $ docker-compose up -d

Setup
-----

Install all the python deps

    $ python -mvenv .venv
    $ . .venv/bin/activate
    $ pip install poetry
    $ poetry install

Create a database if necessary

    $ psql -h localhost -U postgres template1 -e 'CREATE DATABASE slacker_dev'

Create the schema

    $ alembic upgrade head

Running the slack bot
---------------------

    $ python -mslacker.bot

Running the web app
-------------------

    $ FLASK_APP=slacker.webapp flask run

It runs on localhost:5000

Running the tests
-----------------

    $ pytest

Viewing the test coverage report
--------------------------------

First, run the tests with coverage enabled

    $ ./script/ci/run-tests.sh

On linux

    $ xdg-open htmlcov/index.html

On OSX

    $ open htmlcov/index.html

On windows, probably (update this doc if I'm wrong please)

    $ edge htmlcov/index.html

Credentials
-----------

The bot (and the webapp) access github PR data by using a "Personal
Access Token". You should generate your own and put it in `.env`. You
will need to select the scopes `repo`, `read:project` and `read:user`

The bot (and the webapp) access slack by using both a bot token and a
web app token. To test things locally, you will need to create your
own application definition as well as having admin on a slack
workspace in order to add the app to it. I suggest creating your own
free tier slack workspace for that.

You will need to configure the application definition.

In "Settings >> Socket Mode", you need to tick the "Enable Socket
Mode" option.

In "Features >> Interactivity & Shortcuts", you need to add a shortcut
with Name: Review, Short Description: Request a PR Review, Callback
ID: review

In "Features >> Event Subscriptions", you need to subscribe to

 * message.channels
 * message.groups
 * message.im

In "Features >> OAuth & Permissions >> Bot Token Scopes" section, you
will need the following:

 * channels:history
 * channels:read
 * chat:write
 * commands
 * groups:history
 * groups:read
 * im:history
 * im:read
 * mpim:history
 * mpim:read
 * users:read
 * users:read.email

