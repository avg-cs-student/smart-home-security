#!/bin/env python3
from base import BaseStation, BOLD, RED, END

port = 5000
server = BaseStation(port)

# <CTRL-C> to stop the server
print(RED + BOLD + "To stop the server, press <CTRL-C>" + END)
server.run()
