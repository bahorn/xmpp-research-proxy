#!/usr/bin/env python
# coding: utf-8
from twisted.internet import defer, protocol, reactor, ssl
from twisted.python import log

from process import XMPPConnection


class ProxyClientProtocol(protocol.Protocol):
    def __init__(self, srv_queue, cli_queue, factory,
                 server_hook=None, client_hook=None):
        self.srv_queue = srv_queue
        self.cli_queue = cli_queue
        self.factory = factory
        self._xmpp_connection = XMPPConnection(client_hook, server_hook)

    def connectionMade(self):
        log.msg("Client: connected to peer")
        self.cli_queue = self.factory.cli_queue
        self.cli_queue.get().addCallback(self.serverDataReceived)

    def serverDataReceived(self, chunk):
        if chunk is False:
            self.cli_queue = None
            log.msg("Client: disconnecting from peer")
            self.factory.continueTrying = False
            self.transport.loseConnection()
            return

        if self.cli_queue:
            log.msg("Client: writing %d bytes to peer" % len(chunk))
            res = self._xmpp_connection.client_chunk(chunk)
            self.transport.write(res)
            self.cli_queue.get().addCallback(self.serverDataReceived)
            return

        self.factory.cli_queue.put(chunk)

    def dataReceived(self, chunk):
        log.msg("Client: %d bytes received from peer" % len(chunk))
        res = self._xmpp_connection.server_chunk(chunk)
        self.factory.srv_queue.put(res)

    def connectionLost(self, why):
        if self.cli_queue:
            self.cli_queue = None
            log.msg("Client: peer disconnected unexpectedly")


class ProxyClientFactory(protocol.ReconnectingClientFactory):
    maxDelay = 10
    continueTrying = True
    protocol = ProxyClientProtocol

    def __init__(self, srv_queue, cli_queue, server_hook=None,
                 client_hook=None):
        self.srv_queue = srv_queue
        self.cli_queue = cli_queue
        self._server_hook = server_hook
        self._client_hook = client_hook

    def buildProtocol(self, addr):
        return ProxyClientProtocol(
            self.srv_queue,
            self.cli_queue,
            self,
            server_hook=self._server_hook,
            client_hook=self._client_hook
        )


class ProxyServer(protocol.Protocol):
    def __init__(self, target, server_hook=None, client_hook=None):
        self._host = target[0]
        self._port = target[1]
        self._server_hook = server_hook
        self._client_hook = client_hook

    def connectionMade(self):
        self.srv_queue = defer.DeferredQueue()
        self.cli_queue = defer.DeferredQueue()
        self.srv_queue.get().addCallback(self.clientDataReceived)

        factory = ProxyClientFactory(
            self.srv_queue,
            self.cli_queue,
            server_hook=self._server_hook,
            client_hook=self._client_hook
        )
        certificate = ssl.CertificateOptions(verify=False)

        reactor.connectSSL(
            self._host,
            self._port,
            factory,
            contextFactory=certificate
        )

    def clientDataReceived(self, chunk):
        log.msg("Server: writing %d bytes to original client" % len(chunk))
        self.transport.write(chunk)
        self.srv_queue.get().addCallback(self.clientDataReceived)

    def dataReceived(self, chunk):
        log.msg("Server: %d bytes received" % len(chunk))
        self.cli_queue.put(chunk)

    def connectionLost(self, why):
        self.cli_queue.put(False)


class ProxyServerFactory(protocol.Factory):
    def __init__(self, target, server_hook=None, client_hook=None):
        self._target = target
        self._server_hook = server_hook
        self._client_hook = client_hook

    def buildProtocol(self, addr):
        return ProxyServer(
            self._target,
            server_hook=self._server_hook,
            client_hook=self._client_hook
        )


def test():
    pass


if __name__ == "__main__":
    test()
