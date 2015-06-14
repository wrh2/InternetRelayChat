"""
 An IRC server programmed in python for a CS494 project
 Note: code has been tested with python version 2.7.9

 Copyright (C) 2015  William Harringt, Portland State University

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along
    with this program; if not, write to the Free Software Foundation, Inc.,
    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""
import socket   # for socket objects
import select   # for select function
import logging  # for logging
import signal   # for signal interrupts
import sys      # for sys calls
import random   # for random stuff


def broadcast_data(sock, message):
    """Function to broadcast chat messages to all connected clients

    This function sends a message to clients connected to the server
    Messages are sent according to the current channel that the sender is in
    This means that only clients whose current channel is the same as
    The sender will receive the message

    :param sock: socket object
    :param message: message to send
    """

    # stores sockets that have a non-empty current field
    valid_users = []

    # go through sockets in connection list
    for s in CONNECTION_LIST:

        # do not store master socket or client who is sending message
        if s != server_socket and s != sock:

            # find sockets with non empty current channel
            if accounts[s]['current'] != '':

                # store them in array
                valid_users.append(s)

    # go through sockets in valid users
    for s in valid_users:

        # Only send to sockets who are looking at the same current channel
        if accounts[s]['current'] == accounts[sock]['current']:
            # try to send the message
            # if we can't send socket timed out so log client off
            try:
                s.send(message)
            except:
                logoff(socket)


def parse_data(sock, message):
    """Function to parse the data received and perform the appropriate action

    This function really only takes care of
    /PRIVMSG commands and /msg commands
    Everything else is passed on to parse_data2

    :param sock: socket object
    :param message: message to parse
    """

    # received PRIVMSG command
    if message.find('/PRIVMSG') == 0:

        # user not in any channels
        if len(accounts[sock]['channels']) == 0:

            # notify bad user!
            sock.send('\nMust join channel to send a message\r\n')

        # user in channel(s)
        else:

            # we have a message to send
            if message[9]:

                # name of user sending message
                user = accounts[sock]['username']

                # message to send
                msg = message[9:]

                # send message to current channel
                broadcast_data(sock, '\n<%s> %s\r\n' % (user, msg))

            # we didn't actually get a message
            # ..this probably couldn't happen
            # but better safe than sorry!
            else:

                # notify bad user!
                sock.send('\nEmpty message, nothing has been sent\r\n')

    # received a msg command
    elif message.find('/msg') == 0:

        # split message string up to do error checking
        check_msg = message.split()

        # check to make sure we have a sufficient
        # amount of arguments before we try
        if len(check_msg) >= 3:
            privatemsg(sock, message)
        else:
            sock.send('\nInvalid command\r\n')

    else:
        # so for simplicity's sake we don't parse the
        # /PRIVMSG command based on white space
        # but everything else we do
        message = message.split()
        parse_data2(sock, message)


def privatemsg(sock, msg):
    """Function handles msg command
    which allows user to send private messages

    :param sock: socket object
    :param msg: message to send
    """

    sender = accounts[sock]['username']

    # split the msg string into array of strings
    # then grab the piece at index 1
    user = msg.split()[1]

    # user tried to send a private message
    # to themselves
    if user == sender:

        # notify bad user
        sock.send('\nCan not private message yourself!\r\n')

        # get outta here
        return

    # take everything after the user name
    # turn it into msg2send string
    msg2send = msg[5+len(user):]

    # check to see if that username is
    # in the user list
    if user in USER_LIST:

        # go through the accounts
        for key in accounts:

            # find the specified user
            if accounts[key]['username'] == user:

                # try sending the private message
                try:
                    key.send('\n<private message from %s>%s\r\n'
                             % (sender, msg2send))
                    break  # to stop needless iterations

                # otherwise log that socket off
                except:
                    logoff(key)

    # username wasn't in user list
    else:
        sock.send('\nNo such user\r\n')


def parse_data2(sock, message):
    """Function receives data parsed based on
    whitespace and takes the appropriate action

    The majority of messages pass through this function
    (the only exception being /PRIVMSG commands)
    Therefore it is very important to server operation

    :param sock: socket object
    :param message: message to dictate action
    """

    # take action based on the length of the message
    if len(message) == 1:

        # received help command
        if message[0] == '/help':
            # general help command, lists all commands
            help(sock, command=None)

        # received who command
        elif message[0] == '/who':
            who(sock, channel=None)

        # received list command
        elif message[0] == '/list':
            list(sock)

        # received exit command
        elif message[0] == '/exit':
            logoff(sock)

        # received nick command
        elif message[0] == '/nick':
            changenick(sock, nick=None)

        # everything else is invalid
        else:
            sock.send('\nInvalid command\r\n')

    elif len(message) == 2:

        # received help command
        if message[0] == '/help':
            command = message[1]
            help(sock, command)

        # receive a whois command
        elif message[0] == '/whois':
            username = message[1]
            whois(sock, username)

        # received a peek command
        elif message[0] == '/who':
            channel = message[1]
            who(sock, channel)

        # received a join command
        elif message[0] == '/join':
            channel = message[1]
            joinchannel(sock, channel)

        # received a leave command
        elif message[0] == '/leave':
            channel = message[1]
            leavechannel(sock, channel)

        # received a current command
        elif message[0] == '/current':
            channel = message[1]
            switchcurrent(sock, channel)

        # received a nick command
        elif message[0] == '/nick':
            nick = message[1]
            changenick(sock, nick)

        # everything else is invalid
        else:
            sock.send('\nInvalid command\r\n')

    # everything else is invalid
    else:
        sock.send('\nInvalid command\r\n')


def help(sock, command):
    """Function processes help command which shows user list of commands
    If command is supplied, specific info about command is sent to client

    :param sock: socket object
    :param command: option argument shows specific info for command
    """

    if command is None:
        sock.send('\nList of commands\n')
        sock.send('/help -- shows valid commands\n')
        sock.send('/nick <nickname> -- show/change username\n')
        sock.send('/who <channel> -- shows users\n')
        sock.send('/list -- shows channels on server\n')
        sock.send('/exit -- logoff\n')
        sock.send('/whois <username> -- info about user\n')
        sock.send('/join <channel> -- join channel\n')
        sock.send('/leave <channel> -- leave channel\n')
        sock.send('/current <channel> -- change current channel\n')
        sock.send('/msg <user> <message> -- send user private message\n')
        sock.send('/help <command> -- more info on command\r\n')

    else:
        if command == 'nick':
            sock.send('\nCommand: /nick\n')
            sock.send('Arguments: <nickname> (optional)\n')
            sock.send('Description: The nick command will'
                      ' change your username to <nickname>\n')
            sock.send('If <nickname> is not provided,'
                      ' current username is echoed\r\n')

        elif command == 'who':
            sock.send('\nCommand: /who\n')
            sock.send('Arguments: <channel> (optional)\n')
            sock.send('Description: The who command will show'
                      'you all the users on the server\n')
            sock.send('when channel is not provided.'
                      'When channel provided it will show you\n')
            sock.send('the users in that channel\r\n')

        elif command == 'list':
            sock.send('\nCommand: /list\n')
            sock.send('Arguments: none\n')
            sock.send('Description: The list command will show'
                      'you a list of the current channels on the server\r\n')

        elif command == 'exit':
            sock.send('\nCommand: /exit\n')
            sock.send('Arguments: none\n')
            sock.send('Description: The exit command will log'
                      'you off the server\r\n')

        elif command == 'whois':
            sock.send('\nCommand: /whois\n')
            sock.send('Arguments: <username> (required)\n')
            sock.send('Description: The whois command will display basic'
                      'info about the user specified with <username>\n')
            sock.send('Ex: /whois billy\r\n')

        elif command == 'join':
            sock.send('\nCommand: /join\n')
            sock.send('Arguments: <channel> (required)\n')
            sock.send('Description: The join command will place'
                      'you in the channel specified with <channel>\n')
            sock.send('If the channel does not exist yet,'
                      'it will be created\n')
            sock.send('By default the most recent channel you have'
                      'joined becomes your current channel\n')
            sock.send('Channel names must start with # and '
                      'contain no spaces or other illegal characters\n')
            sock.send('Ex: /join #channel_one\r\n')

        elif command == 'leave':
            sock.send('\nCommand: /leave\n')
            sock.send('Arguments: <channel> (required)\n')
            sock.send('Description: The leave command will take you out '
                      'of the channel specified by <channel>\n')
            sock.send('You must be in a channel in order to leave it.\n')
            sock.send('If you are the last person in the channel, '
                      'once you leave it will be deleted\n')
            sock.send('Ex: /leave #channel_one\r\n')

        elif command == 'current':
            sock.send('\nCommand: /current\n')
            sock.send('Arguments: <channel> (required)\n')
            sock.send('Description: The current command will switch your '
                      'current channel\n')
            sock.send('You must be in the channel specified by <channel>\n')
            sock.send('Ex: /current #channel_one\r\n')

        elif command == 'msg':
            sock.send('\nCommand: /msg\n')
            sock.send('Arguments: <user>, <message> (required)\n')
            sock.send('Description: Send private message '
                      '<message> to <user>\n')
            sock.send('Ex: /msg billy hi billybob!\r\n')

        else:
            sock.send('\nSpecified command does not exist.')
            sock.send(' Type /help for list of commands\r\n')


def who(sock, channel):
    """Function processes who command which shows
    user other users connected to server

    :param sock: socket object
    """

    if channel is None:
        # prompt
        sock.send('\nUsers currently connected to server\r\n')

        # make string out of USER_LIST array
        user_list = ", ".join(USER_LIST)

        # send string
        sock.send('%s\r\n' % user_list)

    else:
        users_in_channel = []

        # No channels yet
        if len(CHANNEL_LIST) == 0:
            sock.send('\nNo channels currently on server\r\n')

        # We have channels to peek at
        else:
            # check if channel is in the list
            if channel in CHANNEL_LIST:

                # it is so tell the user who is in there
                sock.send("\nUsers in %s\r\n" % channel)

                # go through the accounts
                for key in accounts:

                    # if channel listed in account, store it in array
                    if channel in accounts[key]['channels']:
                        users_in_channel.append(accounts[key]['username'])

                # turn array into string
                users_in_channel = ", ".join(users_in_channel)

                # send info to client who requested it
                sock.send('%s\r\n' % users_in_channel)

            # uh oh channel not in the list
            else:
                sock.send('\nNo channel named %s\r\n' % channel)


def list(sock):
    """Function processes list command which shows user list of channels on server
    If no channels are currently on the server then the user is prompted
    Otherwise, each channel in CHANNEL_LIST is sent to the user

    :param sock: socket object
    """

    # channel list is 0 so no channels
    if len(CHANNEL_LIST) == 0:
        sock.send('\nNo channels currently on server\r\n')

    # channel list is not 0 so send the list
    else:
        # prompt the client
        sock.send('\nList of channels on server\r\n')

        # grab the channel list which is an array
        # and turn it a string
        channel_list = ", ".join(CHANNEL_LIST)

        # send string off to client
        sock.send('%s\r\n' % channel_list)


def logoff(sock):
    """Function processes exit command which logs a client off the server

    First this function tells everyone what is going on
    Second it removes the client from each channel they are in
    Third it removes user from list
    Fourth it closes the socket and removes it from connection list

    :param sock: socket object
    """

    user = accounts[sock]['username']
    channels = accounts[sock]['channels']

    # tell everyone that someone is leaving
    broadcast_data(sock, '\n%s has gone offline\r\n' % user)

    # Remove user from all the channels that they are currently in
    # this is a nifty trick right here and necessary in this case!
    # iterate over the list backwards, removing channels 1 at a time!
    for i in xrange(len(channels) - 1, -1, -1):
        leavechannel(sock, channels[i])

    # for the server log
    logging.info('%s is offline' % user)

    # remove client from user list
    USER_LIST.remove(user)

    logging.info('Updated user list: %s' % USER_LIST)

    # close the socket
    sock.close()

    # remove socket from connection list
    CONNECTION_LIST.remove(sock)

    # remove account
    del accounts[sock]


def whois(sock, username):
    """Function processes a whois command
    which reveals info about a specific username

    :param sock: socket object
    :param username: user to look up
    """

    # check to see if username exists
    if username in USER_LIST:

        # it does so lets find the socket
        # that is associated with that username
        for key in accounts:
            if accounts[key]['username'] == username:
                ip = accounts[key]['ip']  # store ip
                channels = accounts[key]['channels']  # store channel array
                break  # break out of for loop

        # send client some info on this socket
        sock.send('\nUser: %s [%s]\r\n' % (username, ip))

        # check to see if this socket is in any channels
        if len(channels) > 0:
            # grab the array of channels
            # associated with the socket
            # and turn it into a string
            channel_list = ",".join(channels)

            # send client the channels
            sock.send('\nChannels: %s\r\n' % channel_list)

        # socket is not in any channels
        else:
            sock.send('\n%s is currently not in any channels\r\n' % username)

    # username doesn't exist
    else:
        sock.send('\n%s not currently connected to server\r\n' % username)


def joinchannel(sock, channel):
    """Function processes join command which joins user to channel

    :param sock: socket object
    :param channel: channel name
    """

    user = accounts[sock]['username']
    num_channels = len(accounts[sock]['channels'])

    if channel in CHANNEL_LIST:

        # make sure channel limit not reached
        if num_channels < 10:

            # add channel to user's channels
            accounts[sock]['channels'].append(channel)

            # make channel the user's current channel
            accounts[sock]['current'] = channel

            # notify client
            sock.send('\nJoined %s\r\n' % channel)

            # tell everyone someone has arrived
            broadcast_data(sock, ('\n%s joined %s\r\n') % (user, channel))

        else:
            # notify user that limit reached
            sock.send('\nChannel limit reached\r\n')

    else:

        # make sure channel limit not reached
        if num_channels < 10:

            # make sure channel starts with # character
            if channel.find('#') == 0:

                # create channel by adding it to the channel list
                CHANNEL_LIST.append(channel)

                # add channel to user's channels
                accounts[sock]['channels'].append(channel)

                # make channel the user's current channel
                accounts[sock]['current'] = channel

                # notify client
                sock.send('\nJoined %s\r\n' % channel)

                # tell everyone someone has arrived
                broadcast_data(sock, ('\n%s joined %s\r\n') % (user, channel))

                # for the server logs
                logging.info('New channel: %s' % channel)
                logging.info('Updated channel list: %s' % CHANNEL_LIST)

            # invalid channel name, no bueno
            else:
                sock.send('\nInvalid channel name\r\n')
                sock.send('\nSee /help join\r\n')

        else:
            # notify user that limit reached
            sock.send('\nChannel limit reached\r\n')


def leavechannel(sock, channel):
    """Function processes exit command which removes user from channel

    :param sock: socket object
    :param channel: channel to leave
    """

    user = accounts[sock]['username']
    channels = accounts[sock]['channels']

    # check to see if user is even in that channel
    if channel in channels:

        # tell channel that user is leaving
        broadcast_data(sock, ('\n%s left %s\r\n') % (user, channel))

        # user has the channel in their channel list
        # check to see if its their current channel
        if accounts[sock]['current'] == channel:

            # reset current channel
            accounts[sock]['current'] = ''

            # remove channel from user's
            # channel list
            accounts[sock]['channels'].remove(channel)

            # notify user
            sock.send('\nYou left %s\r\n' % channel)

            # update channels variable
            channels = accounts[sock]['channels']

            # update current channel by
            # randomly selecting a channel from their list
            if len(channels) > 0:
                current = random.choice(channels)
                accounts[sock]['current'] = current
                sock.send('\nCurrent channel is now %s\r\n' % current)

        # not user's current channel
        else:
            # remove channel from user's
            # channel list
            accounts[sock]['channels'].remove(channel)

            # notify user
            sock.send('\nYou left %s\r\n' % channel)

        # Now we need to check to
        # see if we should remove that channel
        # from the channel list

        # counter variable
        count = 0

        # go through the accounts
        for key in accounts:

            # found accounts in channel
            if channel in accounts[key]['channels']:

                # count em up
                count += 1

        # count is equal to 0 so no one in channel
        if count == 0:

            # remove from channel list
            CHANNEL_LIST.remove(channel)

            # log info for server
            logging.info('%s removed from channel list' % channel)
            logging.info('Updated channel list: %s' % CHANNEL_LIST)

    # user isn't in that channel
    else:

        # tell user they are stupid
        sock.send('\nNot in channel\nMust be in a channel to leave\r\n')


def switchcurrent(sock, channel):
    """Function processes a current command which allows a user
    to switch current channel

    :param sock: socket object
    :param channel: channel to switch to
    """

    # as long as they are in that channel
    if channel in accounts[sock]['channels']:

        # switch current channel
        accounts[sock]['current'] = channel

        # store current channel
        current = accounts[sock]['current']

        # notify of successful switch
        sock.send('\nCurrent channel is now %s\r\n' % current)

    # otherwise, no bueno bruh
    else:

        # tell user whats up bruh
        sock.send('\nCurrently not in %s\nMust be in channel\r\n' % channel)


def changenick(sock, nick):
    """Function processes a nick command
    which changes the user's username

    :param sock: socket object
    :param nick: new username (optional)
    """

    # nick argument not provided
    # echo back username
    if nick is None:
        sock.send('\nCurrent username: %s\r\n' % accounts[sock]['username'])

        # get outta here
        return

    # nick argument provided
    # check to see if its in the list
    if nick in USER_LIST:

        # its in the list, now
        # check to see if that is already
        # their username!
        if nick == accounts[sock]['username']:
            sock.send('\nThats already your username\r\n')

        # nope its not but its in use!
        else:
            sock.send('\nUsername already in use\r\n')
    else:

        # store old username
        old = accounts[sock]['username']

        # remove the old username
        USER_LIST.remove(old)

        # set new username
        accounts[sock]['username'] = nick

        # update the USER_LIST
        USER_LIST.append(nick)

        # tell everyone about the change
        broadcast_data(sock, '\n%s is now know as %s\r\n' % (old, nick))
        sock.send('\nNow known as %s\r\n' % nick)


def signal_handler(signal, frame):
    """Function handles signal interrupt (CTRL-C)

    :param signal: signal caught
    :param frame: current stack frame
    """

    for s in CONNECTION_LIST:
        if s != server_socket:
            logoff(s)
    server_socket.close()

    logging.info('Server shutting down')
    sys.exit(0)


# initialize signal handler
signal.signal(signal.SIGINT, signal_handler)

if __name__ == "__main__":
    """Main function

    """

    # for logging information on the server
    logging.basicConfig(level=logging.INFO,
                        format='[%(asctime)s] %(levelname)s: %(message)s',
                        datefmt='%d/%m/%Y %I:%M:%S %p')

    # to keep track of user information
    accounts = {}

    # list to keep track of usernames
    USER_LIST = []

    # list to keep track of socket descriptors
    CONNECTION_LIST = []

    # array to keep track of channels
    CHANNEL_LIST = []

    # receiving buffer size
    RECV_BUFFER = 512

    # server port number
    PORT = 6667

    # create TCP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # set socket options
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # bind socket
    server_socket.bind(("0.0.0.0", PORT))

    # start listening with backlog of 10
    server_socket.listen(10)

    # Add server socket to the list of readable connections
    CONNECTION_LIST.append(server_socket)

    server_ip = socket.gethostbyname(socket.gethostname())
    server_port = str(PORT)

    # information that might be useful to clients
    logging.info('Chat server started [%s:%s]' % (server_ip, server_port))

    while 1:
        # Get the list sockets which are ready to be read through select
        read_sockets, write_sockets, error_sockets = select.select(
            CONNECTION_LIST, [], [])

        for sock in read_sockets:

            # New connection
            if sock == server_socket:

                # Handle the case in which there is
                # a new connection recieved through server_socket
                sockfd, addr = server_socket.accept()

                # Add to connection list
                CONNECTION_LIST.append(sockfd)

                # create an account, in the account dictionary
                accounts[sockfd] = {
                    'username': '',
                    'ip': '',
                    'channels': [],
                    'current': ''
                }

                # store IP address
                accounts[sockfd]['ip'] = addr[0]

                # get the client's username
                name = sockfd.recv(RECV_BUFFER)

                # check to see if its already being used
                if name in USER_LIST:

                    sockfd.send('\nUsername already in use\r\n')
                    sockfd.close()
                    CONNECTION_LIST.remove(sockfd)

                else:

                    # welcome new user!
                    sockfd.send('Username authenticated!\r\n')
                    sockfd.send('Welcome to Internet Relay Chat!!\r\n')
                    sockfd.send('type /help for list of commands\r\n')
                    # set the username in the account
                    accounts[sockfd]['username'] = name

                    # add to user list
                    USER_LIST.append(name)

                    # log some info for the server
                    logging.info('Client (%s, %s) connected' % addr)
                    logging.info('Client is know as %s' % name)
                    logging.info('Updated user list: %s' % USER_LIST)

            # Some incoming message from a client
            else:
                # Data recieved from client, process it
                try:

                    # receive and strip data
                    # stripping makes parsing easier (I guess)
                    data = sock.recv(RECV_BUFFER).strip()

                    # we have data
                    if data:

                        # look to see if its a command
                        if data.find('/') == 0:

                            # it is so lets parse the message as is
                            parse_data(sock, data)

                        # no command probably intended to be
                        # normal chat message
                        else:
                            parse_data(sock, '/PRIVMSG ' + data)

                except:
                    logoff(sock)
                    continue
