import socket

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
    client.connect(("127.0.0.1", 5000))
    reader = client.makefile("r", encoding="utf-8")
    print("Connected. Type a message, or quit to exit.")
    while True:
        message = input("> ")
        if message == "quit":
            break
        client.sendall((message + "\n").encode("utf-8"))
        print(reader.readline().strip())
    