import socket


MAXSIZE = 508
PORT = 69

TERMINATING_DATA_LENGTH = 512

TFTP_OPCODES = {
	'unknown': 0,
	'read': 1,  # RRQ
	'write': 2,  # WRQ
	'data': 3,  # DATA
	'ack': 4,  # ACKNOWLEDGMENT
	'error': 5}  # ERROR


def extract(data): # Get the filename and mode of the first data (RRQ or WRQ)
	filename = ""
	i = 2
	while (data[i] != 0):
		filename = filename + chr(data[i])
		i = i + 1

	mode = ""
	i = i + 1
	while (data[i] != 0):
		mode = mode + chr(data[i])
		i = i + 1

	return filename, mode


def send_ack(ack_data, server, s):
	"""
	This function constructs the ack using the bytearray.
	We dont change the block number cause when server sends data it already has
	block number in it.

			  2 bytes    2 bytes
			 -------------------
	  ACK   | 04    |   Block #  |
			 --------------------
	:param ack_data:
	:param server:
	:return:
	"""
	ack = bytearray(ack_data)
	ack[0] = 0
	ack[1] = TFTP_OPCODES['ack']
	s.sendto(ack, server)


def server_error(data):
	"""
	We are checking if the server is reporting an error
				2 bytes  2 bytes        string    1 byte
			  ----------------------------------------
	   ERROR | 05    |  ErrorCode |   ErrMsg   |   0  |
			  ----------------------------------------
	:param data:
	:return:
	"""
	opcode = data[:2]
	return int.from_bytes(opcode, byteorder='big') == TFTP_OPCODES['error']


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


def main():
	# Connect and open the port 69
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.bind(("", PORT))
	print("listening on {}".format(PORT))

	while True:
		data, addr = s.recvfrom(MAXSIZE) #get a data from the port
		print("{} from {}".format(data, addr))

		if (data[0] == 0 and data[1] == 1): # if first byte is 0 and the second byte is 1, then is RRQ
			
			filename, mode = extract(data)

			if(mode == "octet"): # if the mode is octet
				
				try:
					file = open(filename, 'rb')
					
				except: # No exist the file
					print("ERROR, File not found")
					error = bytearray()
					error.append(0)
					error.append(5)
					error.append(0)
					error.append(1)
					error += bytearray("".encode('utf-8'))
					error.append(0)
					sent = s.sendto(error, addr)
					exit()

				count = 0 # Block number

				while True: # Send the file in blocks

					block = file.read(MAXSIZE) # read the block
					if not block:
						if (count == 0):
						
							data = bytearray()
							data.append(0)
							data.append(3)

							b = bytearray(count.to_bytes(2, 'big'))

							data += b

							print("Send Block #", count)

							sent = s.sendto(data, addr)

							data, addr = s.recvfrom(MAXSIZE)
							if(data[0] == 0 and data[1] == 4 and data[2] == b[0] and data[3] == b[1]):
								print("ACK of block #", count, '\n')

						print("Transfer complete")
						file.close()
						break

					data = bytearray()
					data.append(0)
					data.append(3)

					b = bytearray(count.to_bytes(2, 'big'))

					data += b

					data += block

					print("Send Block #", count)

					sent = s.sendto(data, addr) # Send the data

					while True: # wait for the ACK
						data, addr = s.recvfrom(MAXSIZE)
						if(data[0] == 0 and data[1] == 4 and data[2] == b[0] and data[3] == b[1]):
							print("ACK of block #", count, '\n')
							break


					count += 1

			elif (mode == "netascii"): # if mode is netascii
				pass

			else: #if mode is mail
				pass



		elif (data[0] == 0 and data[1] == 2): # if the first byte is 0 and the second byte is 2, then is WRQ
			
			filename, mode = extract(data)

			if (mode == "octet"): # if mode is octet

				file = open(filename, "wb")

				while True:
					# Wait for the data from the server
					data, server = s.recvfrom(600)

					if server_error(data):
						error_code = int.from_bytes(data[2:4], byteorder='big')
						print(server_error_msg[error_code])
						break

					send_ack(data[0:4], server, s)
					print("Send ack")
					content = data[4:] 

					file.write(content)

					if len(data) < TERMINATING_DATA_LENGTH:
						file.close()
						print("Transfer complete")
						break

			elif (mode == "netascii"): # if mode is netascii
				pass

			else: # if mode is mail
				pass


if __name__ == "__main__":
	main()