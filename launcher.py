from __future__ import annotations

import socket
import threading
import webbrowser

from app import create_app


def find_free_port(host: str = "127.0.0.1") -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((host, 0))
        return sock.getsockname()[1]


def open_browser(url: str) -> None:
    webbrowser.open(url, new=2)


def main() -> int:
    host = "127.0.0.1"
    port = find_free_port(host)
    app = create_app(seed_database=True)
    url = f"http://{host}:{port}"
    threading.Timer(1.0, open_browser, args=[url]).start()
    app.run(host=host, port=port, debug=False, use_reloader=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
