from os import listdir
from os.path import isfile, join
import os
import sys
import threading
import hashlib
import time

from socket import *


DEFAULT_TRACKER_PORT = 42424
DEFAULT_CLIENT_PORT = 3000
FILE_NAME = ""
MAX_CHUNK_SIZE = ""
NUM_FILE_CHUNKS = ""
CHUNK_MSG = ""
BYTE_MASK = ""

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
  FILE_NAME = getByteLine(conn)
  MAX_CHUNK_SIZE = getByteLine(conn)
  NUM_FILE_CHUNKS = getByteLine(conn)
  CHUNK_MSG = getAllBytes(conn)

  for x in range(0, NUM_FILE_CHUNKS+1):
    BYTE_MASK += 0
  
  BYTE_MASK += '\n'
  
  conn.send((DEFAULT_CLIENT_PORT + "," + BYTE_MASK).encode())


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
