"""Desktop launcher: runs the Flask server locally and shows a small control window.

Closing the window stops the server. No terminal is needed.
"""
import os
import sys
import threading
import tkinter as tk
import webbrowser

# Windowed builds have no stdout/stderr; libraries that print would crash.
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")

from werkzeug.serving import make_server  # noqa: E402

from app import app  # noqa: E402

HOST = "127.0.0.1"


def main() -> None:
    server = make_server(HOST, 0, app, threaded=True)  # port 0 = any free port
    url = f"http://{HOST}:{server.server_port}"
    threading.Thread(target=server.serve_forever, daemon=True).start()

    root = tk.Tk()
    root.title("YouTube to MP4")
    root.resizable(False, False)

    tk.Label(root, text="YouTube to MP4 is running", font=("Helvetica", 14, "bold")).pack(
        padx=32, pady=(24, 4)
    )
    tk.Label(root, text=url, fg="#57606a").pack(padx=32)
    tk.Label(root, text="Close this window to quit.", fg="#57606a").pack(padx=32, pady=(0, 12))
    tk.Button(root, text="Open in browser", command=lambda: webbrowser.open(url)).pack(pady=(0, 24))

    def quit_app() -> None:
        server.shutdown()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", quit_app)
    root.after(500, lambda: webbrowser.open(url))
    root.mainloop()


if __name__ == "__main__":
    main()
