#!/usr/bin/env python3

import re
from colored import fg, attr

# Server options
MAX_CONNECTIONS = 10
SERVER_ADDRESS = ("0.0.0.0", 8888)
AUTHKEY = "secret"

# Operation names
EXEC_OP = 	re.compile(r"^EXEC [\w\d_]+$")
STOP_OP = 	re.compile(r"^STOP$")
PING_OP = 	re.compile(r"^PING [\w\d_]+$")
ALLE_OP = 	re.compile(r"^ALLE [01] .+?$")
LOGIN_OP = 	re.compile(r"^LOGIN [\w\d]+$")
UPDATE_OP = re.compile(r"^UPDATE$")
LS_OP = 	re.compile(r"^LS$")

# Debug options
DEBUG = True
WARN, INFO, DONE = range(3)
PREFIX = ["[WARN]", "[INFO]", "[DONE]"]
COLOR = [fg('red_1'), fg('khaki_1'), fg('sea_green_1b'), attr(0)]