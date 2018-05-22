#! /bin/python
from socket import *
import time  
import sys, re, string

#set address and reserve port
serverAddr = ('localhost', 50000)
try:
    #get file name from argument
    file_name = sys.argv[1]
    #get user choice
    choice = sys.argv[2]
except:
    print "Wrong parameters."
    sys.exit()
#create socket
clientSocket = socket(AF_INET, SOCK_DGRAM)
#set buffer size
buffSize = 100

#build header for packet 
def buildHeader(choice, identifier, packetNum, file_name, fileSize, windowSize):
    header = str(choice) + chr(58) + str(identifier) + chr(58) + str(packetNum) + chr(58) + file_name + chr(58) + str(fileSize) + chr(58) + str(windowSize) + chr(42)
    return header
    
def buildPacket(header, buffSize, f): #builds packet
    availableSpace = buffSize - len(header) 
    space = availableSpace
    payload = header
    while space > 0:
        char = f.read(1)
        if char == "" :
            print " Nothing else to read"
            return (payload, -1)
        payload += char
        space -= 1
    return (payload, 1)

def sendPackets(packets, packetNum, f, file_name, fileSize, windowIndex, clientSocket, serverAddr, windowSize):
    # start tracking time for RTT
    start = time.time()
    while windowIndex < windowSize: #send window size
        header = buildHeader(1, 1, packetNum, file_name, fileSize, windowSize) 
        packet, status = buildPacket(header, buffSize, f)
        packets.append(packet)
        print packet
        if(clientSocket.sendto(packet, serverAddr)): #if packet sent
            print "Packet #" + str(packetNum) + " sent."
            packetNum = packetNum + 1
        elif(clientSocket.sendto(packet, serverAddr)):# retry again if no connection
            print "Packet #" + str(packetNum) + "sent."
            packetNum = packetNum + 1
        else: #No connection. Give up.
            print "No connection giving up"
            sys.exit()
        if status == -1:
            print "Nothing else to read done"
            sys.exit()
        windowIndex = windowIndex + 1
    return (packets, start, packetNum)

# checks if all packets recieved by recipient    
def checkAck(f, clientSocket, serverAddr, window, endtime,  ackRecieved, tries):
    Status = True
    # if tries == 16 then quit 
    if(tries == 0):
        return False
    # if not all of the packets in a window recieved resend missing packet plus any packet that comes afterward up until window size
    if(ackRecieved[2] == "WindowNotComplete"):
        head = splitHead(ackRecieved[0])
        fileName =  head[3]
        missingPacket = int(head[2])
        fileSize = int(head[4])
        windowSize = len(window)
        j = missingPacket - 1
        windowSize = int(head[5])
        #start time for resend
        start = time.time()
        while j < windowSize:
            if(clientSocket.sendto(window[j], serverAddr)):
                print "resending packet number: " + j
            else:
                sys.exit()
            j = j + 1
        windowSpaceAvail = windowSize - missingPacket
        # reformat window to contain resent packets plus new packets
        # Example: if window size == 5 and packet 3 not recieved, original window [1, 2, 3, 4, 5], new window = [3, 4, 5, , ,] 
        del window[:missingPacket]
        #fill in missing spaces in new window
        #packets, packetNum, f, file_name, fileSize, windowIndex, clientSocket, serverAddr, windowSize
        newWindow, s, packetNum = sendPackets(window, j, f, fileName, fileSize, missingPacket, clientSocket, serverAddr, windowSize)
        #retrieve ack for new window
        ack, serverAddr = clientSocket.recvfrom(buffSize)
        # end time of resend
        endtime = time.time() - start
        ackRecieved = splitPacket(ack)
        #recursively check if all packets in window recieved, pass in the newWindow, endtime, ack, and client address port
        status = checkAck(f, clientSocket, serverAddr, window, endtime, ackRecieved, tries - 1)
    #return true if all packets in window got acknowledged 
    return Status, endtime;

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
def sendFile(file_name, clientSocket, buffSize, serverAddr):
    print "Sending file..."
    packetNum = 1 # keep track of packet count 
    ack = False # boolean to keep track if acknowledgment arrived
    fileSize = getFileSize(file_name) #getFileSize in byte
    windowSize = 1;
    timeout = 4;
    RTT = 0
    try:
        with open(file_name, 'r') as f:
            while True:
                # initialize new window
                window = []
                # start sending packets to recipient( window, window index, server socket, client address port, window size)
                print "In sendPackets"
                window, start, packetNum = sendPackets(window, packetNum, f, file_name, fileSize, 0, clientSocket, serverAddr, windowSize)
                print "waiting for buffer"
                ack, serverAddr = clientSocket.recvfrom(buffSize)
                print ack
                startTimeout = time.time()
                #implement timeout
                print "waiting for ACK"
                while not ack:
                    timeElapsed = time.time()
                    if(timeElapsed > 4000):
                        print "Timeout: Giving up on ya babe"
                    if(timeElapsed == 2000):
                        i = 0
                        while(i < windowSize):
                            clientSocket.sendto(window[i], serverAddr)
                endtime = time.time() - start
                print "In splitPacket"
                ackRecieved = splitPacket(ack)
                print  "In checkACK"
                success, endtime = checkAck(f, clientSocket, serverAddr, window, endtime, ackRecieved, 16)
                if not success:
                    print "tried sending missing packtes for 16 times. Giving up"
                    sys.exit(1)
                if(windowSize == 1):
                    RTT = endtime;
                RTTguess = int(round(endtime/windowSize))
                if(RTTguess <= RTT):
                    windowSize = windowSize + 1
                else:
                    windowSize = windowSize / 2
    except IOError as e:
        print "No such file or directory. Try again."
        sys.exit()
        
    print "Roundtrip Time: " + str(roundTripTime)  
    throughput = buffSize / roundTripTime
    print "Throughput: " + str(throughput) 
    print "Succesfully sent the file."
    print "Connection closed."

