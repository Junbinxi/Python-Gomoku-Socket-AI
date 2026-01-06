import socket
import threading

# 設定
HOST = '0.0.0.0'
PORT = 5555

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen(2)

print(f"🔥 五子棋伺服器已啟動 (Port: {PORT})，等待玩家連線...")

clients = []

def handle_client(client_socket):
    while True:
        try:
            message = client_socket.recv(1024)
            if not message:
                break
            # 廣播訊息給對手
            for c in clients:
                if c != client_socket:
                    c.send(message)
        except:
            break
    
    if client_socket in clients:
        clients.remove(client_socket)
    client_socket.close()

while True:
    client_socket, addr = server.accept()
    print(f"玩家連線: {addr}")
    clients.append(client_socket)
    
    # 分配顏色
    if len(clients) == 1:
        client_socket.send("COLOR:BLACK".encode('utf-8'))
    elif len(clients) == 2:
        client_socket.send("COLOR:WHITE".encode('utf-8'))
        # 通知兩邊遊戲開始
        for c in clients: c.send("START".encode('utf-8'))
    
    thread = threading.Thread(target=handle_client, args=(client_socket,))
    thread.start()