from socket import *
import sys, re

serverAddr = ("", 5001)
serverSocket = socket(AF_INET, SOCK_DGRAM)
serverSocket.bind(serverAddr)
print "ready to recieve"
while 1:
    message, clientAddrPort = serverSocket.recvfrom(2048)
    print "from %s: rec'd '%s" % (repr(clientAddrPort), message)
    print "%s" % message
    confirmation = "Got your message! send the next one!"
    serverSocket.sendto(confirmation, clientAddrPort)



