"""tftp-server.
Usage:
  tftp-server.py 

"""

import socket

"""
	opcode  operation
	 1     Read request (RRQ)
	 2     Write request (WRQ)
	 3     Data (DATA)
	 4     Acknowledgment (ACK)
	 5     Error (ERROR)

>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

TFTP Formats

   Type   Op #     Format without header

		  2 bytes    string   1 byte     string   1 byte
		  -----------------------------------------------
   RRQ/  | 01/02 |  Filename  |   0  |    Mode    |   0  |
   WRQ    -----------------------------------------------


		  2 bytes    2 bytes       n bytes
		  ---------------------------------
   DATA  | 03    |   Block #  |    Data    |
		  ---------------------------------


		  2 bytes    2 bytes
		  -------------------
   ACK   | 04    |   Block #  |
		  --------------------


		  2 bytes  2 bytes        string    1 byte
		  ----------------------------------------
   ERROR | 05    |  ErrorCode |   ErrMsg   |   0  |
		  ----------------------------------------

Error Codes

   Value     Meaning

   0         Not defined, see error message (if any).
   1         File not found.
   2         Access violation.
   3         Disk full or allocation exceeded.
   4         Illegal TFTP operation.
   5         Unknown transfer ID.
   6         File already exists.
   7         No such user.

====================
Protocol in action
====================

As shown above the protocol can be seen in action on the last 6 lines or so.

1. Client sends a Read Request specifying a file and mode. [ We can see opcodes for that in RFC ]
2. Server responds with block of data along with block number.
3. Client sends an ACK for the received block
4. Server sends next data with incremented block number and ......

** Normal Termination ** - This excerpt is taken directly from `RFC 1350 <https://tools.ietf.org/html/rfc1350/>`_
  The end of a transfer is marked by a DATA packet that contains
  between 0 and 511 bytes of data (i.e., Datagram length < 512).  This
  packet is acknowledged by an ACK packet like all other DATA packets.
  The host acknowledging the final DATA packet may terminate its side
  of the connection on sending the final ACK.

"""

PORT = 69
MAXSIZE = 508
TERMINATING_DATA_LENGTH = 512

TFTP_OPCODES = {
	'unknown': 0,
	'read': 1,  # RRQ
	'write': 2,  # WRQ
	'data': 3,  # DATA
	'ack': 4,  # ACKNOWLEDGMENT
	'error': 5}  # ERROR

# Map server error codes to messages [ Taken from RFC-1350 ]
server_error_msg = {
	0: "Not defined, see error message (if any).",
	1: "File not found.",
	2: "Access violation.",
	3: "Disk full or allocation exceeded.",
	4: "Illegal TFTP operation.",
	5: "Unknown transfer ID.",
	6: "File already exists.",
	7: "No such user."
}

# Create a UDP socket and open the port 69				 # socket.SOCK_DGRAM: type of the connector, DGRAM = UDP , STREAM = TCP
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)	 # socket.AF_INET: the domain of the connector, in this case, an IPv4 connector

def extract(data): # Get the filename and mode of the first data (RRQ or WRQ packets)

	filename = ""

	i = 2
	while (data[i] != 0):					# i is the byte position				
		filename = filename + chr(data[i])

		i = i + 1

	mode = ""

	i = i + 1
	while (data[i] != 0):					# getting the mode of the data: netascii, octet (bynary) or mail
		mode = mode + chr(data[i])

		i = i + 1

	return filename, mode


def send_ack(ack_data, server):
	"""
	This function constructs the ack using the bytearray.

			  2 bytes    2 bytes
			 -------------------
	  ACK   | 04    |   Block #  |
			 --------------------

	"""
	ack = bytearray(ack_data)

	ack[0] = 0
	ack[1] = TFTP_OPCODES['ack']

	sock.sendto(ack, server)


def server_error(data):
	"""
	We are checking if the server is reporting an error
				2 bytes  2 bytes        string    1 byte
			  ----------------------------------------
	   ERROR | 05    |  ErrorCode |   ErrMsg   |   0  |
			  ----------------------------------------
	
	"""
	opcode = data[:2]
	return int.from_bytes(opcode, byteorder='big') == TFTP_OPCODES['error']


