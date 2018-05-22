 
from socket import *
import time
import sys, re , string

def buildPacket(header, bufferSize, f):
    availableSpace = bufferSize - len(header) 
    space = availableSpace
    payload = header
    while space > 0:
        char = f.read(1)
        if char == "":
            return (payload, -1)
        payload += char
        space -= 1
    return (payload, 1)

#split packet contents 
def splitPacket(data):
    array = data.partition("*")
    return array


def splitHead(data):
    array = data.split(":")
    return array


def buildHeader(choice, identifier, packetNum, file_name, fileSize, windowSize):
    header = str(choice) + chr(58) + str(identifier) + chr(58) + str(packetNum) + chr(58) + file_name + chr(58) + str(fileSize) + chr(58) + str(windowSize) + chr(42)
    return header


def getFileSize(file_name):
    try:
        with open(file_name, 'r') as f:
            data=f.read().replace('\n','')
            f.close()
            return len(data)
    except IOError as e:
        print "No such file or directory. Try again."
        sys.exit()

def getFile(serverSocket, packet, head, buffSize, clientAddrPort):
    fileName = str(head[3])
    serverFile = open(fileName.strip(),'w+')
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
            serverSocket.sendto(duplicateMessage, clientAddrPort)
        #This is the part that handles missed packet for any given window size9
        if packetNumber != str(currentPacket):
            #send error message and put expected packet in packet field
            head = buildHeader(1, 3, currentPacket + 1, head[3], 0, windowSize)
            errormessage = head + "WindowNotComplete"
            serverSocket.sendto(errormessage, clientAddrPort)
        else:
            #write data to a file
            if str(currentPacket) == head[2]:
                print "inside current packet comparison"
                serverFile.write(messageReceived[2])
                currentPacket = currentPacket + 1 
                if str(windowCounter) == windowSize:
                    print "inside windowSize comparison" 
                    print "Last Packet of Window Recieved: " + str(currentPacket)
                    head = buildHeader(1, 2, int(packetNumber),head[3], 0, windowSize)
                    ack = head + "GotMessage"
                    serverSocket.sendto(ack, clientAddrPort)
                    print "Ackowledgement sent for packet: " + packetNumber
                    windowCounter = 1;
        windowCounter = windowCounter + 1
        packet, clientAddrPort = serverSocket.recvfrom(buffSize)
        
        
    serverFile.close()
    print "Succesfully downloaded the file."

def sendPackets(packets, packetNum, f, file_name, fileSize, windowIndex, serverSocket, clientAddrPort, windowSize):
    # start tracking time for RTT
    start = time.time()
    while windowIndex < windowSize: #send window size
        header = buildHeader(1, 1, packetNum, file_name, fileSize, windowSize)
        packet, status = buildPacket(header, 100, f)
        packets.append(packet)
        if(serverSocket.sendto(packet, clientAddrPort)): #if packet sent
            print "Packet #" + str(packetNum) + " sent."
            print packet
            packetNum = packetNum + 1
        elif(serverSocket.sendto(packet, clientAddrPort)):# retry again if no connection
            print "Packet #" + str(packetNum) + "sent."
            packetNum = packetNum + 1
        else: #No connection. Give up.
            sys.exit()
        if status == -1:
            sys.exit()
        windowIndex = windowIndex + 1
    return (packets, start, packetNum)


# checks if all packets recieved by recipient    
def checkAck(f, serverSocket, clientAddrPort, window, endtime, ackRecieved, tries):
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
            if(serverSocket.sendto(window[j], clientAddrPort)):
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
        newWindow, s, packetNum = sendPackets(window, j, f, fileName, fileSize, missingPacket, serverSocket, clientAddrPort, windowSize)
        #retrieve ack for new window
        ack, serverAddr = serverSocket.recvfrom(buffSize)
        # end time of resend
        endtime = time.time() - start
        ackRecieved = splitPacket(ack)
        #recursively check if all packets in window recieved, pass in the newWindow, endtime, ack, and client address port
        status = checkAck(f, serverSocket, clientAddrPort, window, endtime, ackRecieved, tries - 1)
    #return true if all packets in window got acknowledged 
    return Status, endtime;

def sendFile(file_name, serverSocket, buffSize, clientAddrPort):
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
                window, start, packetNum = sendPackets(window, packetNum, f, file_name, fileSize, 0, serverSocket, clientAddrPort, windowSize)
                ack, clientAddrPort = serverSocket.recvfrom(buffSize)
                startTimeout = time.time()
                #implement timeout
                while not ack:
                    timeElapsed = time.time()
                    if(timeElapsed > 4000):
                        print "Timeout: Giving up on ya babe"
                    if(timeElapsed == 2000):
                        i = 0
                        while(i < windowSize):
                            serverSocket.sendto(window[i], clientAddrPort)
        
                endtime = time.time() - start
                ackRecieved = splitPacket(ack)
                success, endtime = checkAck(f, serverSocket, clientAddrPort, window, endtime, ackRecieved, 16)
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


def listen():
    #set host and address
    serverAddr = ("", 50000)
    #create socket, bind port, and listen
    serverSocket = socket(AF_INET, SOCK_DGRAM)
    serverSocket.bind(serverAddr)
    print "Binding datagram socket to %s" % repr(serverAddr)
    print "Server listening..."
    return serverSocket
        
def startServer():
    serverSocket = listen()
    buffSize = 100
    packet, clientAddrPort = serverSocket.recvfrom(buffSize)
    messageReceived = splitPacket(packet)
    head = messageReceived[0].split(":")
    fileName = head[3]
    requestType = head[0]
    if requestType == '1':
        getFile(serverSocket, packet, head, buffSize, clientAddrPort)
    elif requestType == '2':
        sendFile(fileName, serverSocket, buffSize, clientAddrPort)
    serverSocket.close()
    sys.exit()

startServer()
        
        
