import re
import Utils

RE_PREFIXES = re.compile(r"\bPREFIX=\((\w+)\)(\W+)(?:\b|$)")
RE_CHANMODES = re.compile(
    r"\bCHANMODES=(\w*),(\w*),(\w*),(\w*)(?:\b|$)")
RE_CHANTYPES = re.compile(r"\bCHANTYPES=(\W+)(?:\b|$)")

handlers = {}
descriptions = {}
current_description = None
def handler(f=None, description=None):
    global current_description
    if description:
        current_description = description
        return handler
    name = f.__name__.split("handle_")[1].upper()
    handlers[name] = f
    if current_description:
        descriptions[name] = current_description
        current_description = None
def handle(line, line_split, bot, server):
    handler_function = None
    if len(line_split) > 1:
        if line_split[0][0] == ":":
            if line_split[1] in handlers:
                handler_function = handlers[line_split[1]]
            elif line_split[1].isdigit():
                bot.events.on("received").on("numeric").on(
                    line_split[1]).call(line=line,
                    line_split=line_split, server=server,
                    number=line_split[1])
        elif line_split[0] in handlers:
            handler_function = handlers[line_split[0]]
    if handler_function:
        handler_function(line, line_split, bot, server)
@handler(description="reply to a ping")
def handle_PING(line, line_split, bot, server):
    nonce = Utils.remove_colon(line_split[1])
    server.send_pong(Utils.remove_colon(line_split[1]))
    bot.events.on("received").on("ping").call(line=line,
        line_split=line_split, server=server, nonce=nonce)
@handler(description="the first line sent to a registered client")
def handle_001(line, line_split, bot, server):
    server.set_own_nickname(line_split[2])
    server.send_whois(server.nickname)
    bot.events.on("received").on("numeric").on("001").call(
        line=line, line_split=line_split, server=server)
@handler(description="the extra supported things line")
def handle_005(line, line_split, bot, server):
    isupport_line = Utils.arbitrary(line_split, 3)
    if "NAMESX" in line:
        server.send("PROTOCTL NAMESX")
    match = re.search(RE_PREFIXES, isupport_line)
    if match:
        modes = match.group(1)
        prefixes = match.group(2)
        for i, prefix in enumerate(prefixes):
            if i < len(modes):
                server.mode_prefixes[prefix] = modes[i]
    match = re.search(RE_CHANMODES, isupport_line)
    if match:
        server.channel_modes = list(match.group(4))
    match = re.search(RE_CHANTYPES, isupport_line)
    if match:
        server.channel_types = list(match.group(1))
    bot.events.on("received").on("numeric").on("005").call(
        line=line, line_split=line_split, server=server,
        isupport=isupport_line)
@handler(description="whois respose (nickname, username, realname, hostname)")
def handle_311(line, line_split, bot, server):
    nickname = line_split[2]
    if server.is_own_nickname(nickname):
        target = server
    else:
        target = server.get_user(nickname)
    target.username = line_split[4]
    target.realname = Utils.arbitrary(line_split, 7)
    target.hostname = line_split[5]
@handler(description="on-join channel topic line")
def handle_332(line, line_split, bot, server):
    channel = server.get_channel(line_split[3])
    topic = Utils.arbitrary(line_split, 4)
    channel.set_topic(topic)
@handler(description="on-join channel topic set by/at")
def handle_333(line, line_split, bot, server):
    channel = server.get_channel(line_split[3])
    topic_setter_hostmask = line_split[4]
    nickname, username, hostname = Utils.seperate_hostmask(
        topic_setter_hostmask)
    topic_time = int(line_split[5]) if line_split[5].isdigit(
        ) else None
    channel.set_topic_setter(nickname, username, hostname)
    channel.set_topic_time(topic_time)
@handler(description="on-join user list with status symbols")
def handle_353(line, line_split, bot, server):
    channel = server.get_channel(line_split[4])
    nicknames = line_split[5:]
    nicknames[0] = Utils.remove_colon(nicknames[0])
    for nickname in nicknames:
        if nickname.strip():
            modes = set([])
            while nickname[0] in server.mode_prefixes:
                modes.add(server.mode_prefixes[nickname[0]])
                nickname = nickname[1:]
            user = server.get_user(nickname)
            user.join_channel(channel)
            channel.add_user(user)
            for mode in modes:
                channel.add_mode(mode, nickname)
@handler(description="on user joining channel")
def handle_JOIN(line, line_split, bot, server):
    nickname, username, realname = Utils.seperate_hostmask(line_split[0])
    channel = server.get_channel(Utils.remove_colon(line_split[2]))
    if not server.is_own_nickname(nickname):
        user = server.get_user(nickname)
        channel.add_user(user)
        user.join_channel(channel)
        bot.events.on("received").on("join").call(line=line,
            line_split=line_split, server=server, channel=channel,
            user=user)
    else:
        bot.events.on("self").on("join").call(line=line,
            line_split=line_split, server=server, channel=channel)
        server.send_who(channel.name)
        channel.send_mode()
