from twisted.internet.protocol import Factory, Protocol, ClientFactory
from twisted.protocols.basic import LineReceiver
from twisted.internet import reactor
from twisted.internet import ssl
import gnupg
import re
from configloader import Configuration

Configuration.default = {
    'SMTP': {
        'host': "",
        'port': 587,
        'localport': 1587
    },
    'IMAP': {
        'host': "",
        'port': 993,
        'localport':1993,
    },
     'privKeyID':"",
     "certFile": "server.pem"
 }
Configuration.load("config.json")
class SMTPClient(LineReceiver):
    # redet mit Uberspace
    def __init__(self, smtp):
        print "Client INIT"
        smtp.smtpclient = self
        self.relay = smtp

    def sendLine(self, line):
        print "Relay -> Server",line
        LineReceiver.sendLine(self,line)

    def lineReceived(self, line):
        print "Server->Relay", line

        self.relay.sendLine(line)

class SMTPClientFactory(ClientFactory):
    def __init__(self, smtp):
        self.smtp=smtp

    def buildProtocol(self, addr):
        print "Client Build Protocol"
        return SMTPClient(self.smtp)

    def clientConnectionLost(self, connector, reason):
        self.smtp.connector.disconnect()
        print 'Client: Lost connection.  Reason:', reason

    def clientConnectionFailed(self, connector, reason):
        print 'Client: Connection failed. Reason:', reason

class SMTP(LineReceiver):
    #redet mit dem iPhone
    def __init__(self):
        self.em = ""
        self.sen = ""
        self.smtpclient = None
        self.state = "preData"
        self.buffer = []

    def sendLine(self, line):
        print "Relay -> iPhone",line
        LineReceiver.sendLine(self,line)

    def connectionMade(self):
        print "connecting to MS"
        self.connector = reactor.connectSSL(Configuration["SMTP.host"],Configuration["SMTP.port"] , SMTPClientFactory(self),ssl.ClientContextFactory())


    def connectionLost(self, reason):
        print "Server", reason

    def lineReceived(self, line):
        print "Client->Relay:", self.state, line

        if self.state=="preData":
            self.smtpclient.sendLine(line)
        elif self.state=="Data":
            self.buffer.append(line)
        elif self.state=="postData":
            self.smtpclient.sendLine(line)


        if line.upper()=="DATA":
            self.state="Data"
        elif line == ".":
            self.state="postData"

            # KeyID = 8F586B2A
            #insert your pgp here
            gpg = gnupg.GPG()
            entry = self.buffer.pop(0)
            while entry != "":
                self.smtpclient.sendLine(entry)
                entry = self.buffer.pop(0)

            signed = gpg.sign("\r\n".join(self.buffer[:-1]),keyid=Configuration["privKeyID"])
            self.smtpclient.sendLine("")
            for entry in str(signed).splitlines():
                self.smtpclient.sendLine(entry)
            #map(self.smtpclient.sendLine, str(signed).splitlines())
            self.smtpclient.sendLine(".")
            self.buffer=[]




class SMTPFactory(Factory):

    def __init__(self):
        pass
    def buildProtocol(self, addr):
        return SMTP()


class IMAPClient(LineReceiver):
    # redet mit Uberspace
    def __init__(self, imap):
        print "Client INIT"
        imap.imapclient = self
        self.relay = imap



    def lineReceived(self, line):
        print "Server->Relay", line

        self.relay.sendLine(line)

class IMAPClientFactory(ClientFactory):
    def __init__(self, imap):
        self.imap=imap

    def buildProtocol(self, addr):
        print "Client Build Protocol"
        return IMAPClient(self.imap)

    def clientConnectionLost(self, connector, reason):
        self.imap.connector.disconnect()
        print 'Client: Lost connection.  Reason:', reason

    def clientConnectionFailed(self, connector, reason):
        print 'Client: Connection failed. Reason:', reason

class IMAP(LineReceiver):
    #redet mit dem iPhone
    def __init__(self):
        self.em = ""
        self.sen = ""
        self.imapclient = None
        self.state = "preFetch"
        self.buffer = []
        self.mregex = re.compile("^([A-Z0-9]+) (UID )?FETCH")
        self.fTag = ""

    def connectionMade(self):
        print "connecting to MS"
        self.connector = reactor.connectSSL(Configuration["IMAP.host"], Configuration["IMAP.port"], IMAPClientFactory(self),ssl.ClientContextFactory())


    def connectionLost(self, reason):
        print "Server", reason

    def lineReceived(self, line):
        print "Client->Relay:", self.state, line

        if self.state=="preFetch":
            self.imapclient.sendLine(line)
        elif self.state=="Fetch":
            self.buffer.append(line)
        elif self.state=="postFetch":
            self.imapclient.sendLine(line)

            # FIXME: Laenge im Header ist falsch

        if self.mregex.match(line.upper()):
            self.state="Fetch"
            print "Fetching"
            m = self.mregex.match(line.upper())
            self.fTag = m.group(1)
            print self.fTag
        elif line.upper().startswith(self.fTag + " OK"):
            self.state="postFetch"
            print self.buffer
'''
            # KeyID = 8F586B2A
            #insert your pgp here
            gpg = gnupg.GPG()
            entry = self.buffer.pop(0)
            while entry != "":
                self.imapclient.sendLine(entry)
                print "Relay -> Server", entry
                entry = self.buffer.pop(0)

            signed = gpg.sign("\r\n".join(self.buffer[:-1]),keyid="8F586B2A")
            self.imapclient.sendLine("")
            for entry in str(signed).splitlines():
                self.imapclient.sendLine(entry)
                print "Relay -> Server", entry
            #map(self.imapclient.sendLine, str(signed).splitlines())
            self.imapclient.sendLine(".")
            self.buffer=[]'''




class IMAPFactory(Factory):

    def __init__(self):
        pass
    def buildProtocol(self, addr):
        return IMAP()

certData = open(Configuration['certFile']).read()

certificate = ssl.PrivateCertificate.loadPEM(certData)
reactor.listenSSL(Configuration["SMTP.localport"], SMTPFactory(),certificate.options())
#reactor.listenSSL(Configuration["IMAP.localport"], IMAPFactory(),certificate.options())
#reactor.listenTCP(1587, SMTPFactory())
reactor.run()
