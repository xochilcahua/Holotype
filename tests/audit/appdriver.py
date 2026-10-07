# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Teo Monroy
import json, sys
from playwright.sync_api import sync_playwright
import os
APP = "file://" + os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "index.html")
class App:
    def __init__(self, url=APP):
        self.p = sync_playwright().start()
        self.b = self.p.chromium.launch()
        self.pg = self.b.new_page(viewport={"width":1280,"height":900})
        self.errors = []
        self.pg.on("pageerror", lambda e: self.errors.append(str(e)))
        self.pg.on("console", lambda m: self.errors.append("console."+m.type+": "+m.text) if m.type in ("error",) else None)
        self.pg.goto(url); self.pg.wait_for_timeout(800)
    def ev(self, js, arg=None):
        return self.pg.evaluate(js, arg) if arg is not None else self.pg.evaluate(js)
    def close(self):
        self.b.close(); self.p.stop()
