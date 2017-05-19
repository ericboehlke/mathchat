import sys
import re
from sympy import sympify
from twisted.web.static import File
from twisted.python import log
from twisted.web.server import Site
from twisted.internet import reactor

from autobahn.twisted.websocket import WebSocketServerFactory, \
    WebSocketServerProtocol

from autobahn.twisted.resource import WebSocketResource

from twisted.python.logfile import DailyLogFile

log.startLogging(DailyLogFile.fromFullPath("server.log"))

class SomeServerProtocol(WebSocketServerProtocol):
    def onOpen(self):
        try:
            self.factory.register(self)
        except:
            pass
        
    def connectionLost(self, reason):
        try:
            self.factory.unregister(self)
        except:
            pass
    def onMessage(self, payload, isBinary):
        try:
            self.factory.communicate(self, payload, isBinary)
        except:
            pass
        
class CalculatorFactory(WebSocketServerFactory):
    def __init__(self, *args, **kwargs):
        super(CalculatorFactory, self).__init__(*args, **kwargs)
        self.clients = {}
        self.history = [eqn+' = '+str(sympify(eqn)) for eqn in ['2+2', '6/2*(1+2)', '1/3', '1/3.', '2^5', '2**8','1+1*0+1', '(4+8)*(19-7)', '5+5', '3*4']]

    def register(self, client):
        self.clients[client.peer] = client
        payload = ','.join(self.history)
        payload = payload.encode('utf8')
        client.sendMessage(payload, False)

    def unregister(self, client):
        self.clients.pop(client.peer)

    def communicate(self, client, payload, isBinary):
        equation = payload.decode("utf-8")
        pattern = re.compile("^[0-9+\-*\/^ .()]+$")
        if pattern.match(equation):
            try:
                solved = (equation + ' = ' + str(sympify(equation)))
            except: 
                solved = (equation + ' = error')
        else:
            solved = (equation + ' = error')
        self.history.pop(0)
        self.history.append(solved)
        payload = ','.join(self.history)
        log.msg(payload)
        payload = payload.encode('utf8')
        for peer in list(self.clients):
            try: 
                self.clients[peer].sendMessage(payload, isBinary)
            except:
                self.clients.pop(peer)
        
if __name__ == "__main__":
    log.startLogging(sys.stdout)

    # static file server seving index.html as root
    root = File(".")

    factory = CalculatorFactory(u"ws://127.0.0.1:8080")
    factory.protocol = SomeServerProtocol
    resource = WebSocketResource(factory)
    # websockets resource on "/ws" path
    root.putChild(b"ws", resource)

    site = Site(root)
    reactor.listenTCP(8080, site)
    while True:
        try:
            log.msg('starting reactor.')
            reactor.run()
        except:
            log.err()