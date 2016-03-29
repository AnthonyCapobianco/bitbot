import signal
from random import randint

QUOTES = {
    "You can build a throne with bayonets, but it's difficult to sit on it." : "Boris Yeltsin",
    "We don't appreciate what we have until it's gone. Freedom is like that. It's like air. When you have it, you don't notice it." : "Boris Yeltsin",
    "Storm clouds of terror and dictatorship are gathering over the whole country... They must not be allowed to bring eternal night." : "Boris Yeltsin",
    "They accused us of suppressing freedom of expression. This was a lie and we could not let them publish it." : "Nelba Blandon, as director of censorship, Nicaragua",
    "Death solves all problems - no man, no problem." : "Joseph Stalin",
    "Make the lie big, make it simple, keep saying it, and eventually they will believe it." : "Adolf Hitler",
    "If we don't end war, war will end us." : "H.G. Wells",
    "All that is necessary for evil to succeed is for good men to do nothing." : "Edmund Burke",
    "Live well. It is the greatest revenge." : "The Talmud",
    "To improve is to change, so to be perfect is to have changed often." : "Winston Churchill",
    "I believe it is peace for our time." : "Neville Chamberlain",
    "Orbiting Earth in the spaceship, I saw how beautiful our planet is. People, let us preserve and increase this beauty, not destroy it!" : "Yuri Gagarin",
    "Science is not everything, but science is very beautiful." : "Robert Oppenheimer",
    "We choose to go to the Moon! We choose to go to the Moon in this decade and do the other things, not because they are easy, but because they are hard." : "",
    "You teach a child to read, and he or her will be able to pass a literacy test." : "George W Bush",
    "I know the human being and fish can coexist peacefully." : "George W Bush",
    "They misunderestimated me." : "George W Bush",
    "I'm an Internet expert too." : "Kim Jong Il",
    "So long, and thanks for all the fish" : "",
    "It is a lie that I made the people starve." : "Nicolae Ceaușescu",
    "As far as I know - effective immediately, without delay." : "Günter Schabowski"
}

class Module(object):
    def __init__(self, bot):
        self.bot = bot
        signal.signal(signal.SIGINT, self.SIGINT)
        signal.signal(signal.SIGUSR1, self.SIGUSR1)

    def SIGINT(self, signum, frame):
        print()
        for server in self.bot.servers.values():
            server.send_quit(self.random_quote())
            self.bot.register_write(server)
        self.bot.running = False

    def SIGUSR1(self, signum, frame):
        print("Reloading config file")
        self.bot.config_object.load_config()

    def random_quote(self):
        quote = list(QUOTES)[randint(0, len(QUOTES)-1)]
        return (" - " if QUOTES[quote] else "").join([quote,
            QUOTES[quote]])