from app import create_app, setup_app
from config import get_config
import uvicorn
import logging.config
import sys
import asyncio

app = None
cfg = get_config()

logging.config.dictConfig(cfg.LOGGING_CONFIG)
if cfg.DEFAULT_LOGGING_LEVEL:
    logging.getLogger().setLevel(cfg.DEFAULT_LOGGING_LEVEL)

async def setup():
    global cfg
    await setup_app(cfg)

def run():
    global cfg, app
    app = create_app(cfg)
    uvicorn.run(app, host=cfg.APP_HOST, port=cfg.APP_PORT, lifespan="on")

def print_logo():
    print("\n")
    print("░▒▓███████▓▒░░▒▓███████▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░░▒▓██████▓▒░  ")
    print("░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ ")
    print("░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒▒▓█▓▒░░▒▓█▓▒░░▒▓█▓▒░ ")
    print("░▒▓███████▓▒░░▒▓███████▓▒░░▒▓█▓▒░░▒▓█▓▒▒▓█▓▒░░▒▓████████▓▒░ ")
    print("░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░ ░▒▓█▓▓█▓▒░ ░▒▓█▓▒░░▒▓█▓▒░ ")
    print("░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░ ░▒▓█▓▓█▓▒░ ░▒▓█▓▒░░▒▓█▓▒░ ")
    print("░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░  ░▒▓██▓▒░  ░▒▓█▓▒░░▒▓█▓▒░ ")
    print("\n")

def print_help():
    print("Usage: python main.py <command>")
    print("")
    print("Commands:")
    print("  setup    Setup the Node")
    print("  run      Run the Node")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "setup":
            print_logo()
            asyncio.run(setup())
        elif command == "run":
            print_logo()
            run()
        else:
            print(f"Unknown command: {command}\n")
            print_help()
    else:
        print("No command provided.\n")
        print_help()
