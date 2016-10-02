# IT-Cat's carma bot by @evgfilim1

### Install guide:
```bash 
$ sudo pip3 install python-telegram-bot
```
If you have `"pip3: command not found"` error, check that you have `python3` and `pip3` 
installed (check your package manager manual to find out how to install packages).

If you don't know, how to create new bot in Telegram, google it, there are a lot of docs :)
But don't forget to disable privacy mode

Then do these steps to set up the bot:
```bash
$ git clone https://github.com/evgfilim1/itcat_carmabot
$ cd itcat_carmabot
$ mkdir botdata
$ cp botlibs/settings.example.py botlibs/settings.py
$ nano botlibs/settings.py
```
Change example values to your ones, then press `Ctrl+X`, `Y`.

### Running bot:

Simply type in your shell:
```bash 
$ python3 bot.py
```
### Setting up bot in chat:
Link it to yours chat using ```
/start getlink
```
