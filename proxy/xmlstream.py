"""
XML Stream Processing
"""
from enum import Enum, auto

from defusedxml import ElementTree as ET


class TokenTransition(Enum):
    SELF = auto()  # Keep in this token
    NEXT = auto()  # Next char goes into the next token
    CURR = auto()  # This char goes into the next token


class Token:
    """
    Base class for a token
    """

    def __init__(self):
        self._body = ""

    def add_char(self, c):
        res = self._transition(c)
        match res:
            case TokenTransition.SELF:
                self._body += c
            case TokenTransition.NEXT:
                self._body += c
            case TokenTransition.CURR:
                pass
        return res

    def __str__(self):
        return self._body


class ContentToken(Token):
    def __init__(self):
        super().__init__()

    def _transition(self, c):
        if c == '<':
            return TokenTransition.CURR
        return TokenTransition.SELF


class MarkupType(Enum):
    OPEN = auto()
    CLOSE = auto()
    SELFCONTAINED = auto()
    RESET = auto()


class MarkupToken(Token):
    # These are incomplete

    def __init__(self):
        super().__init__()
        self._inquote_single = False
        self._inquote_double = False
        self._done = False

    def _transition(self, c):
        # Handle quotes
        if c == '"' and not self._inquote_single:
            if self._inquote_double:
                self._inquote_double = False
            else:
                self._inquote_double = True

        if c == '\'' and not self._inquote_double:
            if self._inquote_single:
                self._inquote_single = False
            else:
                self._inquote_single = True

        if self._inquote_double or self._inquote_single or c != '>':
            return TokenTransition.SELF

        return TokenTransition.NEXT

    def is_declaration(self):
        return len(self._body) > 4 and \
            self._body[0:2] == '<?' and \
            self._body[-2:] == '?>'

    def is_comment(self):
        return len(self._body) > 7 and \
                self._body[0:4] == '<!--' and \
                self._body[-3:] == '-->'

    def is_selfcontained(self):
        return len(self._body) > 3 and \
                self._body[0] == '<' and \
                self._body[-2:] == '/>'

    def is_open(self):
        selfcontained = self.is_declaration() or \
                self.is_comment() or \
                self.is_selfcontained()

        return (not selfcontained) and (not self.is_close())

    def is_close(self):
        return len(self._body) > 3 and \
                self._body[0:2] == '</' and \
                self._body[-1] == '>'

    def is_valid(self):
        known_type = \
            self.is_declaration() or \
            self.is_comment() or \
            self.is_selfcontained() or \
            self.is_open() or \
            self.is_close()

        return known_type and self._body[0] == '<' and self._body[-1] == '>'

    def is_reset(self):
        # hack, to deal with stream resets
        return self._body in ["<?xml version='1.0'?>", '<?xml version="1.0"?>']

    def markup_type(self):
        if self.is_open():
            return MarkupType.OPEN
        elif self.is_close():
            return MarkupType.CLOSE
        elif self.is_reset():
            return MarkupType.RESET

        return MarkupType.SELFCONTAINED

    def __str__(self):
        return self._body


class TokenSequence:
    def __init__(self):
        self._seq = []
        self._complete = False

    def add(self, token):
        self._seq.append(token)

    def complete(self, state=None):
        if state:
            self._complete = state

        return self._complete

    def __str__(self):
        return ''.join(map(lambda x: str(x), self._seq))

    def to_etree(self):
        if len(self._seq) == 0:
            return None
        return ET.fromstring(str(self))

    def __iter__(self):
        return self._seq.__iter__()


class BasicXMLTokenizer:
    """
    Extract 'tokens' from an XML byte stream.

    Cycles between Content and Markup tokens, adding characters until it has to
    switch to the other token type.
    """
    TOKEN_TYPES = [ContentToken, MarkupToken]

    def __init__(self):
        self._curr_token = ContentToken()
        self._token_transition = 0

    def _transition(self):
        res = [self._curr_token]
        self._token_transition += 1
        self._token_transition %= len(self.TOKEN_TYPES)
        self._curr_token = self.TOKEN_TYPES[self._token_transition]()
        return res

    def add_char(self, c):
        res = []

        match self._curr_token.add_char(c):
            case TokenTransition.SELF:
                pass
            case TokenTransition.CURR:
                res = self._transition()
                # recursion depth here is limited
                res += self.add_char(c)
            case TokenTransition.NEXT:
                res = self._transition()

        return res