def main():
	sock.bind(("", PORT))

	print("listening on {}".format(PORT))

	while True:
		data, addr = sock.recvfrom(MAXSIZE) #get a data from the port
		print("{} from {}".format(data, addr))

		#RRQ---------------------------------------------------------------------------------------------
		if (data[0] == 0 and data[1] == 1): # if first byte is 0 and the second byte is 1, then is RRQ
			
			filename, mode = extract(data)

			if(mode == "octet"): # if the mode is octet
				
				try:
					file = open(filename, 'rb')
					
				except: # No exist the file
					error = bytearray()

					error.append(0)
					error.append(5)
					error.append(0)
					error.append(1)

					error += bytearray("".encode('utf-8'))

					error.append(0)

					sent = sock.sendto(error, addr)

					print("ERROR, File not found")
					continue

				count = 0 # Block number

				print("Sending file", filename)

				while True: # Send the file in blocks

					block = file.read(MAXSIZE) # read the block

					if not block:

						if (count == 0):
						
							data = bytearray() 				# Making the DATA Packet

							data.append(0)
							data.append(3)

							b = bytearray(count.to_bytes(2, 'big')) # representing count as bytes big endian
							data += b

							sent = sock.sendto(data, addr)

							data, addr = sock.recvfrom(MAXSIZE)

							while( data[0] != 0 and data[1] != 4 and data[2] != b[0] and data[3] != b[1] ): # Wait for ACK
								data, server_address = sock.recvfrom(MAXSIZE)	

						print("Transfer complete")

						file.close()
						break

					data = bytearray()

					data.append(0)
					data.append(3)

					b = bytearray(count.to_bytes(2, 'big'))
					data += b

					data += block

					sent = sock.sendto(data, addr) # Send the data

					data, server_address = sock.recvfrom(MAXSIZE)

					while( data[0] != 0 and data[1] != 4 and data[2] != b[0] and data[3] != b[1] ): # Wait for ACK
						data, server_address = sock.recvfrom(MAXSIZE)	

					if (count + 1 >= 60000):
						count = 0
					
					else:
						count += 1

			elif (mode == "netascii"): # if mode is netascii
				pass

			else: #if mode is mail
				
				try:
					file = open(filename, 'r')
					
				except: # No exist the file

					error = bytearray()

					error.append(0)
					error.append(5)
					error.append(0)
					error.append(1)

					error += bytearray("".encode('utf-8'))

					error.append(0)

					sent = sock.sendto(error, addr)

					print("ERROR, File not found")
					continue

				count = 0 # Block number

				while True: # Send the file in blocks

					block = file.read(MAXSIZE) # read the block

					if not block:

						if (count == 0):

							data = bytearray() 				# Making the DATA Packet

							data.append(0)
							data.append(3)

							b = bytearray(count.to_bytes(2, 'big')) # representing count as bytes big endian
							data += b

							sent = sock.sendto(data, addr)

							data, addr = sock.recvfrom(MAXSIZE)

							while( data[0] != 0 and data[1] != 4 and data[2] != b[0] and data[3] != b[1] ): # Wait for ACK
								data, server_address = sock.recvfrom(MAXSIZE)

						print("Transfer complete")

						file.close()
						break

					data = bytearray()

					data.append(0)
					data.append(3)

					b = bytearray(count.to_bytes(2, 'big'))
					data += b

					data += block

					sent = sock.sendto(data, addr) # Send the data

					# Wait for the ACK
					while( data[0] != 0 and data[1] != 4 and data[2] != b[0] and data[3] != b[1] ): # Wait for ACK
						data, server_address = sock.recvfrom(MAXSIZE)

					if (count + 1 >= 60000):
						count = 0

					else:
						count += 1

		# WRQ----------------------------------------------------------------------------------------------------------------------
		elif (data[0] == 0 and data[1] == 2): # if the first byte is 0 and the second byte is 2, then is WRQ
			
			filename, mode = extract(data)

			if (mode == "octet"): # if mode is octet

				file = open(filename, "wb")

				print("Receiving file", filename)

				while True:
					# Wait for the data from the server
					data, server = sock.recvfrom(600)

					if server_error(data):

						error_code = int.from_bytes(data[2:4], byteorder='big')

						print(server_error_msg[error_code])

						file.close()
						break

					send_ack(data[0:4], server)

					content = data[4:] 
					file.write(content)

					if len(data) < TERMINATING_DATA_LENGTH:
			
						print("Transfer complete")

						file.close()
						break

			elif (mode == "netascii"): # if mode is netascii
				pass

			else: # if mode is mail
				file = open(filename, "w")

				while True:
					# Wait for the data from the server
					data, server = sock.recvfrom(600)

					if server_error(data):

						error_code = int.from_bytes(data[2:4], byteorder='big')
						print(server_error_msg[error_code])

						break

					send_ack(data[0:4], server)

					content = data[4:] 
					file.write(content)

					if len(data) < TERMINATING_DATA_LENGTH:
						
						print("Transfer complete")

						file.close()
						break


if __name__ == "__main__":
	main()