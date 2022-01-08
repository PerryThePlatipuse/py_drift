import socket
from _thread import *
from new_features import Player
import pickle
import pygame

clock = pygame.time.Clock()
width = 500
height = 500
window = pygame.display.set_mode((width, height))
pygame.display.set_caption("server")
window.fill((255, 255, 255))


server = "192.168.1.80"
port = 5555

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    s.bind((server, port))
except socket.error as e:
    str(e)

s.listen(2)
print("Waiting for a connection, Server Started")

players = [Player(0, 0, 50, 50, (255, 0, 0)), Player(100, 100, 50, 50, (0, 0, 255))]



def threaded_client(conn, player):
    conn.send(pickle.dumps(players[player]))
    reply = ""
    while True:
        try:
            clock.tick(60)
            data = pickle.loads(conn.recv(2048))
            players[player] = data
            players[0].move()
            window.fill((255, 255, 255))
            players[0].draw(window)
            players[1].draw(window)
            pygame.display.update()
            if not data:
                print("Disconnected")
                break
            else:
                if player == 1:
                    reply = players[0]
                else:
                    reply = players[1]

                print("Received: ", data)
                print("Sending : ", reply)
            conn.sendall(pickle.dumps(reply))
        except:
            break

    print("Lost connection")
    conn.close()


currentPlayer = 0
while True:
    conn, addr = s.accept()
    print("Connected to:", addr)

    start_new_thread(threaded_client, (conn, currentPlayer))
    currentPlayer += 1
