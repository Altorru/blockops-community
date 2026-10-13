"""Synthetic Java Server List Ping endpoint; not Minecraft. For protocol QA only."""

import json, socket, threading


def varint(value):
    out = bytearray()
    while True:
        part = value & 127
        value >>= 7
        out.append(part | (128 if value else 0))
        if not value:
            return bytes(out)


def read_varint(sock):
    value = 0
    for i in range(5):
        b = sock.recv(1)
        if not b:
            raise EOFError()
        value |= (b[0] & 127) << (7 * i)
        if not b[0] & 128:
            return value
    raise ValueError("Invalid VarInt")


def packet(sock):
    n = read_varint(sock)
    if n > 4096:
        raise ValueError("Packet too large")
    data = b""
    while len(data) < n:
        part = sock.recv(n - len(data))
        if not part:
            raise EOFError()
        data += part
    return data


def serve_client(sock):
    try:
        sock.settimeout(5)
        packet(sock)  # Handshake
        if packet(sock) != b"\x00":
            return
        data = json.dumps(
            {
                "version": {"name": "BlockOps synthetic fixture", "protocol": 767},
                "players": {
                    "online": 1,
                    "max": 20,
                    "sample": [
                        {
                            "name": "FixturePlayer",
                            "id": "00000000-0000-0000-0000-000000000001",
                        }
                    ],
                },
                "description": {"text": "Synthetic fixture. No Minecraft binary."},
            }
        ).encode()
        body = b"\x00" + varint(len(data)) + data
        sock.sendall(varint(len(body)) + body)
        ping = packet(sock)
        if len(ping) == 9 and ping[0] == 1:
            sock.sendall(varint(len(ping)) + ping)
    except (OSError, EOFError, ValueError):
        pass
    finally:
        sock.close()


def serve(host="0.0.0.0", port=25565):
    server = socket.socket()
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen(10)
    while True:
        sock, _ = server.accept()
        threading.Thread(target=serve_client, args=(sock,), daemon=True).start()


if __name__ == "__main__":
    serve()
