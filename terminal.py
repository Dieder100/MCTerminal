import asyncio
import re
import string
from datetime import datetime

from textual.app import App, ComposeResult
from textual.widgets import Input, RichLog
from textual.containers import Horizontal, Vertical
from textual.events import Key

from observer import Observer

def format(s: str):
    return re.sub(r'\x1b\[[0-9;]*m', '', s.strip())

def clean_string_simple(s: str) -> str:
    printable = set(string.printable)
    return ''.join(ch for ch in s if ch in printable)

def add_log(widget, log, tag=""):
    log = format(log)
    if not log:
        return
    
    if tag != "":
        widget.write(f"{tag} {log}")
    else:
        widget.write(f"{log}")

class MCTerminal(App, Observer):

    CSS = """
    App {
        background: black;
    }
    Horizontal {
        background: black;
        height: 100%;
    }
    Vertical {
        background: black;
        width: 40%;
    }
    RichLog {     
        background: black;
        border: white;
        scrollbar-visibility: hidden;
    }
    Input {
        background: black;
        height: 3;
    }
    """
    
    def __init__(self, config, ping_delay, query_delay, timeout):
        App.__init__(self)
        Observer.__init__(self, config, ping_delay, query_delay, timeout)

        self.log_widget = RichLog(wrap=True)
        self.ping_widget = RichLog(wrap=True)
        self.query_widget = RichLog(wrap=True)
        self.debug_widget = RichLog(wrap=True)
        self.input = Input()

        self.history = []
        self.history_index = -1

    def compose(self) -> ComposeResult:
        with Horizontal():
            with Vertical():
                yield self.ping_widget
                yield self.query_widget
                yield self.debug_widget
                yield self.input
            yield self.log_widget

    async def on_input_submitted(self, event: Input.Submitted):
        command = event.input.value
        if not command:
            return        
        await self.command_queue.put(command)

        event.input.value = ""
        self.history_index = 0
        if not self.history or command != self.history[-1]:
            self.history.append(command)

    def on_key(self, event: Key):
        if event.key == "ctrl+r":
            self.restart()

        if not self.input.has_focus:
            return
        
        match(event.key):
            case "up":
                if self.history:
                    self.history_index -= 1
                    # TODO: Use clipping or wrapping back
                    self.history_index %= -(len(self.history) + 1)
                
            case "down":
                if self.history:
                    self.history_index += 1
                    self.history_index = min(0, self.history_index)

        if self.history and (event.key == "up" or event.key == "down"):
            if self.history_index == 0:
                self.input.value = ""
                return
            self.input.value = self.history[self.history_index]

    async def on_mount(self):
        self.start()
        asyncio.create_task(self.consume_all_streams())
    
    def render_query_widget(self):
        self.query_widget.clear()
        if self.query_output.get('_error') != None:
            self.query_widget.write(self.query_output.get('_error'))
            return
        
        if self.query_output.get('numplayers') == None:
            return

        self.query_widget.write(f"Online Players ({self.query_output.get('numplayers')}/{self.query_output.get('maxplayers')})")
        for player in self.query_output.get("players"):
            self.query_widget.write(f"  {format(player)}")

    def render_ping_widget(self):
        self.ping_widget.clear()
        if self.ping_output.get('_error'):
            self.ping_widget.write(self.query_output.get('_error'))
            return
        
        self.ping_widget.write(f"Version: {self.query_output.get('version')}")
        self.ping_widget.write(f"Enforce Secure Chat: {self.ping_output.get('enforcesSecureChat')}")
        self.ping_widget.write(f"Latency: {self.ping_output.get('time')}")
    
    async def consume_all_streams(self):
        while True:
            while not self.log_output.empty():
                log = await self.log_output.get()
                add_log(self.log_widget, log)

            while not self.debug_output.empty():
                log = await self.debug_output.get()
                now = datetime.now()
                formatted_time = now.strftime("%H:%M:%S")
                add_log(self.debug_widget, log, tag=f"[{formatted_time}] [Rcon/Debug]:")

            self.render_query_widget()
            self.render_ping_widget()

            await asyncio.sleep(0.25)