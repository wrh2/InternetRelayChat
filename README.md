## IRC Client-Server

Internet Relay Chat Client & Server programmed by William Harrington in Python for CS494 project. For proper execution, this code requires python 2.7.9 or earlier. 
It may be compatible with newer versions of python but it hasn't been tested with them yet.
If you run it with newer versions of python and it works/doesn't work please email me.


Coding style adheres to PEP 0008 guidelines. I have used flake8 to ensure this.


The client and server adhere to the protocol outlined in the RFC included with the code.
The protocol outlined in the RFC is like wannabe IRC protocol so don't try to actually use the client to connect to real IRC servers or use real IRC clients to connect to the server.
You can however modify this code to comply with IRC protocol pretty easily as all the beginnings are here for you.


The last thing worth mentioning is that this code is not multithreaded. If you are interested in making this code better, I would suggest exploring that and I'd love to see the code if you do.

## Client
The client is designed to run with the server discussed in the following section.

**To run the client:**
python chat_client.py host port username

host: IP address of server

port: port number that the server is listening on

username: desired username

Please note that the host and port must be the corresponding IP address and port of the server you are trying to connect to.
Also, if the username that you specify is in use, you will get an error message and be disconnected.

## Server
The server is designed to run with the client discussed in the previous section.

**To run the server:**
python chat_server.py


## RFC (Request For Comments)

To edit the RFC use your favorite text editor. See man 7 groff for formatting options. There is an empty nroff template within the repository (empty.nroff).

To make a nice pdf with the nroff do the following:

**For Mac OSX users do the following to make a nice pdf with the nroff:**


groff rfc.nroff | pstopdf -i -o rfc.pdf


open rfc.pdf

**For Linux users do the following to make a nice pdf with the nroff**

pdfroff rfc.nroff > rfc.pdf

evince rfc.pdf