
import asyncio
from mctools import AsyncRCONClient, QUERYClient, AsyncPINGClient

async def logging_process_async(
        config: dict[str | int], 
        output: asyncio.Queue[str], 
        flag: list[bool]):
    
    ssh_cmd = [
        "ssh", "-T",
        f"{config['SSH_USER']}@{config['HOST_IP']}",
        f"journalctl -u {config['SERVER_NAME']}.service -f -o cat"
    ]

    proc = await asyncio.create_subprocess_exec(
        *ssh_cmd,
        stdin=asyncio.subprocess.DEVNULL,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    while flag[0]:
        if proc.returncode != None:
            await output.put("[Error]: No Connection")
            break

        line = await proc.stdout.readline()
        await output.put(line.decode())

async def rcon_command_process_async(
        config: dict[str | int], 
        output: asyncio.Queue[str], 
        command_queue: asyncio.Queue[str],
        flag: list[bool]):
    
    rcon = AsyncRCONClient(
        config["HOST_IP"],
        config["RCON_PORT"],
    )

    try:
        await rcon.authenticate(config["RCON_PASSWORD"])
        while flag[0]:
            command = await command_queue.get()
            response = await rcon.command(command)
            await output.put(response)
    except Exception:
        await output.put("[Error]: No Connection")

async def ping_process_async(
        config: dict[str | int],
        output: dict[str | int],
        delay: float,
        timeout: float,
        flag: list[bool]):
    
    ping = AsyncPINGClient(
        config["HOST_IP"],
        config["MC_PORT"]
    )
    
    output["_error"] = None
    try:
        while flag[0]:
            stats = await asyncio.wait_for(
                ping.get_stats(), 
                timeout=timeout
            )
            output.update(stats)
            await asyncio.sleep(delay)
    except Exception:
        output["_error"] = "[Error]: No Connection"

async def query_process_async(
        config: dict[str | int],
        output: dict[str | int], 
        delay: float,
        timeout: float,
        flag: list[bool]):
    
    query = QUERYClient(
        config["HOST_IP"],
        config["QUERY_PORT"]
    )

    output["_error"] = None
    try:
        while flag[0]:
            stats = await asyncio.wait_for(
                asyncio.to_thread(query.get_full_stats), 
                timeout=timeout
            )
            output.update(stats)
            await asyncio.sleep(delay)
    except Exception:
        output["_error"] = "[Error]: No Connection"

class Observer:
    def __init__(self, config, ping_delay, query_delay, timeout):
        self.log_output = asyncio.Queue()
        self.ping_output = dict()
        self.query_output = dict()
        self.command_queue = asyncio.Queue()
        self.debug_output = asyncio.Queue()

        self.config = config
        self.ping_delay = ping_delay
        self.query_delay = query_delay
        self.timeout = timeout

    def start(self):
        self._flag = [True]
        self.logging_task = asyncio.create_task(
            logging_process_async(self.config, self.log_output, self._flag)
        )
        self.command_task = asyncio.create_task(
            rcon_command_process_async(self.config, self.debug_output, self.command_queue, self._flag)
        )
        self.ping_task = asyncio.create_task(
            ping_process_async(self.config, self.ping_output, self.ping_delay, self.timeout, self._flag)
        )
        self.query_task = asyncio.create_task(
            query_process_async(self.config, self.query_output, self.query_delay, self.timeout, self._flag)
        )

    def restart(self):
        if self.logging_task.done():
            self.logging_task = asyncio.create_task(
                logging_process_async(self.config, self.log_output, self._flag)
            )
        if self.command_task.done():
            self.command_task = asyncio.create_task(
                rcon_command_process_async(self.config, self.debug_output, self.command_queue, self._flag)
            )
        if self.ping_task.done():
            self.ping_task = asyncio.create_task(
                ping_process_async(self.config, self.ping_output, self.ping_delay, self.timeout, self._flag)
            )
        if self.query_task.done():
            self.query_task = asyncio.create_task(
                query_process_async(self.config, self.query_output, self.query_delay, self.timeout, self._flag)
            )

    def stop(self):
        self._flag[0] = False

    def active(self):
        return self._flag[0]