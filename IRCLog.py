import re

class Line(object):
    def __init__(self, sender, message, action, from_self):
        self.sender = sender
        self.message = message
        self.action = action
        self.from_self = from_self

class Log(object):
    def __init__(self, bot):
        self.lines = []
        self.max_lines = 64
        self._skip_next = False
    def add_line(self, sender, message, action, from_self=False):
        if not self._skip_next:
            line = Line(sender, message, action, from_self)
            self.lines.insert(0, line)
            if len(self.lines) > self.max_lines:
                self.lines.pop()
        self._skip_next = False
    def get(self, index=0, **kwargs):
        from_self = kwargs.get("from_self", True)
        for line in self.lines:
            if line.from_self and not from_self:
                continue
            return line
    def find(self, pattern, **kwargs):
        from_self = kwargs.get("from_self", True)
        not_pattern = kwargs.get("not_pattern", None)
        for line in self.lines:
            if line.from_self and not from_self:
                continue
            elif re.search(pattern, line.message):
                if not_pattern and re.search(not_pattern, line.message):
                    continue
                return line
    def skip_next(self):
        self._skip_next = True
