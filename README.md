# TFTP-Server-Client

Group Lambder conformed by: Daniel Berbesi, Cesar Salazar, Valentina Contreras and Saul Ugueto

Guiding us of RFC 1350 we create the formats of the Protcol TFTP packages using byte array, which made it very intuitive to program

Compile with: Python3

Client Features:
Send Requests and control packages (WRQ,RRQ,ACK,ERROR) and files to the server, and receive files in octet (binary) and netascii modes from the server and control packeges. The mail mode is obsolete and not used. 
To see the process you can print the acks when they are delivered.

Server Features:
Listening the client's requests , send and receive files and control packages.

