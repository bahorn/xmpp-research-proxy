"""
To parse markup tags, to determine if its a comment, open/close/selfcontained
or a declaration.
"""


class RejectChar(Exception):
    pass


class Token:
    def __init__(self):
        self._body = ''

    def add_char(self, c):
        self._validate(c)
        self._body.append(c)


class OpenTag(Token):
    def validate(self, c):
        if len(self._body) > 0:
            raise RejectChar()

        if c != '<':
            raise RejectChar()


class CloseTag(Token):
    def validate(self, c):
        if len(self._body) > 0:
            raise RejectChar()

        if c != '>':
            raise RejectChar()


class OpenQuote(Token):
    pass


class CloseQuote(Token):
    pass


class OpenSingleQuote(OpenQuote):
    def validate(self, c):
        if len(self._body) > 0:
            raise RejectChar()

        if c != '\'':
            raise RejectChar()


class CloseSingleQuote(Token):
    def validate(self, c):
        if len(self._body) > 0:
            raise RejectChar()

        if c != '\'':
            raise RejectChar()


class OpenDoubleQuote(OpenQuote):
    def validate(self, c):
        if len(self._body) > 0:
            raise RejectChar()

        if c != '"':
            raise RejectChar()


class CloseDoubleQuote(Token):
    def validate(self, c):
        if len(self._body) > 0:
            raise RejectChar()

        if c != '"':
            raise RejectChar()


class Character(Token):
    def validate(self, c):
        if c in '<>"\'':
            raise RejectChar()


class Seperator(Token):
    def validate(self, c):
        if c not in ' ':
            raise RejectChar()


class MarkupStreamTokenizer:
    def __init__(self):
        pass

    def add_char(self):
        return None


class Attribute:
    def __init__(self, name, value=None):
        pass


class Quote:
    pass


class Tag:
    pass


class Comment(Tag):
    pass


class Declaration(Tag):
    pass


class Markup:
    def __init__(self, tokens):
        self._tokens = tokens


def test():
    pass


if __name__ == "__main__":
    test()
