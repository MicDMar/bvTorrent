from os import listdir
from os.path import isfile, join
import os
import sys
import threading
import hashlib
import time

from socket import *


DEFAULT_PORT = 42424


#Reads in all the bytes that we were expecting to recieve
#from the server.
def getAllBytes(bytesExpected, conn):
  data = []
  while len(data) < bytesExpected:
    chunk = conn.recv(bytesExpected - len(data))
    data += chunk
  return data

#Reads in bytes one at a time so that it can stop
#at a new line character. (\n)
def getByteLine(conn):
  data = ""
  
  #Push one byte into the data array
  byte = conn.recv(1)
  data += byte.decode()

  index = 0
  while data[index] != '\n':
    byte = conn.recv(1)
    data += byte.decode()
    index += 1
  return data[:-1]

#Sends a 12-byte control message to the tracker detailing the clients intentions.
def sendControlMsg(msg, conn):
  #TODO

#Handles the New Connection Protocol specified by the tracker.
def handleNewConnection(conn):
  #TODO

#Handles the protocol for updating the clients Bit Mask.
#Will send the tracker 1's and 0's equal to the number of chunks for the file,
#terminated by a '\n'.
def handleUpdateMask(conn):
  #TODO

#Handles the protocol for updating current connected clients.
#Will recieve number of clients from the tracker and descriptors of each client.
def handleClientListRequest(conn):
  #TODO


def main():

  print("Establishing a connection for download.")

  #Establish a connection to the tracker.
  conn = socket(AF_INET, SOCK_STREAM)
  conn.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
  conn.connect((address, port))

  handleNewConnection(conn)
  
  print("Finished Downloading!")
  print("Closing Connection...")

  #Close the connection to the tracker.
  conn.close()


if __name__ == "__main__":
  main()
