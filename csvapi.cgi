#!/usr/bin/env python
# vim: noexpandtab shiftwidth=4 softtabstop=4 tabstop=4

import socket
import struct
import time
import traceback
import urllib
import cgi
import cgitb
import sys
import re
import subprocess
import commands

fields = cgi.FieldStorage()
if fields.has_key("period"):
       period = fields.getvalue("period")
       
if fields.has_key("action"):
       action = fields.getvalue("action")
       
cmd = "php -f /usr/share/mfscgi/csvapi.php action=%s period=%s" % (action, period)


proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
script_response = proc.stdout.read()

print script_response
print script_response

exit()

