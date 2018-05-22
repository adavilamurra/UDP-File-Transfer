# echoServer.py
Last modification date: 3/15/18

## How to run the program:
    "python echoServer.py"
### Additional notes on how to run program:
    This program does not take in any parameters. So the only way to start the server is by running the command above.

## Background:
 This program is the sever portion of a File Transfer Protocol. There is a client program interacts with the server program to
 make the File transfer protocol possible. The client side will send a request to either retrieve a File(GET) or to save a file(PUT/SEND) to the server.
 Both the server and client programs use UDP to communicate with one another and they send packets with the following packet structure:

### Protocol Description:
	 Packet structure:
	 	--------------------------------------------------------------------------------------------------------------
		|Request Type : Message type : Packet # : file name : file size : window size *            Payload           |
		--------------------------------------------------------------------------------------------------------------
		* PUT(SEND) REQUEST
		  - Request type = 1
		  - Message type = 1
		  - Payload == message
		* ACK(DUPLICATE)
		  - Request type = 1
		  - Message type = 3(Error)
		  - Packet # = Expected Packet #
		  - Payload = "Duplicate"
		* ACK(MISSING)
		  - Request type = 1
		  - Message type = 3(Error)
		  - Packet# = Last Packet received
		  - Payload = "WindowNotComplete"
		* ACK[]
		  - Request type = 1
		  - Message type = 1
		* GET REQUEST
		  - Request type = 2
		  - Message type = 1
		  - Payload = message

### Program Description:
	This code implements the server side of a file transfer protocol using sliding windows. The way we created the Server was we implemented both PUT(SEND) and GET.

	For the PUT(SEND), the program did the following:
	    * Take in any message sent from the client throught the server socket.
	    * If the first bit of the packet was set to 1, it means that this was a PUT request; Otherwise, if it was a two, it was a GET request.
	    * Once a GET request was identified, the program would read in the rest of the packet and extract the payload to "PUT" into a txt file.
	    * Once the first packet had been extracted and used, the server goes into a listening state. The server will send an acknowledgement to the client once the number of packets received
	      equals the window size.
	    * If there are packets missing, ACK[MISSING] would be sent to the client.
	    * If there are duplicate packets. ACK[DUPLICATE] is sent to the client.
	    * If everything seems to be in order, an ACK[] is sent to the client.
	    * The server will continur reading the file until the client is done sending the messages.
	For the GET Request, the program did the following:
	    * Take in any message sent from the client through the socket.
	    * If the first byte is a 2, then it is a GET request
	    * The program extracts the filename from the packet received and opens the file for reading.
	    * As the file is being read, the program is building the packet that will be sent to the client
	    * In the Packet we have the header and the payload
	    * In the payload we get the (100 bytes - headerSize) characters from the file and append it to where the payload is.
	    * Once appended, the packet is sent and we repeat the building and sending process until the number of packets sent is equal to the window size
	    * Once the entire window is sent, the program waits for an ack.
	    * If the program does not get ACK it will timeout
	    * If the program gets a ACK[DUPLICATE], the server will resend the appropriate packet, else it will retry 16 times before giving up
	    * If the program get an ACK[MISSING], the server will resend the missing packet and the rest of the window.
	    * If the program gets an ACK[], then the server will compute the average RTT time for each packet. The way I did it was RTT avg = RTT / WindowSize. If the RTT avg was higher in the next               iteration, then cut the window size by half; otherwise, increment the window size.
	    *once the AVG RTT time was computed, the program prepares to send the next window. It will repeat this until there is nothing else to read from the file.

## Authors

* **Hector Cervantes Jr** - [HcJr20](https://github.com/HcJr20)
* **Alejandro Davila** - [adavilamurra](https://github.com/adavilamurra)

