# IT-Cat's carma bot by @mrsteyk (original @evgfilim1)

Install guide:
```sh
$ sudo pip3 install virtualenv # or how the fuck its done
$ python3 -m virtualenv .venv
$ . .venv/bin/activate
(.venv) $ pip install -r requirements.txt
(.venv) $ echo 'TOKEN = "Here goes your bot API token"' > bottoken.py
(.venv) $ echo 'creatorid = user_id_as_a_number' >> bottoken.py
```

Running bot:

``` (.venv) $ python bot.py```
