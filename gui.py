import os
import webview
from threading import Thread
from time import sleep
from http.client import HTTPConnection

host = "127.0.0.1"
port = 8003


def main():
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    t = Thread(
        target=execute_from_command_line,
        args=(["manage.py", "runserver", "--noreload", f"{host}:{port}"],),
    )
    t.daemon = True
    t.start()

    while not url_ok(host, port):
        sleep(0.1)

    webview.create_window("LocalAI", f"http://{host}:{port}", server=None)
    webview.start(gui="gtk")


def url_ok(host: str, port: int):
    try:
        conn = HTTPConnection(host, port)
        conn.request("GET", "/")
        r = conn.getresponse()
        return r.status == 200
    except:
        # Server not started
        return False


if __name__ == "__main__":
    main()
