# MCTerminal
This repository implements a remote terminal for Minecraft servers with Python.

### Requirements
* For SSH logs:
  * The server must be managed by systemd on linux.
  * A working ssh connection to your server must be available
* For Rcon commands:
  * A valid rcon port must be opened
  * Rcon must be allowed on your server
  * Your rcon port in the server properties must be set to the opened port
* For Querying status:
  * A valid query port must be opened
  * Query must be allowed on your server
  * Your rcon port in the server properties must be set to the opened port
    
### Steps
* Fill the correct fields in the config for your server
* Make a virtual environment and pip install the required packages
* Start the virtual environment
* Start the main.py