@handler(description="on user parting channel")
def handle_PART(line, line_split, bot, server):
    nickname, username, hostname = Utils.seperate_hostmask(line_split[0])
    channel = server.get_channel(line_split[2])
    reason = Utils.arbitrary(line_split, 3)
    if not server.is_own_nickname(nickname):
        user = server.get_user(nickname)
        bot.events.on("received").on("part").call(line=line,
            line_split=line_split, server=server, channel=channel,
            reason=reason, user=user)
        channel.remove_user(user)
        if not len(user.channels):
            server.remove_user(user)
    else:
        server.remove_channel(channel)
        bot.events.on("self").on("part").call(line=line,
            line_split=line_split, server=server, channel=channel,
            reason=reason)
@handler(description="unknown command sent by us, oops!")
def handle_421(line, line_split, bot, server):
    print("warning: unknown command '%s'." % line_split[3])
@handler(description="a user has disconnected!")
def handle_QUIT(line, line_split, bot, server):
    nickname, username, hostname = Utils.seperate_hostmask(line_split[0])
    reason = Utils.arbitrary(line_split, 2)
    if not server.is_own_nickname(nickname):
        user = server.get_user(nickname)
        server.remove_user(user)
        bot.events.on("received").on("quit").call(line=line,
            line_split=line_split, server=server, reason=reason,
            user=user)
    else:
        server.disconnect()
@handler(description="someone has changed their nickname")
def handle_NICK(line, line_split, bot, server):
    nickname, username, hostname = Utils.seperate_hostmask(line_split[0])
    new_nickname = Utils.remove_colon(line_split[2])
    if not server.is_own_nickname(nickname):
        user = server.get_user(nickname)
        old_nickname = user.nickname
        user.set_nickname(new_nickname)
        server.change_user_nickname(old_nickname, new_nickname)
        bot.events.on("received").on("nick").call(line=line,
            line_split=line_split, server=server,
            new_nickname=new_nickname, old_nickname=old_nickname,
            user=user)
    else:
        old_nickname = server.nickname
        server.set_own_nickname(new_nickname)
        bot.events.on("self").on("nick").call(line=line,
            line_split=line_split, server=server,
            new_nickname=new_nickname, old_nickname=old_nickname)
@handler(description="something's mode has changed")
def handle_MODE(line, line_split, bot, server):
    nickname, username, hostname = Utils.seperate_hostmask(line_split[0])
    target = line_split[2]
    is_channel = target[0] in server.channel_types
    if is_channel:
        channel = server.get_channel(target)
        remove = False
        args = line_split[4:]
        for i, char in enumerate(line_split[3]):
            if char == "+":
                remove = False
            elif char == "-":
                remove = True
            else:
                if char in server.channel_modes:
                    if remove:
                        channel.remove_mode(char)
                    else:
                        channel.add_mode(char)
                elif char in server.mode_prefixes.values():
                    nickname = args.pop(0)
                    if remove:
                        channel.remove_mode(char, nickname)
                    else:
                        channel.add_mode(char, nickname)
                else:
                    args.pop(0)
    elif server.is_own_nickname(target):
        modes = Utils.remove_colon(line_split[3])
        remove = False
        for i, char in enumerate(modes):
            if char == "+":
                remove = False
            elif char == "-":
                remove = True
            else:
                if remove:
                    server.remove_own_mode(char)
                else:
                    server.add_own_mode(char)
@handler(description="I've been invited somewhere")
def handle_INVITE(line, line_split, bot, server):
    nickname, username, hostname = Utils.seperate_hostmask(line_split[0])
    target_channel = Utils.remove_colon(line_split[3])
    user = server.get_user(nickname)
    bot.events.on("received").on("invite").call(
        line=line, line_split=line_split, server=server,
        user=user, target_channel=target_channel)
@handler(description="we've received a message")
def handle_PRIVMSG(line, line_split, bot, server):
    nickname, username, hostname = Utils.seperate_hostmask(line_split[0])
    user = server.get_user(nickname)
    message = Utils.arbitrary(line_split, 3)
    message_split = message.split(" ")
    target = line_split[2]
    action = message.startswith("\01ACTION ") and message.endswith("\01")
    if action:
        message = message.replace("\01ACTION ", "", 1)[:-1]
    if target[0] in server.channel_types:
        channel = server.get_channel(line_split[2])
        bot.events.on("received").on("message").on("channel").call(
            line=line, line_split=line_split, server=server,
            user=user, message=message, message_split=message_split,
            channel=channel, action=action)
        channel.log.add_line(user.nickname, message, action)
    elif server.is_own_nickname(target):
        bot.events.on("received").on("message").on("private").call(
            line=line, line_split=line_split, server=server,
            user=user, message=message, message_split=message_split,
            action=action)
@handler(description="response to a WHO command for user information")
def handle_352(line, line_split, bot, server):
    user = server.get_user(line_split[7])
    user.username = line_split[4]
    user.realname = Utils.arbitrary(line_split, 10)
    user.hostname = line_split[5]
@handler(description="response to an empty mode command")
def handle_324(line, line_split, bot, server):
    channel = server.get_channel(line_split[3])
    modes = line_split[4]
    if modes[0] == "+" and modes[1:]:
        for mode in modes[1:]:
            if mode in server.channel_modes:
                channel.add_mode(mode)
@handler(description="channel creation unix timestamp")
def handle_329(line, line_split, bot, server):
    channel = server.get_channel(line_split[3])
    channel.creation_timestamp = int(line_split[4])
@handler(description="nickname already in use")
def handle_433(line, line_split, bot, server):
    pass