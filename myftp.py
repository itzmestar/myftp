#!/usr/bin/python

import socket, select, string, sys
import getpass
import os.path

#global variables
local_port=""
local_ip=""

#socket for data connection
ser_sock=None

curcmd=""
curarg=""

#socket for command connection to ftp server
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(2)

#opens the data connection socket
def open_sock():
	global ser_sock
	global local_port
	#generate temp port
	local_port=local_port+1
	ser_sock = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
	ser_sock.bind( (local_ip, local_port) )
	ser_sock.listen( 1 )

#closes the data connection socket
def close_sock():
	global ser_sock
	ser_sock.close()
	ser_sock=None

#returns the telnet command format
def telnet_cmd(msg):
	#remove newline char
	msg = msg.rstrip("\n")
	#add carriage return & new line char for telnet commands
	msg = msg + '\r' + '\n'
	return msg

#reads input from user
def read_user_input():
	#read from terminal
	msg = sys.stdin.readline()
	return msg

#sends command over socket
def send_cmd(msg):
	#send command in byte form
	s.send(bytes(msg))

#prompt to enter username
def ask_user():
	usr = telnet_cmd(raw_input('FTP USER: '))
	usr = 'USER '+ usr
	return usr

#prompt to enter password
def ask_pass():
	pss = telnet_cmd(getpass.getpass('Password: '))
	pss = 'PASS '+ pss
	return pss

#convert port to command format
def convert_port(port):
	p= repr(port//256) + ',' + repr(port%256)
	return p

#returns the port command	
def port_cmd():	
	cmd = 'PORT ' + local_ip.replace('.',',') + ',' + convert_port(local_port)
	cmd = telnet_cmd(cmd)
	return cmd

#handle the ls command: receives the ls output from server
def handle_ls():
	# use global variables
	global curcmd
	global ser_sock
	#accept connection
	newsock, (remhost, remport) = ser_sock.accept()
	while True:
		d= newsock.recv(1024)
		if not d:
			newsock.close()
			break
		else :
			#print data
			sys.stdout.write(d)
			sys.stdout.flush()
	close_sock()
	curcmd=""

#handles get command: receives the requested file to server
def handle_get():
	# use global variables
	global curcmd
	global ser_sock
	global curarg
	
	ndata=0 #number of bytes received
	#accept connection
	newsock, (remhost, remport) = ser_sock.accept()
	#open the file to write data to
	with open(curarg, 'wb') as f:
		while True:
			d= newsock.recv(1024)
			if not d:
				newsock.close()
				break
			#increment number of bytes received
			ndata = ndata + len(d)
			# write data to the file
			f.write(d)
	#close the file
	f.close()
	#close socket
	close_sock()
	#print message to screen
	print (ndata, 'bytes received from peer.')
	#reset global variables
	curcmd=""
	curarg=""

#handles put command: sends the requested file to server
def handle_put():
	# use global variables
	global curcmd
	global curarg
	global ser_sock
	
	ndata=0 #number of bytes sent
	#accept connection
	newsock, (remhost, remport) = ser_sock.accept()
	#open the file to read data from
	with open(curarg, 'rb') as f:
		l = f.read(1024)
		while(l):
			#increment number of bytes sent
			ndata = ndata + newsock.send(l)
			l = f.read(1024)
	#close the file
	f.close()
	#close socket
	close_sock()
	#print message to screen
	print (ndata, 'bytes sent to peer.')
	#reset global variables
	curcmd=""
	curarg=""

#handle if there are multiple spaces in the user command
def handle_multiple_spaces(msg):
	#remove spaces before & after cmd
	msg = msg.rstrip().lstrip()
	#remove adjacent 2 spaces
	while "  " in msg:
		msg = msg.replace("  "," ")
	return msg

#handle user command & validate if command is ok/nok
def handle_user_cmd(cmd):
	# use global variables
	global curcmd
	global curarg
	if cmd == '\n':
		return False
	#remove newline 
	cmd = cmd.rstrip("\n")
	cmd = handle_multiple_spaces(cmd)

	if cmd == "ls":
		curcmd='ls'
		#create a data socket
		open_sock()
		#send port cmd to server
		send_cmd(port_cmd())
		return True

	elif cmd.startswith("get"):
		#check if its a 2 word command
		if len(cmd.split()) !=2:
			print ("Usage: get remote-file")
			return False
		file = cmd.split()[1]
		curcmd="get"
		curarg=file
		#create a data socket
		open_sock()
		#send port cmd to server
		send_cmd(port_cmd())
		return True
		
	elif cmd.startswith("put"):
		#check if its a 2 word command
		if len(cmd.split()) !=2:
			print ("Usage: put local-file")
			return False
		file = cmd.split()[1]
		#check if file exists
		if not os.path.isfile(file):
			print (file,"Error: file not found")
			return False
		curcmd="put"
		curarg=file
		#create a data socket
		open_sock()
		#send port cmd to server
		send_cmd(port_cmd())
		return True
		
	elif cmd == "quit":
		send_cmd(telnet_cmd(cmd))
		return True

	elif cmd.startswith("delete"):
		if len(cmd.split()) !=2:
			print ("Usage: delete remote-file")
			return False
		cmd=cmd.replace('delete', 'DELE')
		send_cmd(telnet_cmd(cmd))
		return True

	elif not cmd:
		return False
	else:
		print ("?Invalid command")
		return False

#gives user myftp> prompt
def prompt():
	sys.stdout.write('myftp> ')
	sys.stdout.flush()
	
#main function
if __name__ == "__main__":
     
	if(len(sys.argv) < 2) :
		print ('Usage : python myftp hostname')
		sys.exit()
     
	host = sys.argv[1]
	port = 21
     
    # connect to remote host
	try :
		s.connect((host, port))
		#get the local ip & port
		local_ip,local_port=s.getsockname()
		
	except :
		print ('Unable to connect')
		s.close()
		sys.exit()
     
	print ("Connected to %s" % host)
    
	try:
		while 1:
			socket_list = [sys.stdin, s]
         
			# Get the list sockets which are readable
			read_list, write_list, error_list = select.select(socket_list , [], [])
         
			for sock in read_list:
				#incoming message from remote server
				if sock == s:
					data = sock.recv(4096)
					if not data :
						print ('Connection closed')
						s.close()
						sys.exit()
					else :
				#print data
						#sys.stdout.write(data)
						if data.startswith('220'):
							sys.stdout.write(data)
							send_cmd( ask_user())
						elif data.startswith('331'):
							sys.stdout.write(data)
							send_cmd( ask_pass())
						elif data.startswith('200 PORT'):
							sys.stdout.write(data)
							if curcmd == 'ls':
								send_cmd(telnet_cmd('LIST'))
							elif curcmd == 'put':
								cmd = 'STOR ' + curarg
								send_cmd(telnet_cmd(cmd))
							elif curcmd == 'get':
								cmd = 'RETR '+ curarg
								send_cmd(telnet_cmd(cmd))
						elif data.startswith('125'):
							sys.stdout.write(data)
							if curcmd == 'ls':
								handle_ls()
							elif curcmd == 'get':
								handle_get()
							elif curcmd == 'put':
								handle_put()
						else : sys.stdout.write(data)
				#user entered a message
				else :
					msg = read_user_input()
					handle_user_cmd(msg)
				prompt()
	except socket.timeout:
		print ('caught a timeout.')
		s.close()
	except socket.error as err:
		print (err)
		s.close()
