import socket
import pickle

server = ""
port = 5555

games = {}
idCount = 0
currentPlayer = 0

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

s.bind((server, port))

s.listen()
print("Waiting for a connection, Server Started")

class Game:
    def __init__(self, id):
        self.connected = False

players = [Player(0), Player(1)]

def threaded_client(conn, player, gameId):
    global idCount
    conn.send(pickle.dumps(players[player]))
    reply = ""
    while True:
        try:
            data = pickle.loads(conn.recv(2048))
            players[player] = data
            if gameId in games:
                game = games[gameId]
                if not data:
                    print("Disconnected")
                    break
                else:
                    if player == 1:
                        reply = players[0]
                    else:
                        reply = players[1]

                conn.sendall(pickle.dumps(reply))
        except:
            break

    print("Lost connection")
    try:
        del games[gameId]
        print("Closing game", gameId)
    except:
        pass
    idCount -= 1
    conn.close()

while True:
    conn, addr = s.accept()
    print("Connected to:", addr)

    idCount += 1
    p = 0

    gameId = (idCount - 1) // 2

    if idCount % 2 == 1:
        games[gameId] = Game(gameId)
        players[0].connected = True
        print("Creating a new game")
        print("Waiting for another player")
    else:
        games[gameId].connected = True
        p = 1
        players[1].connected = True
        print("Game is available")



    start_new_thread(threaded_client, (conn, currentPlayer, gameId))
    currentPlayer += 1