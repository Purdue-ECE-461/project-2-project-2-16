import socket
import sys
import threading

class Server:
    def __init__(self):
        self.port = 50000
        self.host = ''
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            self.socket.bind((self.host, self.port))
        except socket.error as err:
            print("Bind failed. Error Code: " + str(err[0]))
            print("Error message: " + err[1])
            sys.exit()
        
        print("Socket bind success")
        pass

    def processConnection(self, connection):
        while True:
            request = connection.recv(2048)
            print("Request: " + request)
            if not request:
                break

    def listen(self):
        self.socket.listen(5) # will queue up to 5 incoming connections before denying
        print("waiting for connection")
        while True:
            connection, addr = self.socket.accept()
            print("conneted to: " + addr[0] + ":" + str(addr[1]))

            threading.Thread(target=self.processConnection, args=(self, connection))
    
    