class StanzaExtractor:
    """
    Given a sequence of tokens, convert them into stanzas.
    """

    def __init__(self, depth):
        self._threshold = depth
        self._curr_depth = 0
        self._all = []
        self.reset()

    def reset(self):
        self._curr_sequence = TokenSequence()

    def _maybe_add_token(self, token, depth):
        # Basic sanity check
        if 0 > self._curr_depth:
            raise Exception("Negative Depth")

        self._curr_sequence.add(token)

    def add(self, token):
        original_depth = self._curr_depth
        depth = self._curr_depth
        next_depth = self._curr_depth

        reset = False
        selfcontained = False

        if isinstance(token, MarkupToken):
            match token.markup_type():
                case MarkupType.SELFCONTAINED:
                    selfcontained = True
                    depth += 1
                case MarkupType.OPEN:
                    depth += 1
                    next_depth = depth
                case MarkupType.CLOSE:
                    next_depth -= 1
                case MarkupType.RESET:
                    next_depth = 0
                    depth = 1
                    reset = True

        self._maybe_add_token(token, depth)
        self._curr_depth = next_depth

        res = self._curr_sequence

        # self._all.append((depth, str(token)))
        # print('> res ', self._all)

        if reset:
            self.reset()
            return res

        # If we are below the threshold, emit a non-complete stanza
        if self._threshold > depth:
            self.reset()
            return res

        # If we were above the threshold, and go below it, emite a complete
        # stanza
        if next_depth < self._threshold and original_depth >= self._threshold:
            res.complete(True)
            self.reset()
            return res

        if selfcontained and self._threshold == depth:
            res.complete(True)
            self.reset()
            return res


class XMLStanzaStream:
    """
    Add blocks of text to the stream, obtain stanzas if any were finished in
    the block.

    Does not consider the text, only considers the depth.
    """

    def __init__(self, depth=2):
        self._depth = depth
        self.reset()

    def reset(self):
        self._tokenizer = BasicXMLTokenizer()
        self._extractor = StanzaExtractor(self._depth)

    def add(self, contents):
        stanzas = []
        for c in contents:
            tokens = self._tokenizer.add_char(c)
            if not tokens:
                continue
            for token in tokens:
                potential_stanza = self._extractor.add(token)
                if potential_stanza:
                    stanzas.append(potential_stanza)
        return stanzas


def to_markup_token(s):
    t = MarkupToken()
    check = [t.add_char(c) for c in s]
    assert check[:-1] == [TokenTransition.SELF for i in check[:-1]]
    assert check[-1] == TokenTransition.NEXT
    return t


def markup_type_asserts(tag, values):
    token = to_markup_token(tag)
    assert token.is_valid() is values[0]
    assert token.is_open() is values[1]
    assert token.is_close() is values[2]
    assert token.is_declaration() is values[3]
    assert token.is_comment() is values[4]
    assert token.is_selfcontained() is values[5]


def test_markup_tag():
    TEST_TAGS = [
        ('<A1>', (True, True, False, False, False, False)),
        ('</A2>', (True, False, True, False, False, False)),
        ('<!-- uwu -->', (True, False, False, False, True, False)),
        ('<?xml?>', (True, False, False, True, False, False)),
        ('<xml />', (True, False, False, False, False, True)),
        ('<xml version="1.0"/>', (True, False, False, False, False, True)),
        ('<blah a="B">', (True, True, False, False, False, False)),
        ('<blah a=\'B\'>', (True, True, False, False, False, False)),
        ("<iq to='juliet@capulet.com' type='result' id='vc1'/>",
            (True, False, False, False, False, True)),
        ('<?xml value=test?>',
            (True, False, False, True, False, False, False)),
        ('<?xml value="test"?>',
            (True, False, False, True, False, False, False)),
        ('<?xml value="1.0" ?>',
            (True, False, False, True, False, False, False)),
        ('<stream:features>',
            (True, True, False, False, False, False, False)),
        ("<mechanisms xmlns='urn:ietf:params:xml:ns:xmpp-sasl'>",
            (True, True, False, False, False, False, False)),
        ("<stream:stream id='6410827807996709889' version='1.0' xml:lang='en' xmlns:stream='http://etherx.jabber.org/streams' from='xmpp-research-proxy.lan' xmlns='jabber:client'>",
            (True, True, False, False, False, False, False))
    ]

    for tag, values in TEST_TAGS:
        markup_type_asserts(tag, values)


def test_stanza_extraction():
    teststr = '<a><A1 uwu="magic"><A2><A3>uwu</A3></A2></A1></a>'
    stanzastream = XMLStanzaStream(depth=2)

    found = False
    for idx, stanza in enumerate(stanzastream.add(teststr)):
        if stanza.complete():
            assert str(stanza) == '<A1 uwu="magic"><A2><A3>uwu</A3></A2></A1>'
            found = True
    assert found


def test_file_extraction():
    stanzastream = XMLStanzaStream(depth=2)
    f = open('./tests/test.xml', 'r')
    data = f.read()

    for i in range(100):
        for idx, stanza in enumerate(stanzastream.add(data)):
            if stanza.complete():
                stanza.to_etree()

    f.close()


def test():
    test_markup_tag()
    test_stanza_extraction()
    test_file_extraction()


if __name__ == "__main__":
    test()
