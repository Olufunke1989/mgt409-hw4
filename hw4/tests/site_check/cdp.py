"""Tiny Chrome DevTools driver used for the Problem 11 screenshots.

Needs Google Chrome (macOS path below) and the `websockets` package, which
comes with uvicorn[standard]. Start the backend and frontend first, then run
from the hw4 folder, for example:
    .venv/bin/python tests/site_check/test1.py
"""
import asyncio
import base64
import json
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path

import websockets

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
SCRATCH = Path(tempfile.gettempdir())  # throwaway Chrome profile location
PORT = 9333


class Browser:
    def __init__(self, width=1440, height=1000, scale=1.5):
        self.width, self.height, self.scale = width, height, scale
        self.proc = None
        self.ws = None
        self.msg_id = 0

    async def start(self):
        self.proc = subprocess.Popen(
            [
                CHROME, "--headless=new", f"--remote-debugging-port={PORT}",
                f"--user-data-dir={SCRATCH / 'chrome-profile'}", "--no-first-run", "--no-default-browser-check",
                "--hide-scrollbars", f"--window-size={self.width},{self.height}", "about:blank",
            ],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        for _ in range(50):
            try:
                tabs = json.load(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json"))
                page = next(t for t in tabs if t["type"] == "page")
                break
            except Exception:
                time.sleep(0.2)
        self.ws = await websockets.connect(page["webSocketDebuggerUrl"], max_size=50_000_000)
        await self.cmd("Page.enable")
        await self.cmd("Runtime.enable")
        await self.cmd("Emulation.setDeviceMetricsOverride", width=self.width, height=self.height,
                       deviceScaleFactor=self.scale, mobile=False)

    async def cmd(self, method, **params):
        self.msg_id += 1
        my_id = self.msg_id
        await self.ws.send(json.dumps({"id": my_id, "method": method, "params": params}))
        while True:
            msg = json.loads(await self.ws.recv())
            if msg.get("id") == my_id:
                if "error" in msg:
                    raise RuntimeError(msg["error"])
                return msg.get("result", {})

    async def ev(self, js, timeout=180):
        res = await asyncio.wait_for(
            self.cmd("Runtime.evaluate", expression=js, awaitPromise=True, returnByValue=True), timeout
        )
        if "exceptionDetails" in res:
            raise RuntimeError(res["exceptionDetails"].get("exception", {}).get("description", res["exceptionDetails"]))
        return res.get("result", {}).get("value")

    async def goto(self, url, wait=2.5):
        await self.cmd("Page.navigate", url=url)
        await asyncio.sleep(wait)

    async def shot(self, path):
        data = await self.cmd("Page.captureScreenshot", format="png")
        Path(path).write_bytes(base64.b64decode(data["data"]))
        return path

    async def close(self):
        try:
            await self.ws.close()
        finally:
            self.proc.terminate()
