Highly modular Twitch Bot
=========================

STATUS: WORKING / IN DEVELOPMENT
REQUIRES: Python >= 3.5, gtts, pillow


Readme coming soon for now look into /src/plugins for example usage

To start the bot run `/src/bot.py`
You need to change `nick_name` and `oauth_token` from `/src/cfg.py` to your account [OAuth Generator](http://twitchapps.com/tmi/)

Tested on: Windows 10 and Ubuntu 16.04.1

------

TODO:


- logging
- display cheers in gui
- have viewer list on side of gui and count on top


Errors:
    -> Windows CMD Encoding: if UnicodeEncodeError ->
        - Set cmd font to font supporting utf-8 and type chcp 65001(changing cmd codec to utf-8) into cmd before running bot
        - Working on fix
