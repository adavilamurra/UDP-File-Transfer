# UDP File Transfer Protocol - Client

This is the client side of our file transfer protocol

## Getting Started

In order to run this project successfully you will have to run the server file (udpServer.py) located in the folder /server/ and then the client file (udpClient.py) located in this folder /client/.

### Prerequisites

To run this protocol you will need:
* Python 2.7
* Command Line Terminal

## Running the client

The client can decide whether it wants to send or receive a file.
It receives two arguments that are:
```
file_name get/put
```
The first argument will be the name of the file that the client wants to send or receive.
The second argument is a number (1 or 2), that will represent the get or put. 1 = put, and 2 = get.
The command that will be used to call the client will look like the following example:

```
python udpClient.py file.txt 2
```

## Packet

Packets are made of:
```
1) header                   % used to identify the packet and provide more information
2) payload                  % part of the message being sent
```

## Header

We created headers made up of:
```
1) get/put                  % to identify the number(1,2) and know if it is a get or put
2) file identifier          % to know that the packets received are a part of the same file
3) packet number            % to know if the packets are received in a different order, or to identify packets lost.
4) file name                % to create a new file with the name of the file that is being sent.
5) file size                % sum of all packets should be equivalent to the file size.
```

## Put

When the client sends a file:
```
1) open file that will be sent
2) build header 
3) build packet using header and data from file
4) send packet
5) wait for acknowledgement of packet sent
6) when acknowledgement of that packet is received, send next packet (repeat this until you send every packet)
7) if no acknowledgment is received, wait until timeout and send again
8) if you try sending the packet 16 times without receiving an acknowledgment, give up.
9) if every acknowledgment is received, close connection.
```

## Get

When the client wants to receive a file:
```
1) wait for packet sent from server
2) if a packet is received, send acknowledgement of that packet to the server (repeat steps until an acknowledgement for every packet is sent)
3) if all packets are received by client, close connection.
```

## Analysis

We defined round trip time as the double of the time it took a message sent from the client to arrive to the server.
We defined throughput as the size of the packet divided by the round trip time.
```
Round Trip Time: .0200004577637 s
Throughput: 4166.72031154
```

## Authors

* **Hector Cervantes Jr** - [HcJr20](https://github.com/HcJr20)
* **Alejandro Davila** - [adavilamurra](https://github.com/adavilamurra)

