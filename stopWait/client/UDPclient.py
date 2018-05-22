#! /bin/python
from socket import *
import time  
import sys, re, string

#set address and reserve port
serverAddr = ('localhost', 50000)
#get file name from argument
file_name = sys.argv[1]
#get user choice
choice = sys.argv[2]
#create socket
clientSocket = socket(AF_INET, SOCK_DGRAM)
#set buffer size
buff = 100

#build header for packet 
def buildHeader(choice, identifier, packetNum, file_name, fileSize):
    header = str(choice) + chr(58) + str(identifier) + chr(58) + str(packetNum) + chr(58) + file_name + chr(58) + str(fileSize) + chr(42)
    return header
    
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

# send files to server, takes in file name and socket object        
def sendFile(file_name, clientSocket, serverAddr):
    print "Sending file..."
    packetNum = 1 # keep track of packet count 
    ack = False # boolean to keep track if acknowledgment arrived
    fileSize = getFileSize(file_name) #getFileSize in byte
    identifier = 1
    timeout = 4;
    roundTripTime = 0
    try:
        with open(file_name, 'r') as f:
            while True:
                header = buildHeader(choice, identifier, packetNum, file_name, fileSize)
                packet, status = buildPacket(header, buff, f)
                start = time.time()
                roundT = 0
                if(clientSocket.sendto(packet, serverAddr)):
                    print "Packet #" + str(packetNum) + " sent. Waiting for acknowledgement."
                    ack, serverAddrPort = clientSocket.recvfrom(buff)
                    tries = 1
                    while not ack:
                        end = time.time()
                        elapsedT = end - start
                        if tries == 16:
                            print "Acknowledgement not received. Giving up!"
                            sys.exit()
                        if elapsedT >= timeout: 
                            clientSocket.sendto(packet, serverAddr)
                            start = time.time()
                        tries += 1
                    if roundTripTime == 0:
                        roundTripTime = 2 * (time.time() - start)
                    packetNum += 1
                    print ack
                else:
                    clientSocket.sendto(packet, serverAddr)
                if status == -1:
                    break
    except IOError as e:
        print "No such file or directory. Try again."
        sys.exit()
    print "Roundtrip Time: " + str(roundTripTime)  
    throughput = buff / roundTripTime
    print "Throughput: " + str(throughput) 
    print "Succesfully sent the file."
    print "Connection closed."

def splitPacket(data):
    array = data.partition("*")
    return array

# retrives file from server
def getFile(conn, fileName, serverAddr):
    buff = 100
    print "fileName" 
    serverFile = open(fileName.strip(),'w+')
    print "open"
    previousPacket = -1
    while True:
        data, serverAddrPort = conn.recvfrom(buff)
        if not data:
            break
        messageReceived = splitPacket(data)
        h = messageReceived[0].split(":")
        if h[2] == previousPacket:
            conn.sendto("Packet Number: " + previousPacket + " already received!", serverAddrPort)
            continue
        serverFile.write(messageReceived[2])      #write data to a file
        print "Server received: " + messageReceived[2]
        conn.sendto("Received packet: " + messageReceived[0], serverAddr)
        previousPacket += 1
    serverFile.close()

#connect to server
try:
    clientSocket.connect(serverAddr)
    print "Connected to server."
except:
    print "Error. Server not found."
    sys.exit()

#determine if get or put
if(choice == str(1)):
    sendFile(file_name, clientSocket, serverAddr)
elif(choice == str(2)):
    choiceHeader = buildHeader(choice, 1, 1, file_name, 0) 
    clientSocket.sendto(choiceHeader, serverAddr)
    getFile(clientSocket, file_name, serverAddr)
clientSocket.close()