def splitPacket(data):
    array = data.partition("*")
    return array

def splitHead(data):
    array = data.split(":")
    return array

# retrives file from server
def getFile(clientSocket, packet, head, buffSize, serverAddrPort):
    fileName = str(head[3])
    clientFile = open(fileName.strip(),'w+')
    currentPacket = 1
    windowCounter = 1
    while True:
        if not packet:
            break
        messageReceived = splitPacket(packet)
        head = messageReceived[0].split(":")
        message = messageReceived[2]
        print  head
        packetNumber = head[2]
        windowSize = head[5]
        print messageReceived
        previousPacket = str(currentPacket -1)
        if packetNumber == previousPacket:
            head = buildHeader(1, 3, int(packetNumber), head[3], 0, windowSize)
            duplicateMessage = head + "Duplicate"
            clientSocket.sendto(duplicateMessage, clientAddrPort)
        #This is the part that handles missed packet for any given window size9
        if packetNumber != str(currentPacket):
            #send error message and put expected packet in packet field
            head = buildHeader(1, 3, currentPacket + 1, head[3], 0, windowSize)
            errormessage = head + "WindowNotComplete"
            clientSocket.sendto(errormessage, clientAddrPort)
        else:
            #write data to a file
            if str(currentPacket) == head[2]:
                print "inside current packet comparison"
                clientFile.write(messageReceived[2])
                currentPacket = currentPacket + 1 
                if str(windowCounter) == windowSize:
                    print "inside windowSize comparison" 
                    print "Last Packet of Window Recieved: " + str(currentPacket)
                    head = buildHeader(1, 2, int(packetNumber),head[3], 0, windowSize)
                    ack = head + "GotMessage"
                    clientSocket.sendto(ack, serverAddr)
                    print "Ackowledgement sent for packet: " + packetNumber
                    windowCounter = 1;
            windowCounter = windowCounter + 1
        packet, clientAddrPort = clientSocket.recvfrom(buffSize)
        
        
    serverFile.close()
    print "Succesfully downloaded the file"
    
      
#connect to server
try:
    clientSocket.connect(serverAddr)
    print "Connected to server."
except:
    print "Error. Server not found."
    sys.exit()

#determine if get or put
if choice == '1':
    sendFile(file_name, clientSocket, buffSize, serverAddr)
elif choice == '2':
   choiceHeader = buildHeader(choice, 1, 1, file_name, 0, 1)
   clientSocket.sendto(choiceHeader, serverAddr)
   packet, serverAddr = clientSocket.recvfrom(buffSize)
   print packet
   message = splitPacket(packet)
   head = splitHead(message[0])
   getFile(clientSocket, packet, head, buffSize, serverAddr)
clientSocket.close()
