import socket
import select
import threading

def handle_client(client_sock):
    try:
        backend_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        backend_sock.connect(('127.0.0.1', 8000))
        sockets = [client_sock, backend_sock]
        while True:
            readable, _, _ = select.select(sockets, [], [], 10.0)
            if not readable:
                break
            for s in readable:
                other = backend_sock if s is client_sock else client_sock
                data = s.recv(4096)
                if not data:
                    return
                other.sendall(data)
    except Exception as e:
        pass
    finally:
        client_sock.close()
        backend_sock.close()

def main():
    server = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('::1', 8000))
    server.listen(10)
    print("IPv6 bridge running on [::1]:8000 -> 127.0.0.1:8000")
    while True:
        client, _ = server.accept()
        t = threading.Thread(target=handle_client, args=(client,), daemon=True)
        t.start()

if __name__ == '__main__':
    main()
