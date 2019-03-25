from os import listdir
from os.path import isfile, join
import os, hashlib, math, random, sys, time, threading

from socket import *

DEFAULT_TRACKER_ADDRESS = "localhost"
DEFAULT_TRACKER_PORT = 42424
DEFAULT_CLIENT_PORT = 3000
CLIENT_LIST_UPDATE_INTERVAL = 60

FILE_NAME = ""
MAX_CHUNK_SIZE = ""
NUM_FILE_CHUNKS = ""
BYTE_MASK = ""

file_data = None
digests = []
chunk_sizes = []
clients = {} # { (ip,port) : bytemask, ... }
client_list_lock = threading.Lock()

port = os.environ.get("PORT", DEFAULT_CLIENT_PORT)
tracker_address = os.environ.get("TADDRESS", DEFAULT_TRACKER_ADDRESS)
tracker_port = os.environ.get("TPORT", DEFAULT_TRACKER_PORT)


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
    #while len(data) == 0:
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
    conn.send("{}\n".format(msg).encode())

#Handles the New Connection Protocol specified by the tracker.
def handleNewConnection(conn):
    global BYTE_MASK, file_data, digests, chunk_sizes
    FILE_NAME = getByteLine(conn)
    MAX_CHUNK_SIZE = getByteLine(conn)
    NUM_FILE_CHUNKS = int(getByteLine(conn))

    total_size = 0

    for i in range(NUM_FILE_CHUNKS):
        sz, digest = getByteLine(conn).split(',')
        total_size += int(sz)
        digests.append(digest)
        chunk_sizes.append(sz)
        BYTE_MASK += '0'
        file_data.append(b'0')
        
    # file_data = bytes(total_size)

    BYTE_MASK += '\n'

    conn.send(("{},{}".format(port, BYTE_MASK)).encode())

#Handles the protocol for updating the clients Bit Mask.
#Will send the tracker 1's and 0's equal to the number of chunks for the file,
#terminated by a '\n'.
def handleUpdateMask(conn):
    sendControlMsg("UPDATE_MASK", conn)
    conn.send(BYTE_MASK)

#Handles the protocol for updating current connected clients.
#Will recieve number of clients from the tracker and descriptors of each client.
def handleClientListRequest(conn):
    client_list_lock.acquire()
    global clients
    clients = {}
    sendControlMsg("CLIENT_LIST", conn)
    client_count = int(getByteLine(conn))

    for i in range(client_count):
        address, mask = getByteLine(conn).split(",")
        temp = address.split(":")
        key = (temp[0], int(temp[1])) 
        
        clients[key] = mask
    client_list_lock.release()

def chunk_indexes(chunk_num):
    start = 0
    for i in range(chunk_num-1):
       start += chunk_sizes[i]
    end = start + chunk_sizes[chunk_num] 

    return (start, end)

def serve_chunk(conn):
    # Figure out which chunk they want and see if we have it
    chunk_num = int(getByteLine(conn))
    
    # Determine the byte boundaries for the chunk they want
    startI, endI = chunk_indexes(chunk_num)
    data = file_data[startI:endI]

    # Send it
    conn.send(data)
    
def decide_chunk():
    chunk_search = {} # { chunk_num: (chunk_total_count, potential_hosts), ... }
    for client, client_mask in clients.items():
        
        for i in range(len(chunk_sizes)):
            # Check if the client has this chunk
            if client_mask[i] == '1':
                # If so, increment the count and add this client
                # to the list of potential hosts for this chunk
                t = chunk_search.get(i, (0, [])) 
                newCount = t[0] + 1
                newList = t[1]
                newList.append(client)
                chunk_search[i] = (newCount, newList)

    
    # Determine which key is the smallest
    smallest_key = math.inf
    potential_hosts = []
    selected_chunk = -1
    for chunk_num in chunk_search.keys():
        icount = chunk_search[chunk_num][0]
        host_count = len(chunk_search[chunk_num][1])
        if host_count > 0 and icount < smallest_key:
            smallest_key = icount
            potential_hosts = chunk_search[chunk_num][1]
            selected_chunk = chunk_num

    if len(potential_hosts) == 0:
        print("No further chunks available for this file")
        sys.exit(1)
        # We have no chunks available
        pass
    
    # Pick a random host from the ones who have this chunk
    selected_host = random.choice(potential_hosts)
    #print("Selected to get chunk from {}".format(selected_host))
    return (chunk_num, selected_host)
                

def serve_clients():
    listener = socket(AF_INET, SOCK_STREAM)
    listener.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    listener.bind(('0.0.0.0', port))
    listener.listen(4)
    
    while True:
        threading.Thread(target=serve_chunk, args=(listener.accept(),)).start()

def get_chunk(chunk_num, address):
    print(address)
    conn = socket(AF_INET, SOCK_STREAM)
    conn.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    conn.connect(address)

    # Connect to the client and retrieve the chunk
    # First send the chunk number
    conn.send("{}\n".format(chunk_num).encode())
    # Receive the bytes for the chunk
    chunk_data = getAllBytes(chunk_sizes[chunk_num], conn)
    
    if(digests[chunk_num] != chunk_data):
        break;

    # Store the bytes in the file data  
    j = 0
    for i in range(*chunk_indexes(chunk_num)):
        file_data[i] = chunk_data[j]
        j += 1
        
def update_clients(conn):
    while True:
        handleClientListRequest(conn)
        time.sleep(CLIENT_LIST_UPDATE_INTERVAL)
        
def main():
    print("Establishing a connection for download {}.".format((tracker_address, tracker_port)))

    #Establish a connection to the tracker.
    conn = socket(AF_INET, SOCK_STREAM)
    conn.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    conn.connect((tracker_address, tracker_port))

    handleNewConnection(conn)

    # Launch a thread to accept connections for others to download
    threading.Thread(target=serve_clients, daemon=True).start()

    # Launch a thread to update the client list periodically
    handleClientListRequest(conn) 
    threading.Thread(target=update_clients, args=(conn,)).start()

    # Get a chunk while our byte mask is not full
    while all(map(lambda x: x == '1', BYTE_MASK)) == False:
        selected_chunk, selected_host = decide_chunk()
        
        # Retrieve the chunk
        get_chunk(selected_chunk, selected_host)

    print("Finished Downloading!")
    print("Closing Connection...")
    input("Enter anything to exit")
    
    sendControlMsg("DISCONNECT", conn)
    
    # Write the file to disk
    with open(FILE_NAME, "wb") as f:
        f.write(file_data)

    #Close the connection to the tracker.
    conn.close()

if __name__ == "__main__":
    main()
