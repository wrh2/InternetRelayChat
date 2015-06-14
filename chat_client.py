"""
 An IRC Client programmed in python
 Note: code has been tested with python version 2.7.9
 Programmed by William Harrington for CS494 Programming Project
"""

import socket   # for socket objects
import select   # for select function
import signal   # for signal interrupt
import sys      # for handling command line arguments


def signal_handler(signal, frame):
    """Function handles signal interrupt (CTRL-C)

    :param signal: signal caught
    :param frame: current stack frame
    """
    s.send('/exit')
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


if __name__ == "__main__":
    """Main function

    """

    # user supplied the wrong amount of arguments
    if(len(sys.argv) < 4):
        # show proper usage and exit program
        print 'Usage : python chat_client.py hostname port username'
        sys.exit()

    # get the IRC server address
    host = sys.argv[1]

    # get the IRC server port
    port = int(sys.argv[2])

    # get the user's name
    username = sys.argv[3]

    # protect against user names
    # longer than 9 chars
    if len(username) > 9:
        print 'Username is too long. Max is 9 characters'
        sys.exit()

    # create TCP Socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # set timeout to 2 seconds
    s.settimeout(2)

    # connect to remote host
    try:
        s.connect((host, port))
    except:
        print 'Unable to connect'
        sys.exit()
    print 'Connected to IRC server'

    # send user's name to server
    try:
        s.send(username)
    except:
        # bad username, exit program
        print 'Unable to authenticate username'
        sys.exit()

    while 1:
        socket_list = [sys.stdin, s]

        # Get the list sockets which are readable
        read_sockets, write_sockets, error_sockets = select.select(
            socket_list, [], [])

        for sock in read_sockets:

            # incoming message from remote server
            if sock == s:

                # receive up to 512 bytes of data
                data = sock.recv(512)

                # if there is no data
                # connection timed out
                # close it
                if not data:
                    print '\nDisconnected from chat server'
                    sock.close()
                    sys.exit()

                # we have data from the server
                else:

                    # check for carriage-return line-feed pair
                    # as it represents the end of the message
                    # from the server
                    if data.find('\r\n') > -1:

                        # CR-LF pair is there so show message
                        print data

            # user entered message
            else:

                # read 510 bytes
                msg = sys.stdin.readline(510)

                # add carriage-return line-feed pair
                # to terminate message
                msg += '\r\n'

                # send it
                s.send(msg)
