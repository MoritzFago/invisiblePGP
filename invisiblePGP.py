from twisted.internet.protocol import Factory, Protocol, ClientFactory
from twisted.protocols.basic import LineReceiver
from twisted.internet import reactor
from twisted.internet import ssl
import gnupg
import re
#import email
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
        print 'Cflient: Connection failed. Reason:', reason

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
        self.state = "prePGP"
        self.buffer = []
        self.beginPGP = re.compile("BEGIN PGP MESSAGE")
        self.endPGP = re.compile("END PGP MESSAGE")

    def sendLine(self, line):
        print "Relay -> Server",line
        LineReceiver.sendLine(self,line)

    def lineReceived(self, line):

        if self.beginPGP.search(line.upper()):
            self.state="PGP"
            print "PGPing"
        elif self.endPGP.search(line.upper()):
            self.buffer.append(line)
            import pdb
            #pdb.set_trace()
            gpg = gnupg.GPG()
            decrypted= gpg.decrypt("\r\n".join(self.buffer))
        #    Par = email.parser.Parser()
        #    emailmsg= Par.parsestr(decrypted)
            for entry in str(decrypted).splitlines():
                print "Server->Relayd", entry
                self.relay.sendLine(entry)
            line =""
            #self.buffer=[]
            self.state="prePGP"



        if self.state=="prePGP":
            print "Server->Relayd", line
            self.relay.sendLine(line)
        elif self.state=="PGP":
            self.buffer.append(line)


            # FIXME: Laenge im Header ist falsch




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
        self.state = "prePGP"
        self.buffer = []
        self.beginPGP = re.compile("BEGIN PGP MESSAGE")
        self.endPGP = re.compile("END PGP MESSAGE")

        self.fTag = ""

    def connectionMade(self):
        print "connecting to MS"
        self.connector = reactor.connectSSL(Configuration["IMAP.host"], Configuration["IMAP.port"], IMAPClientFactory(self),ssl.ClientContextFactory())


    def connectionLost(self, reason):
        print "Server", reason

    def lineReceived(self, line):
        self.imapclient.sendLine(line)

'''
            # KeyID = 7CCA6F8A
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
#reactor.listenSSL(Configuration["SMTP.localport"], SMTPFactory(),certificate.options())
reactor.listenSSL(Configuration["IMAP.localport"], IMAPFactory(),certificate.options())
#reactor.listenTCP(1587, SMTPFactory())
reactor.run()
# FIXME SSLv3?
