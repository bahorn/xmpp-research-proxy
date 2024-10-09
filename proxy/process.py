#!/usr/bin/env python
# coding: utf-8
from xmlstream import XMLStanzaStream


def apply_hook(stanzas, fun):
    return [fun(stanza) for stanza in stanzas]


def to_network(stanza_list):
    return ''.join(map(str, stanza_list)).encode('utf-8')


def identity(x):
    return x


def filter_none(stanza_list):
    return list(filter(lambda x: x is not None, stanza_list))


def wrap_state(state, fun):
    def wrapped(stanza):
        return fun(state, stanza)

    return wrapped


class XMPPConnection:
    """
    Process a connection, extract stenzas and apply hooks to them.
    """

    def __init__(self, server_hook=identity, client_hook=identity):
        self._client_stream = XMLStanzaStream(2)
        self._server_stream = XMLStanzaStream(2)
        self._state = {}
        self._client_hook = client_hook if client_hook else identity
        self._server_hook = server_hook if server_hook else identity

        self._bypass = False
        self._no_modification = False

    def client_chunk(self, data):
        if self._bypass:
            return data

        res = self._client_stream.add(data.decode('utf-8'))

        res = filter_none(res)
        res = apply_hook(res, wrap_state(self._state, self._client_hook))
        res = filter_none(res)

        if self._no_modification:
            return data

        return to_network(res)

    def server_chunk(self, data):
        if self._bypass:
            return data

        res = self._server_stream.add(data.decode('utf-8'))

        res = filter_none(res)
        res = apply_hook(res, wrap_state(self._state, self._server_hook))
        res = filter_none(res)

        if self._no_modification:
            return data

        return to_network(res)
