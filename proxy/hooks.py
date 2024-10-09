"""
Hooks for stanzas
"""
import base64
from twisted.python import log


def print_list_stanzas(label, stanzas):
    print(stanzas)
    log.msg(label, ' - ', stanzas)


def decode(message):
    body = message.split('REPLACEME')[1]
    return base64.b64decode(body).decode('utf-8')


def is_encoded_message(message):
    return 'REPLACEME' in message


def potentially_replace(stanza):
    if is_encoded_message(str(stanza)):
        print('DOING REPLACEMENT')
        try:
            res = decode(str(stanza))
            print('>>>>', res)
            return res
        except Exception as e:
            print(f'Exception: {e}')
            return stanza
    return stanza


def client_hook(state, stanza):
    print('######### called')
    if stanza.complete():
        print_list_stanzas('client', stanza)
        return potentially_replace(stanza)
    return stanza


def server_hook(state, stanza):
    print('######### called')
    if stanza.complete():
        print_list_stanzas('server', stanza)
        return potentially_replace(stanza)
    return stanza
