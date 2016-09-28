# IT-Cat's carma bot by @evgfilim1

### Install guide:
```sh 
$ sudo pip3 install python-telegram-bot
```
If you have `"pip3: command not found"` error, check that you have `python3` and `pip3` installed (check your package manager manual to find out how to install packages).

Then do these steps to set up the bot:
```sh
$ mkdir botlibs botdata
$ echo 'TOKEN = "Here goes your bot API token"' >> botlibs/token.py
$ echo 'creatorid = Here goes your Telegram user ID (as number)' >> botlibs/token.py
```

### Running bot:

```sh 
$ python3 bot.py
```
