import socket

MAXSIZE = 508
PORT = 69

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


def main():
	# Connect and open the port 69
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("", PORT))
    print("listening on {}".format(PORT))

    while True:
    	data, addr = s.recvfrom(MAXSIZE) #get a data from the port
    	print("{} from {}".format(data, addr))
    	if (data[0] == 0 and data[1] == 1): # if the second bit is 1, then is RRQ
    		filename, mode = extract(data)
    		if(mode == "octet"): # if the mode is octet
    			try:
    				file = open(filename, 'rb')
    			except: # No exist the file
    				print("ERROR")
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

    				block = file.read(MAXSIZE) # read the first block
    				if not block:
    					break

    				data = bytearray()
    				data.append(0)
    				data.append(3)

    				b = bytearray(count.to_bytes(2, 'big'))

    				data += b

    				data += block

    				print("Block sended")

    				sent = s.sendto(data, addr) # Send the data

    				while True: # wait for the ACK
    					data, addr = s.recvfrom(MAXSIZE)
    					if(data[0] == 0 and data[1] == 4 and data[2] == b[0] and data[3] == b[1]):
    						print("ACK of block #", count, '\n')
    						break


    				count += 1



    	elif (data[1] == 2): # if the second bit is 2, then is WRQ
    		haceralgo() 


if __name__ == "__main__":
	main()