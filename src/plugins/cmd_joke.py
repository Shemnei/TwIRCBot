import random
import time

import master


class IRCPlugin(master.CommandPlugin):

    COOL_DOWN = 5

    JOKES = ["Did you here about the guy whose whole left side was cut off? He is all right now!",
             "I used to be a banker, but then i lost interest.",
             "Why do mermaids wear sea-shells? Because b-shells are too small",
             "I wondered why the baseball was getting bigger. Then it hit me!",
             "What is the difference between a snowman and a snowwoman? Snowballs!",
             "Why did the scarecrow get promoted? Because he was outstanding in his field.",
             "I'm reading a book about anti-gravity. It's impossible to put down.",
             "I used to think the brain was the most important organ. Then I thought, look what’s telling me that.",
             "while true - Famous last words.",
             "Knock, knock. Race condition. Who's there?",
             "I've got a really good UDP joke to tell you, but I don't know if you'll get it ...",
             "A UDP packet walks into a bar, no one acknowledges him."]

    def __init__(self):
        super().__init__()
        self.__last_used = None
        random.seed()

    def get_regex(self):
        return r"PRIVMSG #\w+ :!joke$"

    def cmd(self, message):
        if not self.__last_used or (time.time() - self.__last_used > IRCPlugin.COOL_DOWN):
            self.connection.add_chat_msg(random.choice(IRCPlugin.JOKES))
            self.__last_used = time.time()

    def get_description(self):
        return "!jokes - Tells a joke"
