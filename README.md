# XMPP Research Proxy

Back in late 2023 I decided to do some sec research into XMPP clients, based on
what a server could do.
Project didn't really work out, and I ended up burning a ton of time fruitlessly
fuzzing pillow.

This repo just contains my test server and client because maybe someone might
get some use out of it.

The proxy is meant to sit infront of another server, and you can use the code in
hooks.py to change things.
I implemented a client that can send messages and do stanza injection (like a
lot of the research on other chat protocols based on xmpp [zoom, etc]).

Does some interesting xml stream procesing, which maybe you can steal or
repurpose.

## License

MIT
