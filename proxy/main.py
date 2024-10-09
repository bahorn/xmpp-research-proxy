#!/usr/bin/env python
# coding: utf-8

import sys
import click

from twisted.internet import reactor, ssl
from twisted.python import log
from twisted.internet.endpoints import SSL4ServerEndpoint

from server import ProxyServerFactory
from hooks import client_hook, server_hook


@click.command()
@click.argument('target_address')
@click.argument('target_port', type=int)
@click.option('--cert', default='./certs/server.pem')
@click.option('--listen-address', default='0.0.0.0')
@click.option('--listen-port', default=1337, type=int)
def main(target_address, target_port, cert, listen_address, listen_port):
    log.startLogging(sys.stdout)
    certData = open(cert, 'r').read()
    certificate = ssl.PrivateCertificate.loadPEM(certData).options()
    endpoint = SSL4ServerEndpoint(
        reactor, listen_port, certificate, interface=listen_address
    )
    factory = ProxyServerFactory(
        (target_address, target_port),
        client_hook=client_hook,
        server_hook=server_hook
    )
    endpoint.listen(factory)
    reactor.run()


if __name__ == "__main__":
    main()
