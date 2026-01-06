
import asyncio
import json

from terminal import MCTerminal

async def main():
    with open("config.json") as f:
        config = json.load(f)

    app = MCTerminal(config, 2.0, 1.0, 10.0)
    await app.run_async()

if __name__ == "__main__":
    asyncio.run(main())