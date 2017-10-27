# myftp
ftp client implementation using python
=======================================

Its a simplified FTP client that works in the active mode.
It doesn't uses the ftp lib provided by the python.
Implementation is done using the TCP sockets.

At the moment, only following basic commands are supported:
> ls 
List the files in the current directory of the remote server.

> get <rempte-filename>
Download the file <remote-filename> from the ftp server

> put <local-filename>
Upload the file <local-filename> from the local machine to ftp server

> delete <rempte-filename>
Delete the file <remote-filename> from the ftp server

> quit
Close the ftp session

=============================================
Tested to work with Windows FTP server on Windows 10

===========
How to run:
-----------
# python myftp.py <ftp-server-name or IP>

