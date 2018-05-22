#! /bin/python
from socket import *
import time
import sys, re , string

#split packet contents 
def splitPacket(data):
    array = data.partition("*")
    return array

#splits Head
def splitHead(data):
    array = data.split(":")
    return array 

#put file in server directory
def putFile(conn, data, head, buff, clientAddrPort):
    fileName = str(head[3])
    serverFile = open(fileName.strip(),'w+')
    previousPacket = 0
    while True:
        if not data:
            break
        messageReceived = splitPacket(data)
        h = messageReceived[0].split(":")
        if h[2] == previousPacket:
            conn.sendto("Packet number " + previousPacket + "  already received!", clienAddrPort)
            continue
        serverFile.write(messageReceived[2])      #write data to a file
        print "Server received packet " + h[2] + ": " + messageReceived[2]
        conn.sendto("Received packet: " + messageReceived[0], clientAddrPort)
        print "Ackowledgement sent for packet: " + h[2]
        try:
            data, clientAddrPort = conn.recvfrom(buff)
        except:
            break;
        previousPacket += 1
    serverFile.close()
    print "Succesfully downloaded the file."

#builds header for packet
def buildHeader(choice, identifier, packetNum, file_name, fileSize):
    header = str(choice) + chr(58) + str(identifier) + chr(58) + str(packetNum) + chr(58) + file_name + chr(58) + str(fileSize) + chr(42)
    return header

#builds packet    
def buildPacket(header, buff, f): #builds packet
    availableSpace = buff - len(header) 
    space = availableSpace
    payload = header
    while space > 0:
        char = f.read(1)
        if not char:
            return (payload, -1)
        payload += char
        space -= 1
    return (payload, 1)

#counts the number of characters in file    
def getFileSize(file_name):
    try:
        with open(file_name, 'r') as f:
            data=f.read().replace('\n','')
            f.close()
            return len(data)
    except IOError as e:
        print "No such file or directory. Try again."
        sys.exit()
        
#sends file to client 
def sendFile(file_name, conn, buff, clientAddrPort):
    print "Sending file..."
    packetNum = 1 # keep track of packet count 
    ack = False # boolean to keep track if acknowledgment arrived
    fileSize = getFileSize(file_name) #getFileSize in byte
    identifier = 1
    timeout = 4;
    try:
        with open(file_name, 'r') as f:
            while True:
                header = buildHeader(1, identifier, packetNum, file_name, fileSize)
                packet, status = buildPacket(header, buff, f)
                start = time.time()
                if(conn.sendto(packet, clientAddrPort)):
                    print "Packet #" + str(packetNum) + " sent. Waiting for acknowledgement."
                    ack, clientAddrPort = conn.recvfrom(buff)
                    tries = 1
                    while not ack:
                        end = time.time()
                        elapsedT = end - start
                        if tries == 16:
                            print "Acknowledgement not received. Giving up!"
                            sys.exit()
                        if elapsedT >= timeout: 
                            conn.sendto(packet, clientAddrPort)
                            start = time.time()
                            tries += 1
                    roundTripTime = 2 * (time.time() - start)
                    packetNum += 1
                    print ack
                else:
                    conn.sendto(packet, clientAddrPort)
                if status == -1:
                    break
    except IOError as e:
        print "No such file or directory. Try again."
        sys.exit()
        


#initialize socket and accept connection
def listen():
    #set host and address
    serverAddr = ("", 50000)
    #create socket, bind port, and listen
    serverSocket = socket(AF_INET, SOCK_DGRAM)
    serverSocket.bind(serverAddr)
    print "Binding datagram socket to %s" % repr(serverAddr)
    #serverSocket.listen(5)
    print "Server listening..."
    # establish connection with client
    # conn = serverSocket.accept()
    #print "Got connection from" + str(addr)
    return serverSocket

# starts server
def startServer():
    serverSocket = listen()
    #set buffer size
    buff = 100
    data, clientAddrPort = serverSocket.recvfrom(buff)
    # determine what type of request it is
    messageRecieved = splitPacket(data) 
    head = messageRecieved[0].split(":")
    print head
    requestType = head[0] #retrieve request type
    #determine if get or put
    if(requestType == '1'):
        putFile(serverSocket, data, head, buff, clientAddrPort)
        #sendFile(file_name, clientSocket)
    elif(requestType == '2'):
        sendFile(head[3],serverSocket, buff, clientAddrPort)
        print "Send file"
    #conn.close()
    serverSocket.close()
    print "Connection closed."
    sys.exit()

startServer();
