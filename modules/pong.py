

class Module(object):
    def __init__(self, bot):
        bot.events.on("received").on("command").on("ping"
            ).hook(self.pong, help="Ping pong!")

    def pong(self, event):
        event["stdout"].write("Pong!")
