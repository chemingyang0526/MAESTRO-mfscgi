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

PROTO_BASE = 0

CLTOMA_CSERV_LIST = (PROTO_BASE+500)
MATOCL_CSERV_LIST = (PROTO_BASE+501)
CLTOCS_HDD_LIST_V1 = (PROTO_BASE+502)
CSTOCL_HDD_LIST_V1 = (PROTO_BASE+503)
CLTOMA_SESSION_LIST = (PROTO_BASE+508)
MATOCL_SESSION_LIST = (PROTO_BASE+509)
CLTOMA_INFO = (PROTO_BASE+510)
MATOCL_INFO = (PROTO_BASE+511)
CLTOMA_FSTEST_INFO = (PROTO_BASE+512)
MATOCL_FSTEST_INFO = (PROTO_BASE+513)
CLTOMA_CHUNKSTEST_INFO = (PROTO_BASE+514)
MATOCL_CHUNKSTEST_INFO = (PROTO_BASE+515)
CLTOMA_CHUNKS_MATRIX = (PROTO_BASE+516)
MATOCL_CHUNKS_MATRIX = (PROTO_BASE+517)
CLTOMA_EXPORTS_INFO = (PROTO_BASE+520)
MATOCL_EXPORTS_INFO = (PROTO_BASE+521)
CLTOMA_MLOG_LIST = (PROTO_BASE+522)
MATOCL_MLOG_LIST = (PROTO_BASE+523)
CLTOMA_CSSERV_REMOVESERV = (PROTO_BASE+524)
MATOCL_CSSERV_REMOVESERV = (PROTO_BASE+525)
CLTOCS_HDD_LIST_V2 = (PROTO_BASE+600)
CSTOCL_HDD_LIST_V2 = (PROTO_BASE+601)
LIZ_CLTOMA_CHUNKS_HEALTH = 1526
LIZ_MATOCL_CHUNKS_HEALTH = 1527
LIZ_CLTOMA_LIST_GOALS = 1547
LIZ_MATOCL_LIST_GOALS = 1548
LIZ_CLTOMA_CSERV_LIST = 1549
LIZ_MATOCL_CSERV_LIST = 1550
LIZ_CLTOMA_METADATASERVERS_LIST = 1522
LIZ_MATOCL_METADATASERVERS_LIST = 1523
LIZ_CLTOMA_METADATASERVER_STATUS = 1545
LIZ_MATOCL_METADATASERVER_STATUS = 1546
LIZ_CLTOMA_HOSTNAME = 1551
LIZ_MATOCL_HOSTNAME = 1552

LIZARDFS_VERSION_WITH_QUOTAS = (2, 5, 0)
LIZARDFS_VERSION_WITH_CUSTOM_GOALS = (2, 5, 3)
LIZARDFS_VERSION_WITH_LIST_OF_SHADOWS = (2, 5, 5)

cgitb.enable()

fields = cgi.FieldStorage()

try:
	if fields.has_key("masterhost"):
		masterhost = fields.getvalue("masterhost")
	else:
		masterhost = '127.0.0.1'
except Exception:
	masterhost = '127.0.0.1'
try:
	masterport = int(fields.getvalue("masterport"))
except Exception:
	masterport = 9421
try:
	if fields.has_key("mastername"):
		mastername = fields.getvalue("mastername")
	else:
		mastername = 'LizardFS'
except Exception:
	mastername = 'LizardFS'

thsep = ''
html_thsep = ''
CHARTS_CSV_CHARTID_BASE = 90000

############################
# Deserialization framework

# Elements used to build tree which describes a structure of data to deserialize.
# Examples of such trees:
# String + Primitive("Q") -- a pair: string and uint64_t
# List(String) -- a list of strings
# List(List(String)) -- a list of lists of strings
# List(3 * String) -- a list of tuples (string, string, string)
# Tuple("LQBB") -- a tuple consising of uint32_t, uint64_t, uint8_t, uint8_t
# List(Tuple(3 * "L")) -- a list of 3-tuples of uint32_t
# List(Tuple("LLL") + String) -- a list of (3-tuple of uint32_t, string)
# Dict(Primitive("Q", List(String)) -- a dict uint64_t -> list of strings
def Primitive(format):
	return ("primitive", format)
def Tuple(format):
	return ("tuple", format)
String = ("string",)
def List(element_tree):
	return ("list", element_tree)
def Dict(key_tree, value_tree):
	return ("dict", key_tree, value_tree)

def deserialize(buffer, tree, return_tuple=False):
	""" Deserialize (and remove) data from a buffer described by a tree
	buffer - a bytearray with serialized data
	tree   - a structure of the data built using nodes like 'List', 'Primitive', ...
	return_tuple - if True, returns tuple (even 1-tuple) instead of a value
	"""
	head_len = 2 # Number of elements in a tree to be removed after deserializing first entry
	if tree[0] == "primitive":
		head = deserialize_primitive(buffer, tree[1])
	elif tree[0] == "tuple":
		head = deserialize_tuple(buffer, tree[1])
	elif tree[0] == "string":
		head = deserialize_string(buffer)
		head_len = 1
	elif tree[0] == "list":
		head = deserialize_list(buffer, tree[1])
	elif tree[0] == "dict":
		head = deserialize_dict(buffer, tree[1], tree[2])
		head_len = 3
	else:
		raise RuntimeError, "Unknown tree to deserialize: {0}".format(tree)
	if (len(tree) > head_len):
		tail = deserialize(buffer, tree[head_len:], True)
		return (head,) + tail
	else:
		return (head,) if return_tuple else head

# Deserialization functions for tree nodes

def deserialize_primitive(buffer, format):
	""" Deserialize a single value described in format string and remove it from buffer """
	ret, = deserialize_tuple(buffer, format)
	return ret

def deserialize_tuple(bytebuffer, format):
	""" Deserialize a tuple described in format string and remove it from buffer """
	size = struct.calcsize(">" + format)
	ret = struct.unpack_from(">" + format, buffer(bytebuffer))
	del bytebuffer[0:size]
	return ret

def deserialize_string(buffer):
	""" Deserialize a std::string and remove it from buffer """
	length = deserialize_primitive(buffer, "L")
	if len(buffer) < length or buffer[length - 1] != 0:
		raise RuntimeError, "malformed message; cannot deserialize"
	ret = str(buffer[0:length-1])
	del buffer[0:length]
	return ret

def deserialize_list(buffer, element_tree):
	""" Deserialize a list of elements and remove it from buffer """
	length = deserialize_primitive(buffer, "L")
	return [deserialize(buffer, element_tree) for i in xrange(length)]

def deserialize_dict(buffer, key_tree, value_tree):
	""" Deserialize a dict and remove it from buffer """
	length = deserialize_primitive(buffer, "L")
	ret = {}
	for i in xrange(length):
		key = deserialize(buffer, key_tree)
		val = deserialize(buffer, value_tree)
		ret[key] = val
	return ret

##########################
# Serialization framework

def make_liz_message(type, version, data):
	""" Adds a proper header to message data """
	return struct.pack(">LLL", type, len(data) + 4, version) + data

#####################################
# Implementation of network messages

def cltoma_list_goals():
	if masterversion < LIZARDFS_VERSION_WITH_CUSTOM_GOALS:
		# For old servers just return the default 10 goals
		return [(i, str(i), str(i) + "*_") for i in xrange(1, 10)]
	else:
		# For new servers, use LIZ_CLTOMA_LIST_GOALS to fetch the list of goal definitions
		request = make_liz_message(LIZ_CLTOMA_LIST_GOALS, 0, "\1")
		response = send_and_receive(masterhost, masterport, request, LIZ_MATOCL_LIST_GOALS, 0)
		goals = deserialize(response, List(Primitive("H") + 2 * String))
		if response:
			raise RuntimeError, "malformed LIZ_MATOCL_LIST_GOALS response (too long by {0} bytes)".format(len(response))
		return goals

def cltoma_chunks_health(only_regular):
	goals = cltoma_list_goals()
	request = make_liz_message(LIZ_CLTOMA_CHUNKS_HEALTH, 0, struct.pack(">B", only_regular))
	response = send_and_receive(masterhost, masterport, request, LIZ_MATOCL_CHUNKS_HEALTH, 0)
	regular_only = deserialize(response, Primitive("B"))
	safe, endangered, lost = deserialize(response, 3 * Dict(Primitive("B"), Primitive("Q")))
	raw_replication, raw_deletion = deserialize(response, 2 * Dict(Primitive("B"), Tuple(11 * "Q")))
	if response:
		raise RuntimeError, "malformed LIZ_MATOCL_CHUNKS_HEALTH response (too long by {0} bytes)".format(len(response))
	availability, replication, deletion = [], [], []
	for (id, name, _) in goals:
		availability.append((name, safe.setdefault(id, 0), endangered.setdefault(id, 0), lost.setdefault(id, 0)))
		replication.append((name,) + raw_replication.setdefault(id, 11 * (0,)))
		deletion.append((name,) + raw_deletion.setdefault(id, 11 * (0,)))
	return (availability, replication, deletion)

def cltoma_hostname(host, port):
	request = make_liz_message(LIZ_CLTOMA_HOSTNAME, 0, "")
	response = send_and_receive(host, port, request, LIZ_MATOCL_HOSTNAME, 0)
	return deserialize(response, String)

def cltoma_metadataserver_status(host, port):
	LIZ_METADATASERVER_STATUS_MASTER = 1
	LIZ_METADATASERVER_STATUS_SHADOW_CONNECTED = 2
	LIZ_METADATASERVER_STATUS_SHADOW_DISCONNECTED = 3
	request = make_liz_message(LIZ_CLTOMA_METADATASERVER_STATUS, 0, struct.pack(">L", 0))
	response = send_and_receive(host, port, request, LIZ_MATOCL_METADATASERVER_STATUS, 0)
	_, status, metadata_version = deserialize(response, Tuple("LBQ"))
	if status == LIZ_METADATASERVER_STATUS_MASTER:
		return ("master", "running", metadata_version)
	elif status == LIZ_METADATASERVER_STATUS_SHADOW_CONNECTED:
		return ("shadow", "connected", metadata_version)
	elif status == LIZ_METADATASERVER_STATUS_SHADOW_DISCONNECTED:
		return ("shadow", "disconnected", metadata_version)
	else:
		return ("(unknown)", "(unknown)", metadata_version)

def cltoma_metadataservers_list():
	request = make_liz_message(LIZ_CLTOMA_METADATASERVERS_LIST, 0, "")
	response = send_and_receive(masterhost, masterport, request, LIZ_MATOCL_METADATASERVERS_LIST, 0)
	_, shadows = deserialize(response, Primitive("L") + List(Tuple("LHHBB")))
	servers = [(masterhost, masterport) + masterversion] + shadows
	ret = []
	for (addr, port, v1, v2, v3) in servers:
		# for shadow masters, addr is int (4 bytes) -- convert it to string.
		# for the active master we use "masterhost" to connect with it and we don't know the real IP
		ip = addr_to_host(addr) if isinstance(addr, (int, long)) else "-"
		version = "%u.%u.%u" % (v1, v2, v3)
		if port == 0:
			# shadow didn't register its port yet
			personality = "shadow"
			host, state, metadata = 3 * ("(unknown)",)
		else:
			# master or a fully registered shadow
			try:
				host = cltoma_hostname(addr, port)
				personality, state, metadata = cltoma_metadataserver_status(addr, port)
			except:
				personality, host, state, metadata = 4 * ("(error)",)

		ret.append((host, ip, port, personality, '<div class="statusstater">'+state+'</div>'))
	return ret

###############
# Other things

def make_table_row(cell_begin, cell_end, cell_contents):
	""" Returns a string representation of a html table row
	cell_begin - tag which opens each cell
	cell_end   - tag which ends each cell
	cell_contents - collection of values for the row
	"""
	return "	<tr>" + "".join([cell_begin + str(i) + cell_end for i in cell_contents]) + "</tr>"

def htmlentities(str):
	return str.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;').replace("'",'&apos;').replace('"','&quot;')

def urlescape(str):
	return urllib.quote_plus(str)

def mysend(socket,msg):
	totalsent = 0
	while totalsent < len(msg):
		sent = socket.send(msg[totalsent:])
		if sent == 0:
			raise RuntimeError, "socket connection broken"
		totalsent = totalsent + sent

def myrecv(socket,leng):
	msg = ''
	while len(msg) < leng:
		chunk = socket.recv(leng-len(msg))
		if chunk == '':
			raise RuntimeError, "socket connection broken"
		msg = msg + chunk
	return msg

def addr_to_host(addr):
	""" Convert IP address ('xxx.xxx.xxx.xxx' or 'hostname' or a 4-byte integer) to string """
	if isinstance(addr, (int, long)):
		return socket.inet_ntoa(struct.pack(">L", addr))
	elif isinstance(addr, str):
		return addr
	else:
		raise RuntimeError, "unknown format of server address"


def send_and_receive(host, port, request, response_type, response_version = None):
	""" Sends a request, receives response and verifies its type and (if provided) version """
	s = socket.socket()
	s.connect((addr_to_host(host), port))
	try:
		mysend(s, request)
		header = myrecv(s, 8)
		cmd, length = struct.unpack(">LL", header)
		if cmd != response_type:
			raise RuntimeError, "received wrong response (%x instead of %x)" % (cmd, response_type)
		data = bytearray(myrecv(s, length))
	except:
		s.close()
		raise
	s.close()
	if response_version is not None:
		version = deserialize_primitive(data, "L")
		if version != response_version:
			raise RuntimeError, "received wrong response version (%u instead of %u)" % (version, response_version)
	return data

def decimal_number(number,sep=' '):
	parts = []
	while number>=1000:
		number,rest = divmod(number,1000)
		parts.append("%03u" % rest)
	parts.append(str(number))
	parts.reverse()
	return sep.join(parts)

def humanize_number(number,sep=''):
	number*=100
	scale=0
	while number>=99950:
		number = number//1024
		scale+=1
	if number<995 and scale>0:
		b = (number+5)//10
		nstr = "%u.%u" % divmod(b,10)
	else:
		b = (number+50)//100
		nstr = "%u" % b
	if scale>0:
		return "%s%s%si" % (nstr,sep,"-KMGTPEZY"[scale])
	else:
		return "%s%s" % (nstr,sep)

def timeduration_to_shortstr(timeduration):
	for l,s in ((86400,'d'),(3600,'h'),(60,'m'),(1,'s')):
		if timeduration>=l:
			n = float(timeduration)/float(l)
			rn = round(n,1)
			if n==round(n,0):
				return "%.0f%s" % (n,s)
			else:
				return "%s%.1f%s" % (("~" if n!=rn else ""),rn,s)
	return "0s"

def timeduration_to_fullstr(timeduration):
	if timeduration>=86400:
		days,dayseconds = divmod(timeduration,86400)
		daysstr = "%u day%s, " % (days,("s" if days!=1 else ""))
	else:
		dayseconds = timeduration
		daysstr = ""
	hours,hourseconds = divmod(dayseconds,3600)
	minutes,seconds = divmod(hourseconds,60)
	return "%u second%s (%s%u:%02u:%02u)" % (timeduration,("" if timeduration==1 else "s"),daysstr,hours,minutes,seconds)

# check version
masterversion = (0,0,0)
try:
	s = socket.socket()
	s.connect((masterhost,masterport))
	mysend(s,struct.pack(">LL",CLTOMA_INFO,0))
	header = myrecv(s,8)
	cmd,length = struct.unpack(">LL",header)
	data = myrecv(s,length)
	if cmd==MATOCL_INFO:
		if length==52:
			masterversion = (1,4,0)
		elif length==60:
			masterversion = (1,5,0)
		elif length==68 or length==76:
			masterversion = struct.unpack(">HBB",data[:4])
except Exception:
	print "Content-Type: text/html; charset=UTF-8"
	print
	print """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">"""
	print """<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">"""
	print """<head>"""
	print """<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />"""
	print """<title>LizardFS Info (%s)</title>""" % (htmlentities(mastername))
	print """<link href="favicon.ico" rel="icon" type="image/x-icon" />"""
	print """<link rel="stylesheet" href="mfs.css" type="text/css" />"""
	print """</head>"""
	print """<body>"""
	print """<h1 align="center">Can't connect to LizardFS master (IP:%s ; PORT:%u)</h1>""" % (htmlentities(masterhost),masterport)
	print """</body>"""
	print """</html>"""
	exit()

if masterversion==(0,0,0):
	print "Content-Type: text/html; charset=UTF-8"
	print
	print """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">"""
	print """<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">"""
	print """<head>"""
	print """<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />"""
	print """<title>LizardFS Info (%s)</title>""" % (htmlentities(mastername))
	print """<link href="favicon.ico" rel="icon" type="image/x-icon" />"""
	print """<link rel="stylesheet" href="mfs.css" type="text/css" />"""
	print """</head>"""
	print """<body>"""
	print """<h1 align="center">Can't detect LizardFS master version</h1>"""
	print """</body>"""
	print """</html>"""
	exit()


def createlink(update):
	c = []
	for k in fields:
		if k not in update:
			c.append("%s=%s" % (k,urlescape(fields.getvalue(k))))
	for k,v in update.iteritems():
		if v!="":
			c.append("%s=%s" % (k,urlescape(v)))
	return "mfs.cgi?%s" % ("&amp;".join(c))

def createorderlink(prefix,columnid):
	ordername = "%sorder" % prefix
	revname = "%srev" % prefix
	try:
		orderval = int(fields.getvalue(ordername))
	except Exception:
		orderval = 0
	try:
		revval = int(fields.getvalue(revname))
	except Exception:
		revval = 0
	return createlink({revname:"1"}) if orderval==columnid and revval==0 else createlink({ordername:str(columnid),revname:"0"})

# commands
if fields.has_key("CSremove"):
	cmd_success = 0
	tracedata = ""
	try:
		serverdata = fields.getvalue("CSremove").split(":")
		if len(serverdata)==2:
			csip = map(int,serverdata[0].split("."))
			csport = int(serverdata[1])
			if len(csip)==4:
				s = socket.socket()
				s.connect((masterhost,masterport))
				mysend(s,struct.pack(">LLBBBBH",CLTOMA_CSSERV_REMOVESERV,6,csip[0],csip[1],csip[2],csip[3],csport))
				header = myrecv(s,8)
				cmd,length = struct.unpack(">LL",header)
				if cmd==MATOCL_CSSERV_REMOVESERV and length==0:
					cmd_success = 1
	except Exception:
		tracedata = traceback.format_exc()
	url = createlink({"CSremove":""})
	if cmd_success:
		print "Status: 302 Found"
		print "Location: %s" % url.replace("&amp;","&")
		print "Content-Type: text/html; charset=UTF-8"
		print
		print """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">"""
		print """<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">"""
		print """<head>"""
		print """<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />"""
		print """<meta http-equiv="Refresh" content="0; url=%s" />""" % url
		print """<title>LizardFS Info (%s)</title>""" % (htmlentities(mastername))
		print """<link href="favicon.ico" rel="icon" type="image/x-icon" />"""
		print """<link rel="stylesheet" href="mfs.css" type="text/css" />"""
		print """</head>"""
		print """<body>"""
		print """<h1 align="center"><a href="%s">If you see this then it means that redirection didn't work, so click here</a></h1>"""
		print """</body>"""
		print """</html>"""
	else:
		print "Content-Type: text/html; charset=UTF-8"
		print
		print """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">"""
		print """<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">"""
		print """<head>"""
		print """<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />"""
		print """<meta http-equiv="Refresh" content="5; url=%s" />""" % url
		print """<title>LizardFS Info (%s)</title>""" % (htmlentities(mastername))
		print """<link href="favicon.ico" rel="icon" type="image/x-icon" />"""
		print """<link rel="stylesheet" href="mfs.css" type="text/css" />"""
		print """</head>"""
		print """<body>"""
		print """<h3 align="center">Can't remove server (%s) from list - wait 5 seconds for refresh</h3>""" % fields.getvalue("CSremove")
		if tracedata:
			print """<hr />"""
			print """<pre>%s</pre>""" % tracedata
		print """</body>"""
		print """</html>"""
	exit()

if fields.has_key("sections"):
	sectionstr = fields.getvalue("sections")
	sectionset = set(sectionstr.split("|"))
else:
	sectionset = set(("IN",))

if masterversion<(1,5,14):
	sectiondef={
		"IN":"Dashboard",
		"CS":"Files",
		"HD":"Hard Disks",
		"ML":"Mount List",
		"MC":"Master Charts",
		"CC":"Chunk Servers Charts",
		"HELP":"Help"
	}
	sectionorder=["IN","CS","HD","ML","MC","CC","HELP"];
elif masterversion<LIZARDFS_VERSION_WITH_CUSTOM_GOALS:
	sectiondef={
		"IN":"Dashboard",
		"CS":"Servers",
		"HD":"vDisks",
		"EX":"Config",
		"MS":"Mounts",
		"MO":"Operations",
		"MC":"Master",
		"CC":"Client",
		"HELP":"Help"
	}
	sectionorder=["IN","CS","HD","EX","MS","MO","MC","CC","HELP"];
else:
	sectiondef={
		"IN":"Dashboard",
		"CH":"Files",
		"CS":"Servers",
		"HD":"vDisks",
		"EX":"Config",
		"MS":"Mounts",
		"MO":"Operations",
		"MC":"Master",
		"CC":"Client",
		"HELP":"Help"
	}
	sectionorder=["IN","CH","CS","HD","EX","MS","MO","MC","CC","HELP"];


print "Content-Type: text/html; charset=UTF-8"
print
# print """<!-- Put IE into quirks mode -->
print """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">"""
print """<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">"""
print """<head>"""
print """<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />"""
print """<title>LizardFS Info (%s)</title>""" % (htmlentities(mastername))
print """<link href="favicon.ico" rel="icon" type="image/x-icon" />"""
print """<link rel="stylesheet" href="mfs.css" type="text/css" />"""
print """<link href="http://fonts.googleapis.com/css?family=Open+Sans:300,400,600,700&amp;subset=latin" rel="stylesheet">"""
print """<link href="css/bootstrap.min.css" rel="stylesheet">"""
print """<link href="css/nifty.css" rel="stylesheet">"""
print """<link href="css/fontawesome/css/font-awesome.css" rel="stylesheet">"""
print """<script src="js/jquery-2.1.4.min.js"></script>"""
print """<script src="js/morris-js/morris.min.js"></script>"""
print """<script src="js/morris-js/raphael-js/raphael.min.js"></script>"""
print """<script src="js/easy-pie-chart/jquery.easypiechart.min.js"></script>"""
print """<script src="js/PapaParse-4.1.2/papaparse.js"></script>"""
print """</head>"""
print """<body>"""

#MENUBAR
print """<div class="panel panel-primary">
					
								<!--Panel heading-->
								<div class="panel-heading movepanel">
									<div class="panel-control">
					<ul class="nav nav-tabs MENUZ">"""

last="U"
for k in sectionorder:
	if k==sectionorder[-1]:
		last = "L%s" % last
	if k in sectionset:
		if len(sectionset)<=1:
			print """<li class="%sS">%s</td>""" % (last,sectiondef[k])
		else:
			print """<li class="%sS"><a href="%s">%s</a> <a href="%s" style="display:none;">&#8722;</a></li>""" % (last,createlink({"sections":k}),sectiondef[k],createlink({"sections":"|".join(sectionset-set([k]))}))
		last="S"
	else:
		print """<li class="%sU"><a href="%s">%s</a> <a href="%s" style="display:none;">+</a></li>""" % (last,createlink({"sections":k}),sectiondef[k],createlink({"sections":"|".join(sectionset|set([k]))}))
		last="U"
print """</li>"""
print """</ul></div>
									
								</div>
					
								
							</div>"""
print """<td class="FILLER" style="white-space:nowrap;">"""
print """</td>"""
print """</tr>"""
print """</table>"""
print """</div>"""

#print """<div id="footer">
#Moose File System by Jakub Kruszona-Zawadzki
#</div>
#"""

print """<div id="container">"""

if "IN" in sectionset:
	try:
		INmatrix = int(fields.getvalue("INmatrix"))
	except Exception:
		INmatrix = 0
	try:
		out = []
		s = socket.socket()
		s.connect((masterhost,masterport))
		mysend(s,struct.pack(">LL",CLTOMA_INFO,0))
		header = myrecv(s,8)
		cmd,length = struct.unpack(">LL",header)
		if cmd==MATOCL_INFO and length==52:
			data = myrecv(s,length)
			total,avail,trspace,trfiles,respace,refiles,nodes,chunks,tdcopies = struct.unpack(">QQQLQLLLL",data)
			out.append("""<table class="FRA table table-bordered table-hover toggle-circle tablet breakpoint footable-loaded footable" cellspacing="0" summary="Info table">""")
			out.append("""	<tr class="info"><th colspan="9">Info</th></tr>""")
			out.append("""	<tr class="info">""")
			out.append("""		<th>total space</th>""")
			out.append("""		<th>avail space</th>""")
			out.append("""		<th>trash space</th>""")
			out.append("""		<th>trash files</th>""")
			out.append("""		<th>reserved space</th>""")
			out.append("""		<th>reserved files</th>""")
			out.append("""		<th>all fs objects</th>""")
			out.append("""		<th>chunks</th>""")
			out.append("""		<th>copies to delete</th>""")
			out.append("""	</tr>""")
			out.append("""	<tr class="info">""")
			out.append("""		<td align="right"><a style="cursor:default" title="%s B">%sB</a></td>""" % (decimal_number(total),humanize_number(total,"&nbsp;")))
			out.append("""		<td align="right"><a style="cursor:default" title="%s B">%sB</a></td>""" % (decimal_number(avail),humanize_number(avail,"&nbsp;")))
			out.append("""		<td align="right"><a style="cursor:default" title="%s B">%sB</a></td>""" % (decimal_number(trspace),humanize_number(trspace,"&nbsp;")))
			out.append("""		<td align="right">%u</td>""" % trfiles)
			out.append("""		<td align="right"><a style="cursor:default" title="%s B">%sB</a></td>""" % (decimal_number(respace),humanize_number(respace,"&nbsp;")))
			out.append("""		<td align="right">%u</td>""" % refiles)
			out.append("""		<td align="right">%u</td>""" % nodes)
			out.append("""		<td align="right">%u</td>""" % chunks)
			out.append("""		<td align="right">%u</td>""" % tdcopies)
			out.append("""	</tr>""")
			out.append("""</table>""")
		elif cmd==MATOCL_INFO and length==60:
			data = myrecv(s,length)
			total,avail,trspace,trfiles,respace,refiles,nodes,dirs,files,chunks,tdcopies = struct.unpack(">QQQLQLLLLLL",data)
			out.append("""<table class="FRA table table-bordered table-hover toggle-circle tablet breakpoint footable-loaded footable" cellspacing="0" summary="Info table">""")
			out.append("""	<tr class="info"><th colspan="11">Info</th></tr>""")
			out.append("""	<tr class="info">""")
			out.append("""		<th>total space</th>""")
			out.append("""		<th>avail space</th>""")
			out.append("""		<th>trash space</th>""")
			out.append("""		<th>trash files</th>""")
			out.append("""		<th>reserved space</th>""")
			out.append("""		<th>reserved files</th>""")
			out.append("""		<th>all fs objects</th>""")
			out.append("""		<th>directories</th>""")
			out.append("""		<th>files</th>""")
			out.append("""		<th>chunks</th>""")
			out.append("""		<th>copies to delete</th>""")
			out.append("""	</tr>""")
			out.append("""	<tr>""")
			out.append("""		<td align="right"><a style="cursor:default" title="%s B">%sB</a></td>""" % (decimal_number(total),humanize_number(total,"&nbsp;")))
			out.append("""		<td align="right"><a style="cursor:default" title="%s B">%sB</a></td>""" % (decimal_number(avail),humanize_number(avail,"&nbsp;")))
			out.append("""		<td align="right"><a style="cursor:default" title="%s B">%sB</a></td>""" % (decimal_number(trspace),humanize_number(trspace,"&nbsp;")))
			out.append("""		<td align="right">%u</td>""" % trfiles)
			out.append("""		<td align="right"><a style="cursor:default" title="%s B">%sB</a></td>""" % (decimal_number(respace),humanize_number(respace,"&nbsp;")))
			out.append("""		<td align="right">%u</td>""" % refiles)
			out.append("""		<td align="right">%u</td>""" % nodes)
			out.append("""		<td align="right">%u</td>""" % dirs)
			out.append("""		<td align="right">%u</td>""" % files)
			out.append("""		<td align="right">%u</td>""" % chunks)
			out.append("""		<td align="right">%u</td>""" % tdcopies)
			out.append("""	</tr>""")
			out.append("""</table>""")
		elif cmd==MATOCL_INFO and length==68:
			data = myrecv(s,length)
			v1,v2,v3,total,avail,trspace,trfiles,respace,refiles,nodes,dirs,files,chunks,allcopies,tdcopies = struct.unpack(">HBBQQQLQLLLLLLL",data)
			out.append("""<table class="FRA table table-bordered table-hover toggle-circle tablet breakpoint footable-loaded footable" cellspacing="0" summary="Info table">""")
			out.append("""	<tr class="info"><th colspan="13">Info</th></tr>""")
			out.append("""	<tr class="info">""")
			out.append("""		<th>version</th>""")
			out.append("""		<th>total space</th>""")
			out.append("""		<th>avail space</th>""")
			out.append("""		<th>trash space</th>""")
			out.append("""		<th>trash files</th>""")
			out.append("""		<th>reserved space</th>""")
			out.append("""		<th>reserved files</th>""")
			out.append("""		<th>all fs objects</th>""")
			out.append("""		<th>directories</th>""")
			out.append("""		<th>files</th>""")
			out.append("""		<th>chunks</th>""")
			if masterversion>=(1,6,10):
				out.append("""		<th><a style="cursor:default" title="chunks from 'regular' hdd space and 'marked for removal' hdd space">all chunk copies</a></th>""")
				out.append("""		<th><a style="cursor:default" title="only chunks from 'regular' hdd space">regular chunk copies</a></th>""")
			else:
				out.append("""		<th>chunk copies</th>""")
				out.append("""		<th>copies to delete</th>""")
			out.append("""	</tr>""")
			out.append("""	<tr>""")
			out.append("""		<td align="center">%u.%u.%u</td>""" % (v1,v2,v3))
			out.append("""		<td align="right"><a style="cursor:default" title="%s B">%sB</a></td>""" % (decimal_number(total),humanize_number(total,"&nbsp;")))
			out.append("""		<td align="right"><a style="cursor:default" title="%s B">%sB</a></td>""" % (decimal_number(avail),humanize_number(avail,"&nbsp;")))
			out.append("""		<td align="right"><a style="cursor:default" title="%s B">%sB</a></td>""" % (decimal_number(trspace),humanize_number(trspace,"&nbsp;")))
			out.append("""		<td align="right">%u</td>""" % trfiles)
			out.append("""		<td align="right"><a style="cursor:default" title="%s B">%sB</a></td>""" % (decimal_number(respace),humanize_number(respace,"&nbsp;")))
			out.append("""		<td align="right">%u</td>""" % refiles)
			out.append("""		<td align="right">%u</td>""" % nodes)
			out.append("""		<td align="right">%u</td>""" % dirs)
			out.append("""		<td align="right">%u</td>""" % files)
			out.append("""		<td align="right">%u</td>""" % chunks)
			out.append("""		<td align="right">%u</td>""" % allcopies)
			out.append("""		<td align="right">%u</td>""" % tdcopies)
			out.append("""	</tr>""")
			out.append("""</table>""")
		elif cmd==MATOCL_INFO and length==76:
			v1,v2,v3,memusage,total,avail,trspace,trfiles,respace,refiles,nodes,dirs,files,chunks,allcopies,tdcopies = struct.unpack(">HBBQQQQLQLLLLLLL",data)
			data = myrecv(s,length)
			
			out.append("""<div id="maindash" class="row">""")
			out.append("""<div class="col-xs-3 col-sm-3 col-md-3 col-lg-3">""")
			out.append("""<span class="textoo text-thin">Storage<span id="valuz"></span>:</span><br/><div id="ramspace"></div>""")
			out.append("""</div>""")
			out.append("""<div class="col-xs-3 col-sm-3 col-md-3 col-lg-3">""")
			out.append("""<span class="textoo text-thin">Memory<span id="valuze"></span>:</span><div id="storagespace"></div>""")
			out.append("""		<td align="right"><a style="cursor:default" id="totalspacehddo" title="%s B">%sB</a></td>""" % (decimal_number(total),humanize_number(total,"&nbsp;")))
			out.append("""		<td align="right"><a style="cursor:default" id="availspacehddo" title="%s B">%sB</a></td>""" % (decimal_number(avail),humanize_number(avail,"&nbsp;")))
			out.append("""		<td align="right"><a style="cursor:default" id="memusage" title="%s B">%sB</a></td>""" % (decimal_number(memusage),humanize_number(memusage,"&nbsp;")))
			
			
			df = subprocess.Popen("free -m | grep 'Mem' | awk '//{ print $2 }'", shell = True, stdout = subprocess.PIPE) 
			res = df.communicate()[0]

			out.append(""" <div id="memtotal">%s</div>""" % res)
			

			
			out.append("""</div>""")
			out.append("""<div class="col-xs-3 col-sm-3 col-md-3 col-lg-3"> """)
			out.append("""<div class="row">""")
			out.append("""<div class="col-xs-12 col-sm-12 col-md-12 col-lg-12"><div class="panel media pad-all openo"><div class="media-body"><p class="text-2x mar-no text-thin"><span class="icon-wrap icon-wrap-sm icon-circle bg-success"><i class="fa fa-hdd-o"></i></span><span class="texto">Trash space:</span><br/><span class="smallval">""")
			out.append("""		<td align="right"><a style="cursor:default" title="%s B">%sB</a></td>""" % (decimal_number(trspace),humanize_number(trspace,"&nbsp;")))
			out.append("""</span></p></div></div>""")
			out.append("""</div>""")
			
			out.append("""<div class="col-xs-12 col-sm-12 col-md-12 col-lg-12"><div class="panel media pad-all openo openo33"><div class="media-body"><p class="text-2x mar-no text-thin"><span class="icon-wrap icon-wrap-sm icon-circle bg-success"><i class="fa fa-files-o"></i></span><span class="texto">Trash files:</span><br/><span class="smallval">""")
			out.append("""		<td align="right">%u</td>""" % trfiles)
			out.append("""</span></p></div></div>""")
			out.append("""</div>""")
			out.append("""</div>""")
			out.append("""</div>""")
			
			
			out.append("""<div class="col-xs-3 col-sm-3 col-md-3 col-lg-3"> """)
			out.append("""<div class="row">""")
			out.append("""<div class="col-xs-12 col-sm-12 col-md-12 col-lg-12"><div class="panel media pad-all openo "><div class="media-body"><p class="text-2x mar-no text-thin"><span class="icon-wrap icon-wrap-sm icon-circle bg-success"><i class="fa fa-hdd-o"></i></span><span class="texto">Reserved space:</span><br/><span class="smallval">""")
			out.append("""		<td align="right"><a style="cursor:default" title="%s B">%sB</a></td>""" % (decimal_number(respace),humanize_number(respace,"&nbsp;")))
			out.append("""</span></p></div></div>""")
			out.append("""</div>""")
			
			out.append("""<div class="col-xs-12 col-sm-12 col-md-12 col-lg-12"><div class="panel media pad-all openo openo33"><div class="media-body"><p class="text-2x mar-no text-thin"><span class="icon-wrap icon-wrap-sm icon-circle bg-success"><i class="fa fa-files-o"></i></span><span class="texto">Reserved files:</span><br/><span class="smallval">""")
			out.append("""		<td align="right">%u</td>""" % refiles)
			out.append("""</span></p></div></div>""")
			out.append("""</div>""")

			out.append("""</div>""")
			out.append("""</div>""")
			
		else:
			out.append("""<table class="FRA table table-bordered table-hover toggle-circle tablet breakpoint footable-loaded footable" cellspacing="0">""")
			out.append("""	<tr><td align="left">unrecognized answer from LizardFS master</td></tr>""")
			out.append("""</table>""")
		s.close()
		print "\n".join(out)
	except Exception:
		print """<table class="FRA table table-bordered table-hover toggle-circle tablet breakpoint footable-loaded footable" cellspacing="0" summary="Exception">"""
		print """<tr><td align="left"><pre>"""
		traceback.print_exc(file=sys.stdout)
		print """</pre></td></tr>"""
		print """</table>"""

	print """<br/>"""

	if masterversion>=(1,5,13):
		try:
			out = []
			s = socket.socket()
			s.connect((masterhost,masterport))
			if masterversion>=(1,6,10):
				mysend(s,struct.pack(">LLB",CLTOMA_CHUNKS_MATRIX,1,INmatrix))
			else:
				mysend(s,struct.pack(">LL",CLTOMA_CHUNKS_MATRIX,0))
			header = myrecv(s,8)
			cmd,length = struct.unpack(">LL",header)
			if cmd==MATOCL_CHUNKS_MATRIX and length==484:
				matrix = []
				for i in xrange(11):
					data = myrecv(s,44)
					matrix.append(list(struct.unpack(">LLLLLLLLLLL",data)))
		
				out.append("""<div class="col-xs-2 col-sm-2 col-md-2 col-lg-2"></div>""")
				out.append("""</div>""")
				out.append("""<div class="col-xs-8 col-sm-8 col-md-8 col-lg-8"></div>""")
				out.append("""<table class="FRA table table-bordered table-hover toggle-circle tablet breakpoint footable-loaded footable" cellspacing="0" summary="Chunks state matrix">""")
				if masterversion>=(1,6,10):
					if INmatrix==0:
						out.append("""	<tr class="info"><th colspan="13">Files State View <span style="display:none">(counts 'regular' hdd space and 'marked for removal' hdd space : <a href="%s" class="VISIBLELINK">switch to 'regular'</a>)</span></th></tr>""" % (createlink({"INmatrix":"1"})))
					else:
						out.append("""	<tr class="info"><th colspan="13">Regular chunks state matrix (counts only 'regular' hdd space : <a href="%s" class="VISIBLELINK">switch to 'all'</a>)</th></tr>""" % (createlink({"INmatrix":"0"})))
				else:
					out.append("""	<tr class="info"><th colspan="13">Chunk state matrix</th></tr>""")
				out.append("""	<tr class="info">""")
				out.append("""		<th rowspan="2" class="PERC4">Requested<br/>Copies</th>""")
				out.append("""		<th colspan="12" class="PERC96">Current Copies </th>""")
				out.append("""	</tr>""")
				out.append("""	<tr class="info">""")
				out.append("""		<th class="PERC8">0</th>""")
				out.append("""		<th class="PERC8">1</th>""")
				out.append("""		<th class="PERC8">2</th>""")
				out.append("""		<th class="PERC8">3</th>""")
				out.append("""		<th class="PERC8">4</th>""")
				out.append("""		<th class="PERC8">5</th>""")
				out.append("""		<th class="PERC8">6</th>""")
				out.append("""		<th class="PERC8">7</th>""")
				out.append("""		<th class="PERC8">8</th>""")
				out.append("""		<th class="PERC8">9</th>""")
				out.append("""		<th class="PERC8">10+</th>""")
				out.append("""		<th class="PERC8">all</th>""")
				out.append("""	</tr>""")
				classsum = 7*[0]
				sumlist = 11*[0]
				for neededCopies in xrange(11):
					out.append("""	<tr>""")
					if neededCopies==10:
						out.append("""		<td align="center">10+</td>""")
					else:
						out.append("""		<td align="center">%u</td>""" % neededCopies)
					for vc in xrange(11):
						if neededCopies==0:
							if vc==0:
								cl = "DELETEREADY"
								clidx = 6
							else:
								cl = "DELETEPENDING"
								clidx = 5
						elif vc==0:
							cl = "MISSING"
							clidx = 0
						elif vc>neededCopies:
							cl = "OVERGOAL"
							clidx = 4
						elif vc<neededCopies:
							if vc==1:
								cl = "ENDANGERED"
								clidx = 1
							else:
								cl = "UNDERGOAL"
								clidx = 2
						else:
							cl = "NORMAL"
							clidx = 3
						if matrix[neededCopies][vc]>0:
							out.append("""		<td align="right"><span class="%s">%u</span></td>""" % (cl,matrix[neededCopies][vc]))
							classsum[clidx]+=matrix[neededCopies][vc]
						else:
							out.append("""		<td align="center">-</td>""")
					if neededCopies==0:
						out.append("""		<td align="right"><span class="IGNORE">%u</span></td>""" % sum(matrix[neededCopies]))
					else:
						out.append("""		<td align="right">%u</td>""" % sum(matrix[neededCopies]))
					out.append("""	</tr>""")
					if neededCopies>0:
						sumlist = [ a + b for (a,b) in zip(sumlist,matrix[neededCopies])]
				out.append("""	<tr>""")
				out.append("""		<td align="center">all 1+</td>""")
				for vc in xrange(11):
					out.append("""		<td align="right">%u</td>""" % sumlist[vc])
				out.append("""		<td align="right">%u</td>""" % sum(sumlist))
				out.append("""	</tr>""")
				out.append("""	<tr><td colspan="13">""" + " / ".join(["""<span class="%sBOX"><!-- --></span>&nbsp;-&nbsp;%s (<span class="%s">%u</span>)""" % (cl,desc,cl,classsum[clidx]) for clidx,cl,desc in [(0,"MISSING","missing"),(1,"ENDANGERED","endangered"),(2,"UNDERGOAL","undergoal"),(3,"NORMAL","Health"),(4,"OVERGOAL","overgoal"),(5,"DELETEPENDING","pending&nbsp;deletion"),(6,"DELETEREADY","ready&nbsp;to&nbsp;be&nbsp;removed")]]) + """</td></tr>""")
				out.append("""</table>""")
				out.append("""</div>""")
				out.append("""<div class="col-xs-2 col-sm-2 col-md-2 col-lg-2"></div>""")
				out.append("""</div>""")
				
			s.close()
			print "\n".join(out)
		except Exception:
			print """<table class="FRA table table-bordered table-hover toggle-circle tablet breakpoint footable-loaded footable" cellspacing="0" summary="Exception">"""
			print """<tr><td align="left"><pre>"""
			traceback.print_exc(file=sys.stdout)
			print """</pre></td></tr>"""
			print """</table>"""

		print """<br/>"""

	try:
		out = []
		s = socket.socket()
		s.connect((masterhost,masterport))
		mysend(s,struct.pack(">LL",CLTOMA_CHUNKSTEST_INFO,0))
		header = myrecv(s,8)
		cmd,length = struct.unpack(">LL",header)
		if cmd==MATOCL_CHUNKSTEST_INFO and length==52:
			data = myrecv(s,length)
			loopstart,loopend,del_invalid,ndel_invalid,del_unused,ndel_unused,del_dclean,ndel_dclean,del_ogoal,ndel_ogoal,rep_ugoal,nrep_ugoal,rebalnce = struct.unpack(">LLLLLLLLLLLLL",data[:52])
			out.append("""<div class="tablejsmove"><table class="FRA fraaz table table-bordered table-hover toggle-circle tablet breakpoint footable-loaded footable" cellspacing="0" summary="Chunk operations info">""")
			out.append("""	<tr class="info"><th colspan="8">Files Operations</th></tr>""")
			out.append("""	<tr class="info">""")
			out.append("""		<th colspan="2">loop time</th>""")
			out.append("""		<th colspan="4">deletions</th>""")
			out.append("""		<th colspan="2">replications</th>""")
			out.append("""	</tr>""")
			out.append("""	<tr>""")
			out.append("""		<th>start</th>""")
			out.append("""		<th>end</th>""")
			out.append("""		<th>invalid</th>""")
			out.append("""		<th>unused</th>""")
			out.append("""		<th>disk clean</th>""")
			out.append("""		<th>over goal</th>""")
			out.append("""		<th>under goal</th>""")
			out.append("""		<th>rebalance</th>""")
			out.append("""	</tr>""")
			if loopstart>0:
				out.append("""	<tr>""")
				out.append("""		<td align="center">%s</td>""" % (time.asctime(time.localtime(loopstart)),))
				out.append("""		<td align="center">%s</td>""" % (time.asctime(time.localtime(loopend)),))
				out.append("""		<td align="right">%u/%u</td>""" % (del_invalid,del_invalid+ndel_invalid))
				out.append("""		<td align="right">%u/%u</td>""" % (del_unused,del_unused+ndel_unused))
				out.append("""		<td align="right">%u/%u</td>""" % (del_dclean,del_dclean+ndel_dclean))
				out.append("""		<td align="right">%u/%u</td>""" % (del_ogoal,del_ogoal+ndel_ogoal))
				out.append("""		<td align="right">%u/%u</td>""" % (rep_ugoal,rep_ugoal+nrep_ugoal))
				out.append("""		<td align="right">%u</td>""" % rebalnce)
				out.append("""	</tr>""")
			else:
				out.append("""	<tr>""")
				out.append("""		<td colspan="8" align="center">no data</td>""")
				out.append("""	</tr>""")
			out.append("""</table></div>""")
		s.close()
		print "\n".join(out)
	except Exception:
		print """<table class="FRA table table-bordered table-hover toggle-circle tablet breakpoint footable-loaded footable" cellspacing="0" summary="Exception">"""
		print """<tr><td align="left"><pre>"""
		traceback.print_exc(file=sys.stdout)
		print """</pre></td></tr>"""
		print """</table>"""

	print """<br/>"""

	try:
		out = []
		s = socket.socket()
		s.connect((masterhost,masterport))
		mysend(s,struct.pack(">LL",CLTOMA_FSTEST_INFO,0))
		header = myrecv(s,8)
		cmd,length = struct.unpack(">LL",header)
		if cmd==MATOCL_FSTEST_INFO and length>=36:
			data = myrecv(s,length)
			loopstart,loopend,files,ugfiles,mfiles,chunks,ugchunks,mchunks,msgbuffleng = struct.unpack(">LLLLLLLLL",data[:36])
			out.append("""<div class="tablejsmove"><table class="FRA fraaz fraaz2 table table-bordered table-hover toggle-circle tablet breakpoint footable-loaded footable" cellspacing="0" summary="Filesystem check info">""")
			out.append("""	<tr class="info"><th colspan="8">Filesystem Statistics</th></tr>""")
			out.append("""	<tr class="info">""")
			out.append("""		<th>Loop start time</th>""")
			out.append("""		<th>Loop end time</th>""")
			out.append("""		<th>files</th>""")
			out.append("""		<th>under-goal files</th>""")
			out.append("""		<th>missing files</th>""")
			out.append("""		<th>Files</th>""")
			out.append("""		<th>under-goal Files</th>""")
			out.append("""		<th>missing Files</th>""")
			out.append("""	</tr>""")
			if loopstart>0:
				out.append("""	<tr>""")
				out.append("""		<td align="center">%s</td>""" % (time.asctime(time.localtime(loopstart)),))
				out.append("""		<td align="center">%s</td>""" % (time.asctime(time.localtime(loopend)),))
				out.append("""		<td align="right">%u</td>""" % files)
				out.append("""		<td align="right">%u</td>""" % ugfiles)
				out.append("""		<td align="right">%u</td>""" % mfiles)
				out.append("""		<td align="right">%u</td>""" % chunks)
				out.append("""		<td align="right">%u</td>""" % ugchunks)
				out.append("""		<td align="right">%u</td>""" % mchunks)
				out.append("""	</tr>""")
				if msgbuffleng>0:
					if msgbuffleng==100000:
						out.append("""	<tr><th colspan="8">Important messages (first 100k):</th></tr>""")
					else:
						out.append("""	<tr><th colspan="8">Important messages:</th></tr>""")
					out.append("""	<tr>""")
					out.append("""		<td colspan="8" align="left"><pre>%s</pre></td>""" % (data[36:].replace("&","&amp;").replace(">","&gt;").replace("<","&lt;")))
					out.append("""	</tr>""")
			else:
				out.append("""	<tr>""")
				out.append("""		<td colspan="8" align="center">no data</td>""")
				out.append("""	</tr>""")
			out.append("""</table><br/><br/><br/><br/><br/><br/><br/></div>""")
		s.close()
		print "\n".join(out)
	except Exception:
		print """<table class="FRA table table-bordered table-hover toggle-circle tablet breakpoint footable-loaded footable" cellspacing="0" summary="Exception">"""
		print """<tr><td align="left"><pre>"""
		traceback.print_exc(file=sys.stdout)
		print """</pre></td></tr>"""
		print """</table>"""

	print """<br/>"""

if "CH" in sectionset:
	try:
		CHregular = int(fields.getvalue("CHregular"))
	except Exception:
		CHregular = 0
	try:
		# Get data for our tables
		availability, replication, deletion = cltoma_chunks_health(CHregular)
		switch = """(counts %s hdd space: <a class="VISIBLELINK" href="%s">switch to '%s'</a>)""" % (
				"only 'regular'" if CHregular == 1 else "'regular' hdd space and 'marked for removal'",
				createlink({"CHregular" : "0" if CHregular == 1 else "1"}),
				"all" if CHregular == 1 else "regular"
		)

		def make_cell(value, css_class=None):
			""" Converts value to a string which should be placed in a cell """
			if value == 0:
				return "-"
			elif css_class is None:
				return str(value)
			else:
				return """<span class="%s">%s</span>""" % (css_class, str(value))

		out = []

		# Chunks availability table
		headers = ["goal", "all chunks", "safe chunks", "endangered chunks", "missing chunks"]
		out.append("""<table class="FRA displaynon table table-bordered table-hover toggle-circle tablet breakpoint footable-loaded footable" cellspacing="0" style="width:650px" summary="Statistics of chunks">""")
		switch = """<a href="mfs.cgi?sections=CH&amp;CHregular=1" class="VISIBLELINK">switch to 'regular'</a>"""
		out.append("""	<tr class="info"><th colspan="5">Files Statistics - %s</th></tr>""" % switch)
		out.append(make_table_row('<th class="PERC20">', '</th>', headers))
		sums = 3 * [0]
		i = 0
		for goal, safe, endangered, lost in filter(lambda row: sum(row[1:]) > 0, availability):
			out.append("""	<tr class="%s">""" % ("C1" if i % 2 == 0 else "C2"))
			i += 1
			out.append(("""		<th class="LEFT">%s</th>""" + 4 * """<td>%s</td>""") %
					(goal,
					make_cell(safe + endangered + lost),
					make_cell(safe, "NORMAL"),
					make_cell(endangered, "ENDANGERED"),
					make_cell(lost, "MISSING"))
			)
			out.append("""	</tr>""")
			sums = map(sum, zip(sums, [safe, endangered, lost])) # add row to the summary
		# Add summary and end the table
		out.append("""	<tr>""")
		out.append(("""		<th>all</th>""" + 4 * """<th class="needvl">%s</th>""") %
				((str(sum(sums)),) + tuple(map(make_cell, sums)))
		)
		out.append("""	</tr>""")
		out.append("""</table>""")


		out.append(("""	<div class="row" id="fileviewtbl">""" + 4 * """<div class="col-xs-3 col-sm-3 col-md-3 col-lg-3 "><div class="panel filetabo media pad-all filepanele">
								<div class="media-left">
									<span class="icon-wrap icon-wrap-sm icon-circle bgcolor">
									<i class="fa fa-2x icof"></i>
									</span>
								</div>
								<div class="media-body">
									<p class="text-2x mar-no text-thin">%s</p>
									<p class="text-muted mar-no textf"></p>
								</div>
							</div></div>""") %
				((str(sum(sums)),) + tuple(map(make_cell, sums)))
		)
		
		out.append("""</div>""")

		out.append("""<div class="panel">
								<div class="panel-heading">
									<h3 class="panel-title">Files for replication</h3>
								</div>
								<div class="panel-body">
					
									<!--Morris Line Chart placeholder-->
									<!-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ -->
									<div id="files-line" style="height:212px">No data for display</div>
									<!-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ -->
					
								</div>
							</div><br/>

			<div class="panel">
								<div class="panel-heading">
									<h3 class="panel-title">Files for deletion</h3>
								</div>
								<div class="panel-body">
					
									<!--Morris Line Chart placeholder-->
									<!-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ -->
									<div id="files-line-del" style="height:212px">No data for display</div>
									<!-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ -->
					
								</div>
							</div>""")
	
		def add_repl_del_state(out, title, table):
			""" Appends a table (replication state or deletion state) to out """
			out.append("""<table style="display: none" class="FRA table table-bordered table-hover toggle-circle tablet breakpoint footable-loaded footable" summary="Chunks which need replication/deletion">""")
			out.append("""	<tr><th colspan="12">Chunks which need %sion %s</th></tr>""" % (title, switch))
			cell_format = """<th class="PERC8">%s<br/>to """ + title + """e</th>"""
			out.append(("""	<tr><th>goal</th>""" + 11 * cell_format + """</tr>""") %
				("0 copies", "1 copy", "2 copies", "3 copies", "4 copies",
				"5 copies", "6 copies", "7 copies", "8 copies", "9 copies", "10+ copies")
			)
			i = 0
			sums = 11 * [0]
			for row in filter(lambda row: sum(row[1:]) > 0, table):
				out.append("""	<tr class="%s">""" % ("C1" if i % 2 == 0 else "C2"))
				i += 1
				out.append(("""		<th class="LEFT">%s</th>""" + 11 * """<td>%s</td>""") %
						((row[0], make_cell(row[1], "NORMAL")) + tuple(map(make_cell, row[2:])))
				)
				out.append("""	</tr>""")
				sums = map(sum, zip(sums, row[1:])) # add row to the summary
			# Add summary and end the table
			out.append("""	<tr>""")
			out.append(("""		<th>all</th>""" + 11 * """<th class="firstfiles">%s</th>""") % tuple(map(make_cell, sums)))
			out.append("""	</tr>""")
			out.append("""</table>""")

		out.append("""<br/>""")
		add_repl_del_state(out, "replicat", replication)
		out.append("""<br/>""")
		add_repl_del_state(out, "delet", deletion)
		print "\n".join(out)
	except Exception:
		print """<table class="FRA table table-bordered table-hover toggle-circle tablet breakpoint footable-loaded footable" cellspacing="0" summary="Exception">"""
		print """<tr><td align="left"><pre>"""
		traceback.print_exc(file=sys.stdout)
		print """</pre></td></tr>"""
		print """</table>"""
	print """<br/>"""

if "CS" in sectionset:
	if masterversion >= LIZARDFS_VERSION_WITH_LIST_OF_SHADOWS:
		out = []
		try:
			SHorder = int(fields.getvalue("SHorder"))
		except Exception:
			SHorder = 1
		try:
			SHrev = bool(int(fields.getvalue("SHrev")))
		except Exception:
			SHrev = False

		try:
			out.append("""<script src="http://%s/htvcenter/base/mfs/jquery-quickedit.js" type="text/javascript"></script>""" % (urlescape(masterhost)))
			out.append("""<script src="http://%s/htvcenter/base/mfs/mfschunkeditor.js" type="text/javascript"></script>""" % (urlescape(masterhost)))
			out.append("""<table class="FRA table table-bordered table-hover toggle-circle tablet breakpoint footable-loaded footable" cellspacing="0" summary="Metadata Servers">""")
			out.append("""	<tr class="info"><th colspan="8">Metadata Servers</th></tr>""")
			out.append("""	<tr class="info">""")
			out.append("""		<th>#</th>""")
			out.append("""		<th><a href="%s">host Name</a></th>""" % (createorderlink("SH", 1)))
			out.append("""		<th><a href="%s">IP</a></th>""" % (createorderlink("SH", 2)))
			out.append("""		<th><a href="%s">client<br/>port</a></th>""" % (createorderlink("SH", 3)))
		
			out.append("""		<th><a href="%s">Server Id</a></th>""" % (createorderlink("SH", 5)))
			out.append("""		<th><a href="%s">state</a></th>""" % (createorderlink("SH", 6)))
			out.append("""	</tr>""")
			if SHorder < 1 or SHorder > 7:
				SHorder = 1

			rows = cltoma_metadataservers_list()
			rows = sorted(rows, reverse=SHrev, key=lambda x: x[SHorder - 1])
			i = 1
			for row in rows:
				out.append(make_table_row('<td>', '</td>', (i,) + row))
				i += 1
			out.append("""</table>""")
			print "\n".join(out)
		except Exception:
			print """<table class="FRA table table-bordered table-hover toggle-circle tablet breakpoint footable-loaded footable" cellspacing="0" summary="Exception">"""
			print """<tr><td align="left"><pre>"""
			traceback.print_exc(file=sys.stdout)
			print """</pre></td></tr>"""
			print """</table>"""
		print """<br/>"""

	out = []

	try:
		CSorder = int(fields.getvalue("CSorder"))
	except Exception:
		CSorder = 0
	try:
		CSrev = int(fields.getvalue("CSrev"))
	except Exception:
		CSrev = 0

	try:
		column_count = 13
		out.append("""<table class="FRA table table-bordered table-hover toggle-circle tablet breakpoint footable-loaded footable" cellspacing="0" summary="Chunk Servers">""")
		out.append("""	<tr class="info"><th colspan="14">Data Servers</th></tr>""")
		out.append("""	<tr class="info">""")
		out.append("""		<th rowspan="2">#</th>""")
		out.append("""		<th rowspan="2"><a href="%s">Host Name</a></th>""" % (createorderlink("CS",1)))
		out.append("""		<th rowspan="2"><a href="%s">IP</a></th>""" % (createorderlink("CS",2)))
		out.append("""		<th rowspan="2"><a href="%s">port</a></th>""" % (createorderlink("CS",3)))
		
		if masterversion>=LIZARDFS_VERSION_WITH_CUSTOM_GOALS:
			out.append("""		<th rowspan="2"><a href="%s">label</a></th>""" % (createorderlink("CS",24)))
			column_count += 1
		out.append("""		<th colspan="4">'regular' hdd space</th>""")
		if masterversion>=(1,6,10):
			out.append("""		<th colspan="4">'marked for removal' hdd space</th>""")
		else:
			out.append("""		<th colspan="4">'to be empty' hdd space</th>""")
		out.append("""	</tr>""")
		out.append("""	<tr class="info">""")
		out.append("""		<th><a href="%s">files</a></th>""" % (createorderlink("CS",10)))
		out.append("""		<th><a href="%s">used</a></th>""" % (createorderlink("CS",11)))
		out.append("""		<th><a href="%s">total</a></th>""" % (createorderlink("CS",12)))
		out.append("""		<th class="PROGBAR"><a href="%s">used %%</a></th>""" % (createorderlink("CS",13)))
		out.append("""		<th><a href="%s">files</a></th>""" % (createorderlink("CS",20)))
		out.append("""		<th><a href="%s">used</a></th>""" % (createorderlink("CS",21)))
		out.append("""		<th><a href="%s">total</a></th>""" % (createorderlink("CS",22)))
		out.append("""		<th class="PROGBAR"><a href="%s">used %% </a></th>""" % (createorderlink("CS",23)))
		out.append("""	</tr>""")

		s = socket.socket()
		s.connect((masterhost,masterport))
		if masterversion>=LIZARDFS_VERSION_WITH_CUSTOM_GOALS:
			mysend(s,struct.pack(">LLLB",LIZ_CLTOMA_CSERV_LIST,5,0,0))
		else:
			mysend(s,struct.pack(">LL",CLTOMA_CSERV_LIST,0))
		header = myrecv(s,8)
		cmd, length = struct.unpack(">LL",header)
		data = myrecv(s, length)
		servers = []
		if cmd==LIZ_MATOCL_CSERV_LIST:
			version, vector_size = struct.unpack(">LL", data[0:8])
			pos = 8
		else:
			vector_size = length / 54
			pos = 0
		for i in xrange(vector_size):
			if cmd==LIZ_MATOCL_CSERV_LIST:
				disconnected,v1,v2,v3,ip1,ip2,ip3,ip4,port,used,total,chunks,tdused,tdtotal,tdchunks,errcnt,label_length = struct.unpack(">BBBBBBBBHQQLQQLLL",data[pos:pos + 58])
				label = data[pos+58:pos+58+label_length-1]
				pos = pos + 58 + label_length
			else:
				disconnected,v1,v2,v3,ip1,ip2,ip3,ip4,port,used,total,chunks,tdused,tdtotal,tdchunks,errcnt = struct.unpack(">BBBBBBBBHQQLQQLL",data[pos:pos + 54])
				label = "_"
				pos = pos + 54
			strip = "%u.%u.%u.%u" % (ip1,ip2,ip3,ip4)
			try:
				host = (socket.gethostbyaddr(strip))[0]
			except Exception:
				host = "(unresolved)"
			if CSorder==1:
				sf = host
			elif CSorder==2 or CSorder==0:
				sf = (ip1,ip2,ip3,ip4)
			elif CSorder==3:
				sf = port
			elif CSorder==4:
				sf = (v1,v2,v3)
			elif CSorder==10:
				sf = chunks
			elif CSorder==11:
				sf = used
			elif CSorder==12:
				sf = total
			elif CSorder==13:
				if total>0:
					sf = (1.0*used)/total
				else:
					sf = 0
			elif CSorder==20:
				sf = tdchunks
			elif CSorder==21:
				sf = tdused
			elif CSorder==22:
				sf = tdtotal
			elif CSorder==23:
				if tdtotal>0:
					sf = (1.0*tdused)/tdtotal
				else:
					sf = 0
			elif CSorder==24:
				sf = label
			else:
				sf = 0
			servers.append((sf,disconnected,host,strip,label,port,v1,v2,v3,used,total,chunks,tdused,tdtotal,tdchunks,errcnt))
			servers.sort()
			if CSrev:
				servers.reverse()
		i = 1
		for sf,disconnected,host,strip,label,port,v1,v2,v3,used,total,chunks,tdused,tdtotal,tdchunks,errcnt in servers:
			out.append("""	<tr class="C%u">""" % (((i-1)%2)+1))
			if disconnected==1:
				out.append("""		<td align="right"><span class="DISCONNECTED">%u</span></td><td align="left"><span class="DISCONNECTED">%s</span></td><td align="center"><span class="DISCONNECTED">%s</span></td><td align="center"><span class="DISCONNECTED">%u</span></td><td align="center"><span class="DISCONNECTED">disconnected !!!</span></td><td align="right" colspan="%d"><a href="%s">click to remove</a></td>""" % (i,host,strip,port,column_count-5,createlink({"CSremove":("%s:%u" % (strip,port))})))
			else:
				out.append("""		<td align="right">%u</td><td align="left">%s</td><td align="center">%s</td><td align="center">%u</td>""" % (i,host,strip,port))
				if masterversion>=LIZARDFS_VERSION_WITH_CUSTOM_GOALS:
					out.append("""		<td class="LEFT">%s</td>""" % label)
				out.append("""		<td align="right">%u</td><td align="right"><a style="cursor:default" title="%s B">%sB</a></td><td align="right"><a style="cursor:default" title="%s B">%sB</a></td>""" % (chunks,decimal_number(used),humanize_number(used,"&nbsp;"),decimal_number(total),humanize_number(total,"&nbsp;")))
				if (total>0):
					out.append("""<td><div class="pie-title-center mar-rgt charter" data-percent="%.2f"><span class="pie-value text-thin"></span></div></td>""" % ((used*100.0)/total))
				else:
					out.append("""		<td><div class="pie-title-center mar-rgt charter" data-percent="0"><span class="pie-value text-thin"></span></div></td>""")
				out.append("""		<td align="right">%u</td><td align="right"><a style="cursor:default" title="%s B">%sB</a></td><td align="right"><a style="cursor:default" title="%s B">%sB</a></td>""" % (tdchunks,decimal_number(tdused),humanize_number(tdused,"&nbsp;"),decimal_number(tdtotal),humanize_number(tdtotal,"&nbsp;")))
				if (tdtotal>0):
					out.append("""		<td><div class="pie-title-center mar-rgt charter" data-percent="%.2f"><span class="pie-value text-thin"></span></div></td>""" % ((tdused*100.0)/tdtotal))
				else:
					out.append("""		<td><div class="pie-title-center mar-rgt charter" data-percent="0"><span class="pie-value text-thin"></span></div></td>""")
			out.append("""	</tr>""")
			i+=1

		out.append("""</table>""")
		s.close()
		print "\n".join(out)
	except Exception:
		print """<table class="FRA table table-bordered table-hover toggle-circle tablet breakpoint footable-loaded footable" cellspacing="0" summary="Exception">"""
		print """<tr><td align="left"><pre>"""
		traceback.print_exc(file=sys.stdout)
		print """</pre></td></tr>"""
		print """</table>"""

	print """<br/>"""

	if masterversion>=(1,6,5):
		out = []

		try:
			MBorder = int(fields.getvalue("MBorder"))
		except Exception:
			MBorder = 0
		try:
			MBrev = int(fields.getvalue("MBrev"))
		except Exception:
			MBrev = 0

		try:
			out.append("""<table class="FRA table table-bordered table-hover toggle-circle tablet breakpoint footable-loaded footable" cellspacing="0" summary="Metadata Backup loggers">""")
			out.append("""	<tr class="info"><th colspan="4">Metadata Backup</th></tr>""")
			out.append("""	<tr class="info">""")
			out.append("""		<th>#</th>""")
			out.append("""		<th><a href="%s">host</a></th>""" % (createorderlink("MB",1)))
			out.append("""		<th><a href="%s">IP</a></th>""" % (createorderlink("MB",2)))
			out.append("""		<th><a href="%s">version</a></th>""" % (createorderlink("MB",3)))
			out.append("""	</tr>""")

			s = socket.socket()
			s.connect((masterhost,masterport))
			mysend(s,struct.pack(">LL",CLTOMA_MLOG_LIST,0))
			header = myrecv(s,8)
			cmd,length = struct.unpack(">LL",header)
			if cmd==MATOCL_MLOG_LIST and (length%8)==0:
				data = myrecv(s,length)
				n = length/8
				servers = []
				for i in xrange(n):
					d = data[i*8:(i+1)*8]
					v1,v2,v3,ip1,ip2,ip3,ip4 = struct.unpack(">HBBBBBB",d)
					strip = "%u.%u.%u.%u" % (ip1,ip2,ip3,ip4)
					try:
						host = (socket.gethostbyaddr(strip))[0]
					except Exception:
						host = "(unresolved)"
					if MBorder==1:
						sf = host
					elif MBorder==2 or MBorder==0:
						sf = (ip1,ip2,ip3,ip4)
					elif MBorder==3:
						sf = (v1,v2,v3)
					servers.append((sf,host,strip,v1,v2,v3))
				servers.sort()
				if MBrev:
					servers.reverse()
				i = 1
				for sf,host,strip,v1,v2,v3 in servers:
					out.append("""	<tr class="C%u">""" % (((i-1)%2)+1))
					out.append("""		<td align="right">%u</td><td align="left">%s</td><td align="center">%s</td><td align="center">%u.%u.%u</td>""" % (i,host,strip,v1,v2,v3))
					out.append("""	</tr>""")
					i+=1
			out.append("""</table>""")
			s.close()
			print "\n".join(out)
		except Exception:
			print """<table class="FRA table table-bordered table-hover toggle-circle tablet breakpoint footable-loaded footable" cellspacing="0" summary="Exception">"""
			print """<tr><td align="left"><pre>"""
			traceback.print_exc(file=sys.stdout)
			print """</pre></td></tr>"""
			print """</table>"""

		print """<br/>"""

if "HD" in sectionset:
	out = []

	try:
		HDorder = int(fields.getvalue("HDorder"))
	except Exception:
		HDorder = 0
	try:
		HDrev = int(fields.getvalue("HDrev"))
	except Exception:
		HDrev = 0
	try:
		HDperiod = int(fields.getvalue("HDperiod"))
	except Exception:
		HDperiod = 0
	try:
		HDtime = int(fields.getvalue("HDtime"))
	except Exception:
		HDtime = 0
	try:
		HDaddrname = int(fields.getvalue("HDaddrname"))
	except Exception:
		HDaddrname = 0

	try:
		# get cs list
		hostlist = []
		s = socket.socket()
		s.connect((masterhost,masterport))
		mysend(s,struct.pack(">LL",CLTOMA_CSERV_LIST,0))
		header = myrecv(s,8)
		cmd,length = struct.unpack(">LL",header)
		if cmd==MATOCL_CSERV_LIST and masterversion>=(1,5,13) and (length%54)==0:
			data = myrecv(s,length)
			n = length/54
			servers = []
			for i in xrange(n):
				d = data[i*54:(i+1)*54]
				disconnected,v1,v2,v3,ip1,ip2,ip3,ip4,port,used,total,chunks,tdused,tdtotal,tdchunks,errcnt = struct.unpack(">BBBBBBBBHQQLQQLL",d)
				if disconnected==0:
					hostlist.append((v1,v2,v3,ip1,ip2,ip3,ip4,port))
		elif cmd==MATOCL_CSERV_LIST and masterversion<(1,5,13) and (length%50)==0:
			data = myrecv(s,length)
			n = length/50
			servers = []
			for i in xrange(n):
				d = data[i*50:(i+1)*50]
				ip1,ip2,ip3,ip4,port,used,total,chunks,tdused,tdtotal,tdchunks,errcnt = struct.unpack(">BBBBHQQLQQLL",d)
				hostlist.append((1,5,0,ip1,ip2,ip3,ip4,port))
		s.close()

		# get hdd lists one by one
		hdd = []
		for v1,v2,v3,ip1,ip2,ip3,ip4,port in hostlist:
			hostip = "%u.%u.%u.%u" % (ip1,ip2,ip3,ip4)
			try:
				hoststr = (socket.gethostbyaddr(hostip))[0]
			except Exception:
				hoststr = "(unresolved)"
			if port>0:
				if (v1,v2,v3)<=(1,6,8):
					s = socket.socket()
					s.connect((hostip,port))
					mysend(s,struct.pack(">LL",CLTOCS_HDD_LIST_V1,0))
					header = myrecv(s,8)
					cmd,length = struct.unpack(">LL",header)
					if cmd==CSTOCL_HDD_LIST_V1:
						data = myrecv(s,length)
						while length>0:
							plen = ord(data[0])
							if HDaddrname==1:
								path = "%s:%u:%s" % (hoststr,port,data[1:plen+1])
							else:
								path = "%s:%u:%s" % (hostip,port,data[1:plen+1])
							flags,errchunkid,errtime,used,total,chunkscnt = struct.unpack(">BQLQQL",data[plen+1:plen+34])
							length -= plen+34
							data = data[plen+34:]
							if HDorder==1 or HDorder==0:
								sf = (ip1,ip2,ip3,ip4,port,data[1:plen+1])
							elif HDorder==2:
								sf = chunkscnt
							elif HDorder==3:
								sf = errtime
							elif HDorder==4:
								sf = -flags
							elif HDorder==20:
								sf = used
							elif HDorder==21:
								sf = total
							elif HDorder==22:
								if total>0:
									sf = (1.0*used)/total
								else:
									sf = 0
							else:
								sf = 0
							hdd.append((sf,path,flags,errchunkid,errtime,used,total,chunkscnt,0,0,0,0,0,0,0,0,0,0,0,0))
					s.close()
				else:
					s = socket.socket()
					s.connect((hostip,port))
					mysend(s,struct.pack(">LL",CLTOCS_HDD_LIST_V2,0))
					header = myrecv(s,8)
					cmd,length = struct.unpack(">LL",header)
					if cmd==CSTOCL_HDD_LIST_V2:
						data = myrecv(s,length)
						while length>0:
							entrysize = struct.unpack(">H",data[:2])[0]
							entry = data[2:2+entrysize]
							data = data[2+entrysize:]
							length -= 2+entrysize;

							plen = ord(entry[0])
							if HDaddrname==1:
								path = "%s:%u:%s" % (hoststr,port,entry[1:plen+1])
							else:
								path = "%s:%u:%s" % (hostip,port,entry[1:plen+1])
							flags,errchunkid,errtime,used,total,chunkscnt = struct.unpack(">BQLQQL",entry[plen+1:plen+34])
							rbytes,wbytes,usecreadsum,usecwritesum,usecfsyncsum,rops,wops,fsyncops,usecreadmax,usecwritemax,usecfsyncmax = (0,0,0,0,0,0,0,0,0,0,0)
							if entrysize==plen+34+144:
								if HDperiod==0:
									rbytes,wbytes,usecreadsum,usecwritesum,rops,wops,usecreadmax,usecwritemax = struct.unpack(">QQQQLLLL",entry[plen+34:plen+34+48])
								elif HDperiod==1:
									rbytes,wbytes,usecreadsum,usecwritesum,rops,wops,usecreadmax,usecwritemax = struct.unpack(">QQQQLLLL",entry[plen+34+48:plen+34+96])
								elif HDperiod==2:
									rbytes,wbytes,usecreadsum,usecwritesum,rops,wops,usecreadmax,usecwritemax = struct.unpack(">QQQQLLLL",entry[plen+34+96:plen+34+144])
							elif entrysize==plen+34+192:
								if HDperiod==0:
									rbytes,wbytes,usecreadsum,usecwritesum,usecfsyncsum,rops,wops,fsyncops,usecreadmax,usecwritemax,usecfsyncmax = struct.unpack(">QQQQQLLLLLL",entry[plen+34:plen+34+64])
								elif HDperiod==1:
									rbytes,wbytes,usecreadsum,usecwritesum,usecfsyncsum,rops,wops,fsyncops,usecreadmax,usecwritemax,usecfsyncmax = struct.unpack(">QQQQQLLLLLL",entry[plen+34+64:plen+34+128])
								elif HDperiod==2:
									rbytes,wbytes,usecreadsum,usecwritesum,usecfsyncsum,rops,wops,fsyncops,usecreadmax,usecwritemax,usecfsyncmax = struct.unpack(">QQQQQLLLLLL",entry[plen+34+128:plen+34+192])
							if usecreadsum>0:
								rbw = rbytes*1000000/usecreadsum
							else:
								rbw = 0
							if usecwritesum+usecfsyncsum>0:
								wbw = wbytes*1000000/(usecwritesum+usecfsyncsum)
							else:
								wbw = 0
							if HDtime==1:
								if rops>0:
									rtime = usecreadsum/rops
								else:
									rtime = 0
								if wops>0:
									wtime = usecwritesum/wops
								else:
									wtime = 0
								if fsyncops>0:
									fsynctime = usecfsyncsum/fsyncops
								else:
									fsynctime = 0
							else:
								rtime = usecreadmax
								wtime = usecwritemax
								fsynctime = usecfsyncmax
							if HDorder==1 or HDorder==0:
								sf = (ip1,ip2,ip3,ip4,port,data[1:plen+1])
							elif HDorder==2:
								sf = chunkscnt
							elif HDorder==3:
								sf = errtime
							elif HDorder==4:
								sf = -flags
							elif HDorder==5:
								sf = rbw
							elif HDorder==6:
								sf = wbw
							elif HDorder==7:
								sf = -rtime
							elif HDorder==8:
								sf = -wtime
							elif HDorder==9:
								sf = -fsynctime
							elif HDorder==10:
								sf = rops
							elif HDorder==11:
								sf = wops
							elif HDorder==12:
								sf = fsyncops
							elif HDorder==20:
								sf = used
							elif HDorder==21:
								sf = total
							elif HDorder==22:
								if total>0:
									sf = (1.0*used)/total
								else:
									sf = 0
							else:
								sf = 0
							hdd.append((sf,path,flags,errchunkid,errtime,used,total,chunkscnt,rbw,wbw,rtime,wtime,fsynctime,rops,wops,fsyncops,rbytes,wbytes,usecreadsum,usecwritesum))
					s.close()

		if len(hdd)>0:
			out.append("""<table class="FRA smdiskmove table table-bordered table-hover toggle-circle tablet breakpoint footable-loaded footable" cellspacing="0" summary="Disks">""")
			
			out.append("""	<tr class="info">""")
			out.append("""		<th rowspan="3">#</th>""")
			out.append("""		<th colspan="4" rowspan="2">vDisks Info</th>""")
			if HDperiod==2:
				out.append("""		<th colspan="8">I/O stats day <a href="%s" class="VISIBLELINK">min</a> <a href="%s" class="VISIBLELINK">hour</a></th>""" % (createlink({"HDperiod":"0"}),createlink({"HDperiod":"1"})))
			elif HDperiod==1:
				out.append("""		<th colspan="8">I/O stats hour <a href="%s" class="VISIBLELINK">min</a> <a href="%s" class="VISIBLELINK">day</a></th>""" % (createlink({"HDperiod":"0"}),createlink({"HDperiod":"2"})))
			else:
				out.append("""		<th colspan="8">I/O stats min <a href="%s" class="VISIBLELINK">hour</a> <a href="%s" class="VISIBLELINK">day</a></th>""" % (createlink({"HDperiod":"1"}),createlink({"HDperiod":"2"})))
			out.append("""		<th colspan="3" rowspan="2">Disk Space</th>""")
			out.append("""	</tr>""")
			out.append("""	<tr class="info">""")
			out.append("""		<th colspan="2"><a style="cursor:default" title="average data transfer speed">transfer</a></th>""")
			if HDtime==1:
				out.append("""		<th colspan="3"><a style="cursor:default" title="average time of read or write chunk block (up to 64kB)">average</a> <a href="%s" class="VISIBLELINK">max time</a></th>""" % (createlink({"HDtime":"0"})))
			else:
				out.append("""		<th colspan="3"><a style="cursor:default" title="max time of read or write one chunk block (up to 64kB)">max time</a> <a href="%s" class="VISIBLELINK">average</a></th>""" % (createlink({"HDtime":"1"})))
			out.append("""		<th colspan="3"><a style="cursor:default" title="number of chunk block operations / chunk fsyncs">OF OPS</a></th></tr>""")
			out.append("""	<tr class="info">""")
			if HDaddrname==1:
				out.append("""		<th><a href="%s">name path</a> (<a href="%s" class="VISIBLELINK">switch to IP</a>)</th>""" % (createorderlink("HD",1),createlink({"HDaddrname":"0"})))
			else:
				out.append("""		<th><a href="%s">IP Address</a> (<a href="%s" class="VISIBLELINK">switch to name</a>)</th>""" % (createorderlink("HD",1),createlink({"HDaddrname":"1"})))
			out.append("""		<th><a href="%s">Files</a></th>""" % (createorderlink("HD",2)))
			out.append("""		<th><a href="%s">Errors</a></th>""" % (createorderlink("HD",3)))
			out.append("""		<th><a href="%s">status</a></th>""" % (createorderlink("HD",4)))
			out.append("""		<th><a href="%s">read</a></th>""" % (createorderlink("HD",5)))
			out.append("""		<th><a href="%s">write</a></th>""" % (createorderlink("HD",6)))
			out.append("""		<th><a href="%s">read</a></th>""" % (createorderlink("HD",7)))
			out.append("""		<th><a href="%s">write</a></th>""" % (createorderlink("HD",8)))
			out.append("""		<th><a href="%s">fsync</a></th>""" % (createorderlink("HD",9)))
			out.append("""		<th><a href="%s">read</a></th>""" % (createorderlink("HD",10)))
			out.append("""		<th><a href="%s">write</a></th>""" % (createorderlink("HD",11)))
			out.append("""		<th><a href="%s">fsync</a></th>""" % (createorderlink("HD",12)))
			out.append("""		<th><a href="%s">used GiB</a></th>""" % (createorderlink("HD",20)))
			out.append("""		<th><a href="%s">total GiB</a></th>""" % (createorderlink("HD",21)))
			out.append("""		<th class="SMPROGBAR"><a href="%s">used (%%)</a></th>""" % (createorderlink("HD",22)))
			out.append("""	</tr>""")
			hdd.sort()
			if HDrev:
				hdd.reverse()
			i = 1
			for sf,path,flags,errchunkid,errtime,used,total,chunkscnt,rbw,wbw,rtime,wtime,fsynctime,rops,wops,fsyncops,rbytes,wbytes,rsum,wsum in hdd:
				if flags==1:
					if masterversion>=(1,6,10):
						status = 'marked for removal'
					else:
						status = 'to be empty'
				elif flags==2:
					status = 'damaged'
				elif flags==3:
					if masterversion>=(1,6,10):
						status = 'damaged, marked for removal'
					else:
						status = 'damaged, to be empty'
				elif flags==4 or flags==6:
					status = 'scanning'
				elif flags==5 or flags==7:
					status = 'marked for removal, scanning'
				else:
					status = 'ok'
				if errtime==0 and errchunkid==0:
					lerror = 'no errors'
				else:
					errtimetuple = time.localtime(errtime)
					lerror = '<a style="cursor:default" title="%s on chunk: %u">%s</a>' % (time.strftime("%Y-%m-%d %H:%M:%S",errtimetuple),errchunkid,time.strftime("%Y-%m-%d %H:%M",errtimetuple))
				out.append("""	<tr class="C%u">""" % (((i-1)%2)+1))
				out.append("""		<td align="right">%u</td><td align="left">%s</td><td align="right">%u</td><td align="right">%s</td><td align="right" class="vdiskstat">%s</td>""" % (i,path,chunkscnt,lerror,status))
				if rbw==0 and wbw==0 and rtime==0 and wtime==0 and rops==0 and wops==0:
					out.append("""		<td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td>""")
				else:
					if rops>0:
						rbsize = rbytes/rops
					else:
						rbsize = 0
					if wops>0:
						wbsize = wbytes/wops
					else:
						wbsize = 0
					out.append("""		<td align="right"><a style="cursor:default" title="%s B/s">%sB/s</a></td><td align="right"><a style="cursor:default" title="%s B">%sB/s</a></td>""" % (decimal_number(rbw),humanize_number(rbw,"&nbsp;"),decimal_number(wbw),humanize_number(wbw,"&nbsp;")))
					out.append("""		<td align="right">%u us</td><td align="right">%u us</td><td align="right">%u us</td><td align="right"><a style="cursor:default" title="average block size: %u B">%u</a></td><td align="right"><a style="cursor:default" title="average block size: %u B">%u</a></td><td align="right">%u</td>""" % (rtime,wtime,fsynctime,rbsize,rops,wbsize,wops,fsyncops))
				if flags&4:
					out.append("""		<td colspan="3" align="right"><div class="box"><div class="progress" style="width:%upx;"></div><div class="value">%.0f%% scanned</div></div></td>""" % (int(used)*2,used))
				else:
					out.append("""		<td align="right"><a style="cursor:default" title="%s B">%sB</a></td><td align="right"><a style="cursor:default" title="%s B">%sB</a></td>""" % (decimal_number(used),humanize_number(used,"&nbsp;"),decimal_number(total),humanize_number(total,"&nbsp;")))
					if (total>0):
						out.append("""<td><div class="pie-title-center mar-rgt charter" data-percent="%.2f"><span class="pie-value text-thin"></span></div></td>""" % ((used*100.0)/total))
					else:
						out.append("""<td><div class="pie-title-center mar-rgt charter" data-percent="0"><span class="pie-value text-thin"></span></div></td>""")
				out.append("""	</tr>""")
				i+=1
			out.append("""</table>""")

		print "\n".join(out)
	except Exception:
		print """<table class="FRA table table-bordered table-hover toggle-circle tablet breakpoint footable-loaded footable" cellspacing="0" summary="Exception">"""
		print """<tr><td align="left"><pre>"""
		traceback.print_exc(file=sys.stdout)
		print """</pre></td></tr>"""
		print """</table>"""

	print """<br/>"""

if "EX" in sectionset:
	out = []

	try:
		EXorder = int(fields.getvalue("EXorder"))
	except Exception:
		EXorder = 0
	try:
		EXrev = int(fields.getvalue("EXrev"))
	except Exception:
		EXrev = 0

	try:
		out.append("""<table class="FRA table table-bordered table-hover toggle-circle tablet breakpoint footable-loaded footable" cellspacing="0" summary="Exports">""")
		out.append("""	<tr class="info"><th colspan="%u">Exports</th></tr>""" % (19 if masterversion>=LIZARDFS_VERSION_WITH_QUOTAS else 18 if masterversion>=(1,6,26) else 14))
		out.append("""	<tr class="info">""")
		out.append("""		<th rowspan="2">#</th>""")
		out.append("""		<th colspan="2">ip&nbsp;range</th>""")
		out.append("""		<th rowspan="2"><a href="%s">path</a></th>""" % (createorderlink("EX",3)))
		out.append("""		<th rowspan="2"><a href="%s">minversion</a></th>""" % (createorderlink("EX",4)))
		out.append("""		<th rowspan="2"><a href="%s">alldirs</a></th>""" % (createorderlink("EX",5)))
		out.append("""		<th rowspan="2"><a href="%s">password</a></th>""" % (createorderlink("EX",6)))
		out.append("""		<th rowspan="2"><a href="%s">ro/rw</a></th>""" % (createorderlink("EX",7)))
		out.append("""		<th rowspan="2"><a href="%s">restricted&nbsp;ip</a></th>""" % (createorderlink("EX",8)))
		out.append("""		<th rowspan="2"><a href="%s">ignore&nbsp;gid</a></th>""" % (createorderlink("EX",9)))
		if masterversion>=LIZARDFS_VERSION_WITH_QUOTAS:
			out.append("""		<th rowspan="2"><a href="%s">quota&nbsp;admin</a></th>""" % (createorderlink("EX",10)))
		out.append("""		<th colspan="2">map&nbsp;root</th>""")
		out.append("""		<th colspan="2">map&nbsp;users</th>""")
		if masterversion>=(1,6,26):
			out.append("""		<th colspan="2">goal&nbsp;limit</th>""")
			out.append("""		<th colspan="2">trashtime&nbsp;limit</th>""")
		out.append("""	</tr>""")
		out.append("""	<tr>""")
		out.append("""		<th><a href="%s">from</a></th>""" % (createorderlink("EX",1)))
		out.append("""		<th><a href="%s">to</a></th>""" % (createorderlink("EX",2)))
		out.append("""		<th><a href="%s">uid</a></th>""" % (createorderlink("EX",11)))
		out.append("""		<th><a href="%s">gid</a></th>""" % (createorderlink("EX",12)))
		out.append("""		<th><a href="%s">uid</a></th>""" % (createorderlink("EX",13)))
		out.append("""		<th><a href="%s">gid</a></th>""" % (createorderlink("EX",14)))
		if masterversion>=(1,6,26):
			out.append("""		<th><a href="%s">min</a></th>""" % (createorderlink("EX",15)))
			out.append("""		<th><a href="%s">max</a></th>""" % (createorderlink("EX",16)))
			out.append("""		<th><a href="%s">min</a></th>""" % (createorderlink("EX",17)))
			out.append("""		<th><a href="%s">max</a></th>""" % (createorderlink("EX",18)))
		out.append("""	</tr>""")

		s = socket.socket()
		s.connect((masterhost,masterport))
		if masterversion>=(1,6,26):
			mysend(s,struct.pack(">LLB",CLTOMA_EXPORTS_INFO,1,1))
		else:
			mysend(s,struct.pack(">LL",CLTOMA_EXPORTS_INFO,0))
		header = myrecv(s,8)
		cmd,length = struct.unpack(">LL",header)
		if cmd==MATOCL_EXPORTS_INFO and masterversion>=(1,5,14):
			data = myrecv(s,length)
			servers = []
			pos = 0
			while pos<length:
				fip1,fip2,fip3,fip4,tip1,tip2,tip3,tip4,pleng = struct.unpack(">BBBBBBBBL",data[pos:pos+12])
				ipfrom = "%d.%d.%d.%d" % (fip1,fip2,fip3,fip4)
				ipto = "%d.%d.%d.%d" % (tip1,tip2,tip3,tip4)
				pos+=12
				path = data[pos:pos+pleng]
				pos+=pleng
				if masterversion>=(1,6,26):
					v1,v2,v3,exportflags,sesflags,rootuid,rootgid,mapalluid,mapallgid,mingoal,maxgoal,mintrashtime,maxtrashtime = struct.unpack(">HBBBBLLLLBBLL",data[pos:pos+32])
					pos+=32
					if mingoal<=1 and maxgoal>=20:
						mingoal = None
						maxgoal = None
					if mintrashtime==0 and maxtrashtime==0xFFFFFFFF:
						mintrashtime = None
						maxtrashtime = None
				elif masterversion>=(1,6,1):
					v1,v2,v3,exportflags,sesflags,rootuid,rootgid,mapalluid,mapallgid = struct.unpack(">HBBBBLLLL",data[pos:pos+22])
					mingoal = None;
					maxgoal = None;
					mintrashtime = None;
					maxtrashtime = None;
					pos+=22
				else:
					v1,v2,v3,exportflags,sesflags,rootuid,rootgid = struct.unpack(">HBBBBLL",data[pos:pos+14])
					mapalluid = 0
					mapallgid = 0
					mingoal = None;
					maxgoal = None;
					mintrashtime = None;
					maxtrashtime = None;
					pos+=14
				ver = "%d.%d.%d" % (v1,v2,v3)
				if path=='.':
					meta=1
				else:
					meta=0
				if EXorder==1 or EXorder==0:
					sf = (fip1,fip2,fip3,fip4)
				elif EXorder==2:
					sf = (tip1,tip2,tip3,tip4)
				elif EXorder==3:
					sf = path
				elif EXorder==4:
					sf = (v1,v2,v3)
				elif EXorder==5:
					if meta:
						sf = None
					else:
						sf = exportflags&1
				elif EXorder==6:
					sf = exportflags&2
				elif EXorder==7:
					sf = sesflags&1
				elif EXorder==8:
					sf = 2-(sesflags&2)
				elif EXorder==9:
					if meta:
						sf = None
					else:
						sf = sesflags&4
				elif EXorder==10:
					if meta:
						sf = None
					else:
						sf = sesflags&8
				elif EXorder==11:
					if meta:
						sf = None
					else:
						sf = rootuid
				elif EXorder==12:
					if meta:
						sf = None
					else:
						sf = rootgid
				elif EXorder==13:
					if meta or (sesflags&16)==0:
						sf = None
					else:
						sf = mapalluid
				elif EXorder==14:
					if meta or (sesflags&16)==0:
						sf = None
					else:
						sf = mapalluid
				elif EXorder==15:
					sf = mingoal
				elif EXorder==16:
					sf = maxgoal
				elif EXorder==17:
					sf = mintrashtime
				elif EXorder==18:
					sf = maxtrashtime
				else:
					sf = 0
				servers.append((sf,ipfrom,ipto,path,meta,ver,exportflags,sesflags,rootuid,rootgid,mapalluid,mapallgid,mingoal,maxgoal,mintrashtime,maxtrashtime))
			servers.sort()
			if EXrev:
				servers.reverse()
			i = 1
			for sf,ipfrom,ipto,path,meta,ver,exportflags,sesflags,rootuid,rootgid,mapalluid,mapallgid,mingoal,maxgoal,mintrashtime,maxtrashtime in servers:
				out.append("""	<tr class="C%u">""" % (((i-1)%2)+1))
				out.append("""		<td align="right">%u</td>""" % i)
				out.append("""		<td align="center">%s</td>""" % ipfrom)
				out.append("""		<td align="center">%s</td>""" % ipto)
				out.append("""		<td align="left">%s</td>""" % (".&nbsp;(META)" if meta else path))
				out.append("""		<td align="center">%s</td>""" % ver)
				out.append("""		<td align="center">%s</td>""" % ("-" if meta else "yes" if exportflags&1 else "no"))
				out.append("""		<td align="center">%s</td>""" % ("yes" if exportflags&2 else "no"))
				out.append("""		<td align="center">%s</td>""" % ("ro" if sesflags&1 else "rw"))
				out.append("""		<td align="center">%s</td>""" % ("no" if sesflags&2 else "yes"))
				out.append("""		<td align="center">%s</td>""" % ("-" if meta else "yes" if sesflags&4 else "no"))
				if masterversion>=LIZARDFS_VERSION_WITH_QUOTAS:
					out.append("""		<td align="center">%s</td>""" % ("-" if meta else "yes" if sesflags&8 else "no"))
				if meta:
					out.append("""		<td align="center">-</td>""")
					out.append("""		<td align="center">-</td>""")
				else:
					out.append("""		<td align="right">%u</td>""" % rootuid)
					out.append("""		<td align="right">%u</td>""" % rootgid)
				if meta or (sesflags&16)==0:
					out.append("""		<td align="center">-</td>""")
					out.append("""		<td align="center">-</td>""")
				else:
					out.append("""		<td align="right">%u</td>""" % mapalluid)
					out.append("""		<td align="right">%u</td>""" % mapallgid)
				if masterversion>=(1,6,26):
					if mingoal!=None and maxgoal!=None:
						out.append("""		<td align="right">%u</td>""" % mingoal)
						out.append("""		<td align="right">%u</td>""" % maxgoal)
					else:
						out.append("""		<td align="center">-</td>""")
						out.append("""		<td align="center">-</td>""")
					if mintrashtime!=None and maxtrashtime!=None:
						out.append("""		<td align="right"><a style="cursor:default" title="%s">%s</a></td>""" % (timeduration_to_fullstr(mintrashtime),timeduration_to_shortstr(mintrashtime)))
						out.append("""		<td align="right"><a style="cursor:default" title="%s">%s</a></td>""" % (timeduration_to_fullstr(maxtrashtime),timeduration_to_shortstr(maxtrashtime)))
					else:
						out.append("""		<td align="center">-</td>""")
						out.append("""		<td align="center">-</td>""")
				out.append("""	</tr>""")
				i+=1
		out.append("""</table>""")
		out.append("""<br/>""")
	except Exception:
		print """<table class="FRA table table-bordered table-hover toggle-circle tablet breakpoint footable-loaded footable" cellspacing="0" summary="Exception">"""
		print """<tr><td align="left"><pre>"""
		traceback.print_exc(file=sys.stdout)
		print """</pre></td></tr>"""
		print """</table>"""

	try:
		goals = cltoma_list_goals()
		out.append("""<table class="FRA table table-bordered table-hover toggle-circle tablet breakpoint footable-loaded footable" cellspacing="0" summary="Goal definitions">""")
		out.append("""	<tr class="info"><th colspan="3">Goal definitions</th></tr>""")
		out.append("""	<tr class="info"><th class="PERC4">ID</th><th class="PERC8 LEFT">name</th><th class="PERC88 LEFT">definition</th></tr>""")
		i = 0;
		for (id, name, definition) in goals:
			row_class = 1 + i % 2
			i += 1
			if id >= 247:
				# a xor goal
				id = "-"
			else:
				# Convert ugly 1*_,2*label1,3*label2 to something more readable
				definition = re.sub(r'([0-9]+)\*([A-Za-z0-9_]+)(,?)', r'\1 &times; <b>\2</b>\3 ', definition)
			out.append("""	<tr class="C%u"><td>%s</td><td class="LEFT">%s</td><td class="LEFT">%s</td>""" % (row_class, id, name, definition))
		out.append("""</table>""")
		print "\n".join(out)
	except Exception:
		print """<table class="FRA table table-bordered table-hover toggle-circle tablet breakpoint footable-loaded footable" cellspacing="0" summary="Exception">"""
		print """<tr><td align="left"><pre>"""
		traceback.print_exc(file=sys.stdout)
		print """</pre></td></tr>"""
		print """</table>"""

	print """<br/>"""

if "ML" in sectionset:
	out = []

	try:
		MLorder = int(fields.getvalue("MLorder"))
	except Exception:
		MLorder = 0
	try:
		MLrev = int(fields.getvalue("MLrev"))
	except Exception:
		MLrev = 0

	try:
		out.append("""<table class="FRA table table-bordered table-hover toggle-circle tablet breakpoint footable-loaded footable" cellspacing="0" summary="Active mounts">""")
		out.append("""	<tr class="info"><th colspan="20">Active mounts</th></tr>""")
		out.append("""	<tr class="info">""")
		out.append("""		<th rowspan="2">#</th>""")
		out.append("""		<th rowspan="2"><a href="%s">host</a></th>""" % (createorderlink("ML",1)))
		out.append("""		<th rowspan="2"><a href="%s">ip</a></th>""" % (createorderlink("ML",2)))
		out.append("""		<th rowspan="2"><a href="%s">version</a></th>""" % (createorderlink("ML",3)))
		out.append("""		<th colspan="16">operations current hour/last hour</th>""")
		out.append("""	</tr>""")
		out.append("""	<tr class="info">""")
		out.append("""		<th><a href="%s">statfs</a></th>""" % (createorderlink("ML",100)))
		out.append("""		<th><a href="%s">getattr</a></th>""" % (createorderlink("ML",101)))
		out.append("""		<th><a href="%s">setattr</a></th>""" % (createorderlink("ML",102)))
		out.append("""		<th><a href="%s">lookup</a></th>""" % (createorderlink("ML",103)))
		out.append("""		<th><a href="%s">mkdir</a></th>""" % (createorderlink("ML",104)))
		out.append("""		<th><a href="%s">rmdir</a></th>""" % (createorderlink("ML",105)))
		out.append("""		<th><a href="%s">symlink</a></th>""" % (createorderlink("ML",106)))
		out.append("""		<th><a href="%s">readlink</a></th>""" % (createorderlink("ML",107)))
		out.append("""		<th><a href="%s">mknod</a></th>""" % (createorderlink("ML",108)))
		out.append("""		<th><a href="%s">unlink</a></th>""" % (createorderlink("ML",109)))
		out.append("""		<th><a href="%s">rename</a></th>""" % (createorderlink("ML",110)))
		out.append("""		<th><a href="%s">link</a></th>""" % (createorderlink("ML",111)))
		out.append("""		<th><a href="%s">readdir</a></th>""" % (createorderlink("ML",112)))
		out.append("""		<th><a href="%s">open</a></th>""" % (createorderlink("ML",113)))
		out.append("""		<th><a href="%s">read</a></th>""" % (createorderlink("ML",114)))
		out.append("""		<th><a href="%s">write</a></th>""" % (createorderlink("ML",115)))
		out.append("""	</tr>""")

		s = socket.socket()
		s.connect((masterhost,masterport))
		mysend(s,struct.pack(">LL",CLTOMA_SESSION_LIST,0))
		header = myrecv(s,8)
		cmd,length = struct.unpack(">LL",header)
		if cmd==MATOCL_SESSION_LIST and masterversion<=(1,5,13) and (length%136)==0:
			data = myrecv(s,length)
			n = length/136
			servers = []
			for i in xrange(n):
				d = data[i*136:(i+1)*136]
				addrdata = d[0:8]
				stats_c = []
				stats_l = []
				ip1,ip2,ip3,ip4,spare,v1,v2,v3 = struct.unpack(">BBBBBBBB",addrdata)
				ipnum = "%d.%d.%d.%d" % (ip1,ip2,ip3,ip4)
				if v1==0 and v2==0:
					if v3==2:
						ver = "1.3.x"
					elif v3==3:
						ver = "1.4.x"
					else:
						ver = "unknown"
				else:
					ver = "%d.%d.%d" % (v1,v2,v3)
				for i in xrange(16):
					stats_c.append(struct.unpack(">L",d[i*4+8:i*4+12]))
					stats_l.append(struct.unpack(">L",d[i*4+72:i*4+76]))
				try:
					host = (socket.gethostbyaddr(ipnum))[0]
				except Exception:
					host = "(unresolved)"
				if MLorder==1:
					sf = host
				elif MLorder==2 or MLorder==0:
					sf = (ip1,ip2,ip3,ip4)
				elif MLorder==3:
					sf = (v1,v2,v3)
				elif MLorder>=100 and MLorder<=115:
					sf = stats_c[MLorder-100][0]+stats_l[MLorder-100][0]
				else:
					sf = 0
				servers.append((sf,host,ipnum,ver,stats_c,stats_l))
			servers.sort()
			if MLrev:
				servers.reverse()
			i = 1
			for sf,host,ipnum,ver,stats_c,stats_l in servers:
				out.append("""	<tr class="C%u">""" % (((i-1)%2)*2+1))
				out.append("""		<td align="right" rowspan="2">%u</td>""" % i)
				out.append("""		<td align="left" rowspan="2">%s</td>""" % host)
				out.append("""		<td align="center" rowspan="2">%s</td>""" % ipnum)
				out.append("""		<td align="center" rowspan="2">%s</td>""" % ver)
				for st in xrange(16):
					out.append("""		<td align="right">%u</td>""" % (stats_c[st]))
				out.append("""	</tr>""")
				out.append("""	<tr class="C%u">""" % (((i-1)%2)*2+2))
				for st in xrange(16):
					out.append("""		<td align="right">%u</td>""" % (stats_l[st]))
				out.append("""	</tr>""")
				i+=1
		out.append("""</table>""")
		s.close()
		print "\n".join(out)
	except Exception:
		print """<table class="FRA table table-bordered table-hover toggle-circle tablet breakpoint footable-loaded footable" cellspacing="0" summary="Exception">"""
		print """<tr><td align="left"><pre>"""
		traceback.print_exc(file=sys.stdout)
		print """</pre></td></tr>"""
		print """</table>"""

	print """<br/>"""

if "MS" in sectionset:
	out = []

	try:
		MSorder = int(fields.getvalue("MSorder"))
	except Exception:
		MSorder = 0
	try:
		MSrev = int(fields.getvalue("MSrev"))
	except Exception:
		MSrev = 0

	try:
		out.append("""<table class="FRA table table-bordered table-hover toggle-circle tablet breakpoint footable-loaded footable" cellspacing="0" summary="Active mounts">""")
		out.append("""	<tr class="info"><th colspan="%u">Active mounts (parameters)</th></tr>""" % (19 if masterversion>=(2,5,0) else 18 if masterversion>=(1,6,26) else 14))
		out.append("""	<tr class="info">""")
		out.append("""		<th rowspan="2">#</th>""")
		out.append("""		<th rowspan="2"><a href="%s">session&nbsp;id</a></th>""" % (createorderlink("MS",1)))
		out.append("""		<th rowspan="2"><a href="%s">host</a></th>""" % (createorderlink("MS",2)))
		out.append("""		<th rowspan="2"><a href="%s">ip</a></th>""" % (createorderlink("MS",3)))
		out.append("""		<th rowspan="2"><a href="%s">mount&nbsp;point</a></th>""" % (createorderlink("MS",4)))
		out.append("""		<th rowspan="2"><a href="%s">version</a></th>""" % (createorderlink("MS",5)))
		out.append("""		<th rowspan="2"><a href="%s">root&nbsp;dir</a></th>""" % (createorderlink("MS",6)))
		out.append("""		<th rowspan="2"><a href="%s">ro/rw</a></th>""" % (createorderlink("MS",7)))
		out.append("""		<th rowspan="2"><a href="%s">restricted&nbsp;ip</a></th>""" % (createorderlink("MS",8)))
		out.append("""		<th rowspan="2"><a href="%s">ignore&nbsp;gid</a></th>""" % (createorderlink("MS",9)))
		if masterversion>=(2,5,0):
			out.append("""		<th rowspan="2"><a href="%s">quota&nbsp;admin</a></th>""" % (createorderlink("MS",10)))
		out.append("""		<th colspan="2">map&nbsp;root</th>""")
		out.append("""		<th colspan="2">map&nbsp;users</th>""")
		if masterversion>=(1,6,26):
			out.append("""		<th colspan="2">goal&nbsp;limits</th>""")
			out.append("""		<th colspan="2">trashtime&nbsp;limits</th>""")
		out.append("""	</tr>""")
		out.append("""	<tr class="info">""")
		out.append("""		<th><a href="%s">uid</a></th>""" % (createorderlink("MS",11)))
		out.append("""		<th><a href="%s">gid</a></th>""" % (createorderlink("MS",12)))
		out.append("""		<th><a href="%s">uid</a></th>""" % (createorderlink("MS",13)))
		out.append("""		<th><a href="%s">gid</a></th>""" % (createorderlink("MS",14)))
		if masterversion>=(1,6,26):
			out.append("""		<th><a href="%s">min</a></th>""" % (createorderlink("MS",15)))
			out.append("""		<th><a href="%s">max</a></th>""" % (createorderlink("MS",16)))
			out.append("""		<th><a href="%s">min</a></th>""" % (createorderlink("MS",17)))
			out.append("""		<th><a href="%s">max</a></th>""" % (createorderlink("MS",18)))
		out.append("""	</tr>""")

		s = socket.socket()
		s.connect((masterhost,masterport))
		if masterversion>=(1,6,26):
			mysend(s,struct.pack(">LLB",CLTOMA_SESSION_LIST,1,1))
		else:
			mysend(s,struct.pack(">LL",CLTOMA_SESSION_LIST,0))
		header = myrecv(s,8)
		cmd,length = struct.unpack(">LL",header)
		if cmd==MATOCL_SESSION_LIST and masterversion>=(1,5,14):
			data = myrecv(s,length)
			servers = []
			if masterversion<(1,6,21):
				statscnt = 16
				pos = 0
			elif masterversion==(1,6,21):
				statscnt = 21
				pos = 0
			else:
				statscnt = struct.unpack(">H",data[0:2])[0]
				pos = 2
			while pos<length:
				sessionid,ip1,ip2,ip3,ip4,v1,v2,v3,ileng = struct.unpack(">LBBBBHBBL",data[pos:pos+16])
				ipnum = "%d.%d.%d.%d" % (ip1,ip2,ip3,ip4)
				ver = "%d.%d.%d" % (v1,v2,v3)
				pos+=16
				info = data[pos:pos+ileng]
				pos+=ileng
				pleng = struct.unpack(">L",data[pos:pos+4])[0]
				pos+=4
				path = data[pos:pos+pleng]
				pos+=pleng
				if masterversion>=(1,6,26):
					sesflags,rootuid,rootgid,mapalluid,mapallgid,mingoal,maxgoal,mintrashtime,maxtrashtime = struct.unpack(">BLLLLBBLL",data[pos:pos+27])
					pos+=27
					if mingoal<=1 and maxgoal>=20:
						mingoal = None
						maxgoal = None
					if mintrashtime==0 and maxtrashtime==0xFFFFFFFF:
						mintrashtime = None
						maxtrashtime = None
				elif masterversion>=(1,6,1):
					sesflags,rootuid,rootgid,mapalluid,mapallgid = struct.unpack(">BLLLL",data[pos:pos+17])
					mingoal = None
					maxgoal = None
					mintrashtime = None
					maxtrashtime = None
					pos+=17
				else:
					sesflags,rootuid,rootgid = struct.unpack(">BLL",data[pos:pos+9])
					mapalluid = 0
					mapallgid = 0
					mingoal = None
					maxgoal = None
					mintrashtime = None
					maxtrashtime = None
					pos+=9
				pos+=8*statscnt		# skip stats
				if path=='.':
					meta=1
				else:
					meta=0
				try:
					host = (socket.gethostbyaddr(ipnum))[0]
				except Exception:
					host = "(unresolved)"
#				if path=="":
#					path="(empty)"
				if MSorder==1:
					sf = sessionid
				elif MSorder==2:
					sf = host
				elif MSorder==3 or MSorder==0:
					sf = (ip1,ip2,ip3,ip4)
				elif MSorder==4:
					sf = info
				elif MSorder==5:
					sf = (v1,v2,v3)
				elif MSorder==6:
					sf = path
				elif MSorder==7:
					sf = sesflags&1
				elif MSorder==8:
					sf = 2-(sesflags&2)
				elif MSorder==9:
					if meta:
						sf = None
					else:
						sf = sesflags&4
				elif MSorder==10:
					if meta:
						sf = None
					else:
						sf = sesflags&8
				elif MSorder==11:
					if meta:
						sf = None
					else:
						sf = rootuid
				elif MSorder==12:
					if meta:
						sf = None
					else:
						sf = rootgid
				elif MSorder==13:
					if meta or (sesflags&16)==0:
						sf = None
					else:
						sf = mapalluid
				elif MSorder==14:
					if meta or (sesflags&16)==0:
						sf = None
					else:
						sf = mapallgid
				elif MSorder==15:
					sf = mingoal
				elif MSorder==16:
					sf = maxgoal
				elif MSorder==17:
					sf = mintrashtime
				elif MSorder==18:
					sf = maxtrashtime
				else:
					sf = 0
				servers.append((sf,sessionid,host,ipnum,info,ver,meta,path,sesflags,rootuid,rootgid,mapalluid,mapallgid,mingoal,maxgoal,mintrashtime,maxtrashtime))
			servers.sort()
			if MSrev:
				servers.reverse()
			i = 1
			for sf,sessionid,host,ipnum,info,ver,meta,path,sesflags,rootuid,rootgid,mapalluid,mapallgid,mingoal,maxgoal,mintrashtime,maxtrashtime in servers:
				out.append("""	<tr class="C%u">""" % (((i-1)%2)+1))
				out.append("""		<td align="right">%u</td>""" % i)
				out.append("""		<td align="center">%u</td>""" % sessionid)
				out.append("""		<td align="left">%s</td>""" % host)
				out.append("""		<td align="center">%s</td>""" % ipnum)
				out.append("""		<td align="left">%s</td>""" % info)
				out.append("""		<td align="center">%s</td>""" % ver)
				if meta:
					out.append("""		<td align="left">.&nbsp;(META)</td>""")
				else:
					out.append("""		<td align="left">%s</td>""" % path)
				if sesflags&1:
					out.append("""		<td align="center">ro</td>""")
				else:
					out.append("""		<td align="center">rw</td>""")
				if sesflags&2:
					out.append("""		<td align="center">no</td>""")
				else:
					out.append("""		<td align="center">yes</td>""")
				if meta:
					out.append("""		<td align="center">-</td>""")
				elif sesflags&4:
					out.append("""		<td align="center">yes</td>""")
				else:
					out.append("""		<td align="center">no</td>""")
				if masterversion>=(2,5,0):
					if meta:
						out.append("""		<td align="center">-</td>""")
					elif sesflags&8:
						out.append("""		<td align="center">yes</td>""")
					else:
						out.append("""		<td align="center">no</td>""")
				if meta:
					out.append("""		<td align="center">-</td>""")
					out.append("""		<td align="center">-</td>""")
				else:
					out.append("""		<td align="right">%u</td>""" % rootuid)
					out.append("""		<td align="right">%u</td>""" % rootgid)
				if meta or (sesflags&16)==0:
					out.append("""		<td align="center">-</td>""")
					out.append("""		<td align="center">-</td>""")
				else:
					out.append("""		<td align="right">%u</td>""" % mapalluid)
					out.append("""		<td align="right">%u</td>""" % mapallgid)
				if masterversion>=(1,6,26):
					if mingoal!=None and maxgoal!=None:
						out.append("""		<td align="right">%u</td>""" % mingoal)
						out.append("""		<td align="right">%u</td>""" % maxgoal)
					else:
						out.append("""		<td align="center">-</td>""")
						out.append("""		<td align="center">-</td>""")
					if mintrashtime!=None and maxtrashtime!=None:
						out.append("""		<td align="right"><a style="cursor:default" title="%s">%s</a></td>""" % (timeduration_to_fullstr(mintrashtime),timeduration_to_shortstr(mintrashtime)))
						out.append("""		<td align="right"><a style="cursor:default" title="%s">%s</a></td>""" % (timeduration_to_fullstr(maxtrashtime),timeduration_to_shortstr(maxtrashtime)))
					else:
						out.append("""		<td align="center">-</td>""")
						out.append("""		<td align="center">-</td>""")
				out.append("""	</tr>""")
				i+=1
		out.append("""</table>""")
		s.close()
		print "\n".join(out)
	except Exception:
		print """<table class="FRA table table-bordered table-hover toggle-circle tablet breakpoint footable-loaded footable" cellspacing="0" summary="Exception">"""
		print """<tr><td align="left"><pre>"""
		traceback.print_exc(file=sys.stdout)
		print """</pre></td></tr>"""
		print """</table>"""

	print """<br/>"""

if "MO" in sectionset:
	out = []

	try:
		MOorder = int(fields.getvalue("MOorder"))
	except Exception:
		MOorder = 0
	try:
		MOrev = int(fields.getvalue("MOrev"))
	except Exception:
		MOrev = 0

	try:
		out.append("""<table class="FRA table table-bordered table-hover toggle-circle tablet breakpoint footable-loaded footable" cellspacing="0" summary="Active mounts">""")
		out.append("""	<tr class="info"><th colspan="21">Active mounts (operations)</th></tr>""")
		out.append("""	<tr class="info">""")
		out.append("""		<th rowspan="2">#</th>""")
		out.append("""		<th rowspan="2"><a href="%s">host</a></th>""" % (createorderlink("MO",1)))
		out.append("""		<th rowspan="2"><a href="%s">ip</a></th>""" % (createorderlink("MO",2)))
		out.append("""		<th rowspan="2"><a href="%s">mount&nbsp;point</a></th>""" % (createorderlink("MO",3)))
		out.append("""		<th colspan="17">operations current hour/last hour</th>""")
		out.append("""	</tr>""")
		out.append("""	<tr class="info">""")
		out.append("""		<th><a href="%s">statfs</a></th>""" % (createorderlink("MO",100)))
		out.append("""		<th><a href="%s">getattr</a></th>""" % (createorderlink("MO",101)))
		out.append("""		<th><a href="%s">setattr</a></th>""" % (createorderlink("MO",102)))
		out.append("""		<th><a href="%s">lookup</a></th>""" % (createorderlink("MO",103)))
		out.append("""		<th><a href="%s">mkdir</a></th>""" % (createorderlink("MO",104)))
		out.append("""		<th><a href="%s">rmdir</a></th>""" % (createorderlink("MO",105)))
		out.append("""		<th><a href="%s">symlink</a></th>""" % (createorderlink("MO",106)))
		out.append("""		<th><a href="%s">readlink</a></th>""" % (createorderlink("MO",107)))
		out.append("""		<th><a href="%s">mknod</a></th>""" % (createorderlink("MO",108)))
		out.append("""		<th><a href="%s">unlink</a></th>""" % (createorderlink("MO",109)))
		out.append("""		<th><a href="%s">rename</a></th>""" % (createorderlink("MO",110)))
		out.append("""		<th><a href="%s">link</a></th>""" % (createorderlink("MO",111)))
		out.append("""		<th><a href="%s">readdir</a></th>""" % (createorderlink("MO",112)))
		out.append("""		<th><a href="%s">open</a></th>""" % (createorderlink("MO",113)))
		out.append("""		<th><a href="%s">read</a></th>""" % (createorderlink("MO",114)))
		out.append("""		<th><a href="%s">write</a></th>""" % (createorderlink("MO",115)))
		out.append("""		<th><a href="%s">total</a></th>""" % (createorderlink("MO",150)))
		out.append("""	</tr>""")

		s = socket.socket()
		s.connect((masterhost,masterport))
		mysend(s,struct.pack(">LL",CLTOMA_SESSION_LIST,0))
		header = myrecv(s,8)
		cmd,length = struct.unpack(">LL",header)
		if cmd==MATOCL_SESSION_LIST and masterversion>=(1,5,14):
			data = myrecv(s,length)
			servers = []
			if masterversion<(1,6,21):
				statscnt = 16
				pos = 0
			elif masterversion==(1,6,21):
				statscnt = 21
				pos = 0
			else:
				statscnt = struct.unpack(">H",data[0:2])[0]
				pos = 2
			while pos<length:
				sessionid,ip1,ip2,ip3,ip4,v1,v2,v3,ileng = struct.unpack(">LBBBBHBBL",data[pos:pos+16])
				ipnum = "%d.%d.%d.%d" % (ip1,ip2,ip3,ip4)
				ver = "%d.%d.%d" % (v1,v2,v3)
				pos+=16
				info = data[pos:pos+ileng]
				pos+=ileng
				pleng = struct.unpack(">L",data[pos:pos+4])[0]
				pos+=4
				path = data[pos:pos+pleng]
				pos+=pleng
				# sesflags,rootuid,rootgid,mapalluid,mapallgid = struct.unpack(">BLLLL",data[pos:pos+17])
				if masterversion>=(1,6,0):
					pos+=17
				else:
					pos+=9
				if statscnt<16:
					stats_c = struct.unpack(">"+"L"*statscnt,data[pos:pos+4*statscnt])+(0,)*(16-statscnt)
					pos+=statscnt*4
					stats_l = struct.unpack(">"+"L"*statscnt,data[pos:pos+4*statscnt])+(0,)*(16-statscnt)
					pos+=statscnt*4
				else:
					stats_c = struct.unpack(">LLLLLLLLLLLLLLLL",data[pos:pos+64])
					pos+=statscnt*4
					stats_l = struct.unpack(">LLLLLLLLLLLLLLLL",data[pos:pos+64])
					pos+=statscnt*4
				try:
					host = (socket.gethostbyaddr(ipnum))[0]
				except Exception:
					host = "(unresolved)"
				if MOorder==1:
					sf = host
				elif MOorder==2 or MOorder==0:
					sf = (ip1,ip2,ip3,ip4)
				elif MOorder==3:
					sf = info
				elif MOorder>=100 and MOorder<=115:
					sf = -(stats_c[MOorder-100]+stats_l[MOorder-100])
				elif MOorder==150:
					sf = -(sum(stats_c)+sum(stats_l))
				else:
					sf = 0
				if path!='.':
					servers.append((sf,host,ipnum,info,stats_c,stats_l))
			servers.sort()
			if MOrev:
				servers.reverse()
			i = 1
			for sf,host,ipnum,info,stats_c,stats_l in servers:
				out.append("""	<tr class="C%u">""" % (((i-1)%2)*2+1))
				out.append("""		<td align="right" rowspan="2">%u</td>""" % i)
				out.append("""		<td align="left" rowspan="2">%s</td>""" % host)
				out.append("""		<td align="center" rowspan="2">%s</td>""" % ipnum)
				out.append("""		<td align="left" rowspan="2">%s</td>""" % info)
				for st in xrange(16):
					out.append("""		<td align="right">%u</td>""" % (stats_c[st]))
				out.append("""		<td align="right">%u</td>""" % (sum(stats_c)))
				out.append("""	</tr>""")
				out.append("""	<tr class="C%u">""" % (((i-1)%2)*2+2))
				for st in xrange(16):
					out.append("""		<td align="right">%u</td>""" % (stats_l[st]))
				out.append("""		<td align="right">%u</td>""" % (sum(stats_l)))
				out.append("""	</tr>""")
				i+=1
		out.append("""</table>""")
		s.close()
		print "\n".join(out)
	except Exception:
		print """<table class="FRA table table-bordered table-hover toggle-circle tablet breakpoint footable-loaded footable" cellspacing="0" summary="Exception">"""
		print """<tr>11<td align="left"><pre>"""
		traceback.print_exc(file=sys.stdout)
		print """</pre></td></tr>"""
		print """</table>"""

	print """<br/>"""

if "MC" in sectionset:
	out = []

	try:
		charts = (
			(100,'cpu','cpu usage (percent)'),
			(20,'memory','memory usage (if available)'),
			(2,'dels','chunk deletions (per minute)'),
			(3,'repl','chunk replications (per minute)'),
			(4,'stafs','statfs operations (per minute)'),
			(5,'getattr','getattr operations (per minute)'),
			(6,'setattr','setattr operations (per minute)'),
			(7,'lookup','lookup operations (per minute)'),
			(8,'mkdir','mkdir operations (per minute)'),
			(9,'rmdir','rmdir operations (per minute)'),
			(10,'symlink','symlink operations (per minute)'),
			(11,'readlink','readlink operations (per minute)'),
			(12,'mknod','mknod operations (per minute)'),
			(13,'unlink','unlink operations (per minute)'),
			(14,'rename','rename operations (per minute)'),
			(15,'link','link operations (per minute)'),
			(16,'readdir','readdir operations (per minute)'),
			(17,'open','open operations (per minute)'),
			(18,'read','read operations (per minute)'),
			(19,'write','write operations (per minute)'),
			(21,'prcvd','packets received (per second)'),
			(22,'psent','packets sent (per second)'),
			(23,'brcvd','bits received (per second)'),
			(24,'bsent','bits sent (per second)')
		)
		out.append("""<div class="panel">
					
								<!--Panel heading-->
								<div class="panel-heading">
									<div class="panel-control">
										<ul class="nav nav-tabs tabelo">
											<li class="active"><a data-toggle="tab" href="#demo-tabs-box-1">CPU</a></li>
											<li><a data-toggle="tab" href="#demo-tabs-box-2">Memory</a></li>
											<li><a data-toggle="tab" href="#demo-tabs-box-3">Deletion</a></li>
											<li><a data-toggle="tab" href="#demo-tabs-box-4">Replication</a></li>
											<li><a data-toggle="tab" href="#demo-tabs-box-5">Read</a></li>
											<li><a data-toggle="tab" href="#demo-tabs-box-6">Write</a></li>
											<li><a data-toggle="tab" href="#demo-tabs-box-7">Packets Received</a></li>
											<li><a data-toggle="tab" href="#demo-tabs-box-8">Packets Sent</a></li>
										</ul>
									</div>
									<h3 class="panel-title">&nbsp;</h3>
								</div>
					""")
		out.append("""<script type="text/javascript">""")
		out.append("""<!--//--><![CDATA[//><!--""")
		out.append("""	var i,j;""")
		out.append("""	var ma_chartid = new Array(0,0);""")
		out.append("""	var ma_range=0;""")
		out.append("""	var ma_imgs = new Array();""")
		out.append("""	var ma_vids = new Array(%s);""" % ','.join(['"%s"' % x[0] for x in charts]))
		out.append("""	var ma_inames = new Array(%s);""" % ','.join(['"%s"' % x[1] for x in charts]))
		out.append("""	var ma_idesc = new Array(%s);""" % ','.join(['"%s"' % x[2] for x in charts]))
		out.append("""	for (i=0 ; i<ma_vids.length ; i++) {""")
		out.append("""		for (j=0 ; j<4 ; j++) {""")
		out.append("""			var vid = ma_vids[i];""")
		out.append("""			var id = vid*10+j;""")
		out.append("""			ma_imgs[id] = new Image();""")
		out.append("""			ma_imgs[id].src = "chart.cgi?host=%s&amp;port=%u&amp;id="+id;""" % (urlescape(masterhost),masterport))
		out.append("""		}""")
		out.append("""	}""")
		out.append("""	function ma_change(num) {""")
		out.append("""		for (i=0 ; i<ma_inames.length ; i++) {""")
		out.append("""			var name = "ma_"+ma_inames[i];""")
		out.append("""			var vid = ma_vids[i];""")
		out.append("""			var id = vid*10+num;""")
		out.append("""			document.images[name].src = ma_imgs[id].src;""")
		out.append("""		}""")
		out.append("""	}""")
		out.append("""	function ma_cmp_refresh() {""")
		out.append("""		var vid,id,iname;""")
		out.append("""		for (i=0 ; i<2 ; i++) {""")
		out.append("""			vid = ma_vids[ma_chartid[i]];""")
		out.append("""			id = vid*10+ma_range;""")
		out.append("""			iname = "ma_chart"+i;""")
		out.append("""			document.images[iname].src = ma_imgs[id].src;""")
		out.append("""		}""")
		out.append("""	}""")
		out.append("""	function ma_change_range(no) {""")
		out.append("""		ma_range = no;""")
		out.append("""		ma_cmp_refresh();""")
		out.append("""	}""")
		out.append("""	function ma_change_type(id,no) {""")
		out.append("""		var o;""")
		out.append("""		o = document.getElementById("ma_cell_"+id+"_"+ma_chartid[id]);""")
		out.append("""		o.className="REL";""")
		out.append("""		ma_chartid[id]=no;""")
		out.append("""		o = document.getElementById("ma_cell_"+id+"_"+ma_chartid[id]);""")
		out.append("""		o.className="PR";""")
		out.append("""		o = document.getElementById("ma_desc"+id);""")
		out.append("""		o.innerHTML = ma_idesc[no];""")
		out.append("""		ma_cmp_refresh();""")
		out.append("""	}""")
		out.append("""	function ma_change_links(range) {""")
		out.append("""		var table = document.getElementById("ma_stats_table");""")
		out.append("""		var row;""")
		out.append("""		var cells;""")
		out.append("""		var str;""")
		out.append("""		for (var i = 0; row = table.rows[i]; i++) {""")
		out.append("""			cells = row.cells;""")
		out.append("""			for (j in cells) {""")
		out.append("""				if (cells[j].children !== undefined && cells[j].children[1] !== undefined){""")
		out.append("""					str=cells[j].children[1].href;""")
		out.append("""					cells[j].children[1].href=str.slice(0,-1)+range;""")
		out.append("""					str=cells[j].children[1].children[0].src;""")
		out.append("""					cells[j].children[1].children[0].src = str.slice(0,-1)+ range;""")
		out.append("""				}""")
		out.append("""			}""")
		out.append("""		}""")
		out.append("""	}""")
		out.append("""//--><!]]>""")
		out.append("""</script>""")
		out.append("""<div >""")
		out.append("""<table id="ma_stats_table" class="FRA table table-bordered table-hover toggle-circle tablet breakpoint footable-loaded footable" cellspacing="0" summary="Master Stats">""")
		#out.append("""	<tr class="info">""")
		#out.append("""		<th><a href="javascript:ma_change_links(0);">short range</a></th>""")
		#out.append("""		<th><a href="javascript:ma_change_links(1);">medium range</a></th>""")
		#out.append("""		<th><a href="javascript:ma_change_links(2);">long range</a></th>""")
		#out.append("""		<th><a href="javascript:ma_change_links(3);">very long range</a></th>""")
		#out.append("""	</tr>""")
		out.append(""" <!--Panel body-->
								<div class="panel-body">
									<div class="tab-content tabelocont">
										""")
		i = 0
		for id,name,desc in charts:
			i = i+1
			if i == 1:

				out.append(""" <div id="demo-tabs-box-%i" class="tab-pane fade in active"> """ % (i))
			else:
				out.append(""" <div id="demo-tabs-box-%i" class="tab-pane fade"> """ % (i))


		
			#out.append("""			%s:<br/><a href="chart.cgi?host=%s&amp;port=%u&amp;id=%u"> """ % (desc, urlescape(masterhost),masterport,CHARTS_CSV_CHARTID_BASE+id*10))
			#out.append("""			<img  src="chart.cgi?host=%s&amp;port=%u&amp;id=%u" width="1000" height="120" id="ma_%s" alt="%s" /></a>""" % (urlescape(masterhost),masterport,id*10,name,name))
			if i == 1:
				out.append("""<h3 class="zago">CPU Usage:</h3><div class="labelezo"><span class="daylabel">Day</span><span class="weeklabel">Week</span><span class="monthlabel">Month</span></div><div class="labeleso"></div>""")
				out.append("""<div id="cpu-chart-area" style="height:212px"></div><div class="todate"></div>""")

			if i == 2:
				out.append("""<h3 class="zago">Memory Usage:</h3><div class="labelezo"><span class="memdaylabel daylbl">Day</span><span class="memweeklabel weeklbl">Week</span><span class="memmonthlabel monthlbl">Month</span></div><div class="labeleso"></div>""")
				out.append("""<div id="memory-chart-area" style="height:212px"></div><div class="todate"></div>""")

			if i == 3:
				out.append("""<h3 class="zago">Files Deletion:</h3><div class="labelezo"><span class="deldaylabel daylbl">Day</span><span class="delweeklabel weeklbl">Week</span><span class="delmonthlabel monthlbl">Month</span></div><div class="labeleso"></div>""")
				out.append("""<div id="deletion-chart-area" style="height:212px"></div><div class="todate"></div>""")

			if i == 4:
				out.append("""<h3 class="zago">Files Replication:</h3><div class="labelezo"><span class="repdaylabel daylbl">Day</span><span class="repweeklabel weeklbl">Week</span><span class="repmonthlabel monthlbl">Month</span></div><div class="labeleso"></div>""")
				out.append("""<div id="replication-chart-area" style="height:212px"></div><div class="todate"></div>""")

			if i == 5:
				out.append("""<h3 class="zago">Read:</h3><div class="labelezo"><span class="readdaylabel daylbl">Day</span><span class="readweeklabel weeklbl">Week</span><span class="readmonthlabel monthlbl">Month</span></div><div class="labeleso"></div>""")
				out.append("""<div id="read-chart-area" style="height:212px"></div><div class="todate"></div>""")

			if i == 6:
				out.append("""<h3 class="zago">Write:</h3><div class="labelezo"><span class="writedaylabel daylbl">Day</span><span class="writeweeklabel weeklbl">Week</span><span class="writemonthlabel monthlbl">Month</span></div><div class="labeleso"></div>""")
				out.append("""<div id="write-chart-area" style="height:212px"></div><div class="todate"></div>""")

			if i == 7:
				out.append("""<h3 class="zago">Packets Received:</h3><div class="labelezo"><span class="prdaylabel daylbl">Day</span><span class="prweeklabel weeklbl">Week</span><span class="prmonthlabel monthlbl">Month</span></div><div class="labeleso"></div>""")
				out.append("""<div id="pr-chart-area" style="height:212px"></div><div class="todate"></div>""")

			if i == 8:
				out.append("""<h3 class="zago">Packets Sent:</h3><div class="labelezo"><span class="psdaylabel daylbl">Day</span><span class="psweeklabel weeklbl">Week</span><span class="psmonthlabel monthlbl">Month</span></div><div class="labeleso"></div>""")
				out.append("""<div id="ps-chart-area" style="height:212px"></div><div class="todate"></div>""")

			out.append("""</div>""")
			
		out.append("""</table></div>""")
	
		
		#out.append("""<table class="FRA table table-bordered table-hover toggle-circle tablet breakpoint footable-loaded footable" cellspacing="0" summary="Master stats">""")
		#out.append("""	<tr class="info">""")
		#out.append("""		<th><a href="javascript:ma_change_range(0);">short range</a></th>""")
		#out.append("""		<th><a href="javascript:ma_change_range(1);">medium range</a></th>""")
		#out.append("""		<th><a href="javascript:ma_change_range(2);">long range</a></th>""")
		#out.append("""		<th><a href="javascript:ma_change_range(3);">very long range</a></th>""")
		#out.append("""	</tr>""")
		#out.append("""</table>""")


		out.append("""</div></div>""")


		#out.append("""<table class="FRA table table-bordered table-hover toggle-circle tablet breakpoint footable-loaded footable" cellspacing="0" summary="Master charts view">""")
		#for i in xrange(2):
		#	out.append("""	<tr>""")
		#	out.append("""		<td align="center" colspan="4">""")
		#	out.append("""			<div id="ma_desc%u">%s</div>""" % (i,charts[0][2]))
		#	out.append("""			<img src="chart.cgi?host=%s&amp;port=%u&amp;id=%u" width="1000" height="120" id="ma_chart%u" alt="chart" />""" % (urlescape(masterhost),masterport,10*charts[0][0],i))
		#	out.append("""			<table class="BOTMENU" cellspacing="0" summary="Master charts menu">""")
		#	out.append("""				<tr>""")
		#	no=0
		#	cl="PR"
		#	for id,name,desc in charts:
		#		out.append("""					<td align="center" id="ma_cell_%u_%u" class="%s"><a href="javascript:ma_change_type(%u,%u);" title="%s">%s</a></td>""" % (i,no,cl,i,no,desc,name))
		#		cl="REL"
		#		no+=1
		#	out.append("""				</tr>""")
		#	out.append("""			</table>""")
		#	out.append("""		</td>""")
		#	out.append("""	</tr>""")
		#out.append("""</table>""")
		print "\n".join(out)
	except Exception:
		print """<table class="FRA table table-bordered table-hover toggle-circle tablet breakpoint footable-loaded footable" cellspacing="0" summary="Exception">"""
		print """<tr><td align="left"><pre>"""
		traceback.print_exc(file=sys.stdout)
		print """</pre></td></tr>"""
		print """</table>"""

	print """<br/>"""

if "CC" in sectionset:
	out = []

	try:
		if fields.has_key("CCdata"):
			CCdata = fields.getvalue("CCdata")
		else:
			CCdata = ""
	except Exception:
		CCdata = ""

	try:
		# get cs list
		hostlist = []
		s = socket.socket()
		s.connect((masterhost,masterport))
		mysend(s,struct.pack(">LL",CLTOMA_CSERV_LIST,0))
		header = myrecv(s,8)
		cmd,length = struct.unpack(">LL",header)
		if cmd==MATOCL_CSERV_LIST and (length%54)==0:
			data = myrecv(s,length)
			n = length/54
			for i in xrange(n):
				d = data[i*54:(i+1)*54]
				disconnected,v1,v2,v3,ip1,ip2,ip3,ip4,port,used,total,chunks,tdused,tdtotal,tdchunks,errcnt = struct.unpack(">BBBBBBBBHQQLQQLL",d)
				if disconnected==0:
					hostlist.append((ip1,ip2,ip3,ip4,port))
		elif cmd==MATOCL_CSERV_LIST and (length%50)==0:
			data = myrecv(s,length)
			n = length/50
			for i in xrange(n):
				d = data[i*50:(i+1)*50]
				ip1,ip2,ip3,ip4,port,used,total,chunks,tdused,tdtotal,tdchunks,errcnt = struct.unpack(">BBBBHQQLQQLL",d)
				hostlist.append((ip1,ip2,ip3,ip4,port))
		s.close()

		charts = (
			(100,'cpu','cpu usage (percent)'),
			(101,'datain','traffic from clients and other chunkservers (bits/s)'),
			(102,'dataout','traffic to clients and other chunkservers (bits/s)'),
			(103,'bytesr','bytes read - data/other (bytes/s)'),
			(104,'bytesw','bytes written - data/other (bytes/s)'),
			(2,'masterin','traffic from master (bits/s)'),
			(3,'masterout','traffic to master (bits/s)'),
			#(105,'hddopr','number of low-level read operations per minute'),
			#(106,'hddopw','number of low-level write operations per minute'),
			#(16,'hlopr','number of high-level read operations per minute'),
			#(17,'hlopw','number of high-level write operations per minute'),
			#(18,'rtime','time of data read operations'),
			#(19,'wtime','time of data write operations'),
			(20,'repl','number of chunk replications per minute'),
			(21,'create','number of chunk creations per minute'),
			(22,'delete','number of chunk deletions per minute'),
			(27,'tests','number of chunk tests per minute'),
		)
		servers = []

		if len(hostlist)>0:
			hostlist.sort()
			out.append("""<form action=""><table class="FRA table table-bordered table-hover toggle-circle tablet breakpoint footable-loaded footable" cellspacing="0" summary="Server charts selection"><tr class="info"><th>Server Manager: <select name="server" id="select" size="1" onchange="document.location.href='%s&amp;CCdata='+this.options[this.selectedIndex].value">""" % createlink({"CCdata":""}))
			entrystr = []
			entrydesc = {}
			for id,oname,desc in charts:
				name = oname.replace(":","")
				entrystr.append(name)
				entrydesc[name] = desc
			for ip1,ip2,ip3,ip4,port in hostlist:
				strip = "%u.%u.%u.%u" % (ip1,ip2,ip3,ip4)
				name = "%s:%u" % (strip,port)
				try:
					host = " / "+(socket.gethostbyaddr(strip))[0]
				except Exception:
					host = ""
				entrystr.append(name)
				entrydesc[name] = "Server: %s%s" % (name,host)
				servers.append((strip,port,name.replace(".","_").replace(":","_"),entrydesc[name]))
			if CCdata not in entrystr:
				out.append("""<option value="" selected="selected"> data type or server</option>""")
			for estr in entrystr:
				if estr==CCdata:
					out.append("""<option value="%s" selected="selected">%s</option>""" % (estr,entrydesc[estr]))
				else:
					out.append("""<option value="%s" class="select">%s</option>""" % (estr,entrydesc[estr]))
			out.append("""</select></th></tr></table></form><br/>""")

		cchtmp = CCdata.split(":")
		if len(cchtmp)==2:
			cshost = cchtmp[0]
			csport = cchtmp[1]

			out.append("""<script type="text/javascript">""")
			out.append("""<!--//--><![CDATA[//><!--""")
			out.append("""	var i,j;""")
			out.append("""	var cs_chartid = new Array(0,0);""")
			out.append("""	var cs_range=0;""")
			out.append("""	var cs_imgs = new Array();""")
			out.append("""	var cs_vids = new Array(%s);""" % ','.join(['"%s"' % x[0] for x in charts]))
			out.append("""	var cs_inames = new Array(%s);""" % ','.join(['"%s"' % x[1] for x in charts]))
			out.append("""	var cs_idesc = new Array(%s);""" % ','.join(['"%s"' % x[2] for x in charts]))
			out.append("""	for (i=0 ; i<cs_vids.length ; i++) {""")
			out.append("""		for (j=0 ; j<4 ; j++) {""")
			out.append("""			var vid = cs_vids[i];""")
			out.append("""			var id = vid*10+j;""")
			out.append("""			cs_imgs[id] = new Image();""")
			out.append("""			cs_imgs[id].src = "chart.cgi?host=%s&amp;port=%s&amp;id="+id;""" % (cshost,csport))
			out.append("""		}""")
			out.append("""	}""")
			out.append("""	function cs_change(num) {""")
			out.append("""		for (i=0 ; i<cs_inames.length ; i++) {""")
			out.append("""			var name = "cs_"+cs_inames[i];""")
			out.append("""			var vid = cs_vids[i];""")
			out.append("""			var id = vid*10+num;""")
			out.append("""			document.images[name].src = cs_imgs[id].src;""")
			out.append("""		}""")
			out.append("""	}""")
			out.append("""	function cs_cmp_refresh() {""")
			out.append("""		var vid,id,iname;""")
			out.append("""		for (i=0 ; i<2 ; i++) {""")
			out.append("""			vid = cs_vids[cs_chartid[i]];""")
			out.append("""			id = vid*10+cs_range;""")
			out.append("""			iname = "cs_chart"+i;""")
			out.append("""			document.images[iname].src = cs_imgs[id].src;""")
			out.append("""		}""")
			out.append("""	}""")
			out.append("""	function cs_change_range(no) {""")
			out.append("""		cs_range = no;""")
			out.append("""		cs_cmp_refresh();""")
			out.append("""	}""")
			out.append("""	function cs_change_type(id,no) {""")
			out.append("""		var o;""")
			out.append("""		o = document.getElementById("cs_cell_"+id+"_"+cs_chartid[id]);""")
			out.append("""		o.className="REL";""")
			out.append("""		cs_chartid[id]=no;""")
			out.append("""		o = document.getElementById("cs_cell_"+id+"_"+cs_chartid[id]);""")
			out.append("""		o.className="PR";""")
			out.append("""		o = document.getElementById("cs_desc"+id);""")
			out.append("""		o.innerHTML = cs_idesc[no];""")
			out.append("""		cs_cmp_refresh();""")
			out.append("""	}""")
			out.append("""	function cs_change_links(range) {""")
			out.append("""		var table = document.getElementById("cs_stats_table");""")
			out.append("""		var row;""")
			out.append("""		var cells;""")
			out.append("""		var str;""")
			out.append("""		for (var i = 0; row = table.rows[i]; i++) {""")
			out.append("""			cells = row.cells;""")
			out.append("""			for (j in cells) {""")
			out.append("""				if (cells[j].children !== undefined && cells[j].children[1] !== undefined){""")
			out.append("""					str=cells[j].children[1].href;""")
			out.append("""					cells[j].children[1].href=str.slice(0,-1) + range;""")
			out.append("""					str=cells[j].children[1].children[0].src;""")
			out.append("""					cells[j].children[1].children[0].src = str.slice(0,-1) + range;""")
			out.append("""				}""")
			out.append("""			}""")
			out.append("""		}""")
			out.append("""	}""")
			out.append("""//--><!]]>""")
			out.append("""</script>""")
			out.append("""<div >""")
			#out.append("""<table id="cs_stats_table" class="FRA table table-bordered table-hover toggle-circle tablet breakpoint footable-loaded footable" cellspacing="0" summary="Server stats">""")
			#out.append("""	<tr class="info">""")
			#out.append("""		<th><a href="javascript:cs_change_links(0);">short range!!!</a></th>""")
			#out.append("""		<th><a href="javascript:cs_change_links(1);">medium range</a></th>""")
			#out.append("""		<th><a href="javascript:cs_change_links(2);">long range</a></th>""")
			#out.append("""		<th><a href="javascript:cs_change_links(3);">very long range</a></th>""")
			#out.append("""	</tr>""")
			i = 0;
			out.append("""<div class="panel" id="panelcli"><!--Panel heading--><div class="panel-heading"><div class="panel-control"><ul class="nav nav-tabs tabelo" id="clitabz">
			<li class="active" id="clicpu"><a>CPU</a></li>
			<li id="clitraf"><a>Traffic</a></li>
			<li id="clibytes"><a>Bytes</a></li>
			<li id="cliperf"><a>Performance</a></li>
			
			</ul>
			</div>
			<h3 class="panel-title">&nbsp;</h3>
			</div>

			</div>
			
			""");

			for id,name,desc in charts:
				i = i + 1;
				out.append("""<div id="clientside%s" class="clientside">""" %(i))
				out.append("""			<h3 class="zago">%s</h3><br/> <span id="clichart%s" class="cliurlo"><a href="chart.cgi?host=%s&amp;port=%s&amp;id=%u">link</a></span>""" % (desc,i,cshost,csport,CHARTS_CSV_CHARTID_BASE+id*10))
				out.append("""<p align="center" class="preloader preloaderalign preloadera preload%s"><img src="../preloader.gif"/></p></div>""" %(i))
				out.append("""<div id="chart-client-%s" class="clientchart"></div> """ %(i))
				#out.append("""	<tr class="C2">""")
				#out.append("""		<td align="center" colspan="4">""")
				#out.append("""			%s:<br/> <a href="chart.cgi?host=%s&amp;port=%s&amp;id=%u">link</a>""" % (desc,cshost,csport,CHARTS_CSV_CHARTID_BASE+id*10))
				#out.append("""			<br/><img src="chart.cgi?host=%s&amp;port=%s&amp;id=%u" width="1000" height="120" id="cs_%s" alt="%s" /> <br/>""" % (cshost,csport,id*10,name,name))
				#out.append("""		</td>""")
				#out.append("""	</tr>""")
			#out.append("""</table>""")
			
			out.append("""<br/>""")

			#out.append("""<table class="FRA table table-bordered table-hover toggle-circle tablet breakpoint footable-loaded footable" cellspacing="0" summary="Server stats">""")
			#out.append("""	<tr class="info">""")
			#out.append("""		<th><a href="javascript:cs_change_range(0);">short rangeeee</a></th>""")
			#out.append("""		<th><a href="javascript:cs_change_range(1);">medium range</a></th>""")
			#out.append("""		<th><a href="javascript:cs_change_range(2);">long range</a></th>""")
			#out.append("""		<th><a href="javascript:cs_change_range(3);">very long range</a></th>""")
			#out.append("""	</tr>""")
			#out.append("""</table>""")
			#out.append("""<table class="FRA table table-bordered table-hover toggle-circle tablet breakpoint footable-loaded footable" cellspacing="0" summary="Server charts view">""")
			#for i in xrange(2):
			#	out.append("""	<tr>""")
			#	out.append("""		<td align="center" colspan="4">""")
			#	out.append("""			<div id="cs_desc%u">%s</div>""" % (i,charts[0][2]))
			#	out.append("""			<img src="chart.cgi?host=%s&amp;port=%s&amp;id=%u" width="1000" height="120" id="cs_chart%u" alt="chart" />""" % (cshost,csport,10*charts[0][0],i))
			#	out.append("""			<table class="BOTMENU" cellspacing="0" summary="Server stats menu">""")
			#	out.append("""				<tr>""")
			#	no=0
			#	cl="PR"
			#	for id,name,desc in charts:
			#		out.append("""					<td align="center" id="cs_cell_%u_%u" class="%s"><a href="javascript:cs_change_type(%u,%u);" title="%s">%s</a></td>""" % (i,no,cl,i,no,desc,name))
			#		cl="REL"
			#		no+=1
			#	out.append("""				</tr>""")
			#	out.append("""			</table>""")
			#	out.append("""		</td>""")
			#	out.append("""	</tr>""")
			#out.append("""</table>""")
		elif len(cchtmp)==1 and len(CCdata)>0:
			chid = 0
			for id,name,desc in charts:
				if name==CCdata:
					chid = id
			if chid==0:
				try:
					chid = int(CCdata)
				except Exception:
					pass
			if chid>0 and chid<1000:
				out.append("""<script type="text/javascript">""")
				out.append("""<!--//--><![CDATA[//><!--""")
				out.append("""	var i,j;""")
				out.append("""	var cs_chartid = new Array(0,0);""")
				out.append("""	var cs_range=0;""")
				out.append("""	var cs_imgs = new Array();""")
				out.append("""	var cs_vhosts = new Array(%s);""" % ','.join(['"%s"' % x[0] for x in servers]))
				out.append("""	var cs_vports = new Array(%s);""" % ','.join(['"%s"' % x[1] for x in servers]))
				out.append("""	var cs_inames = new Array(%s);""" % ','.join(['"%s"' % x[2] for x in servers]))
				out.append("""	for (i=0 ; i<cs_inames.length ; i++) {""")
				out.append("""		for (j=0 ; j<4 ; j++) {""")
				out.append("""			var vhost = cs_vhosts[i];""")
				out.append("""			var vport = cs_vports[i];""")
				out.append("""			var id = %d*10+j;""" % chid)
				out.append("""			cs_imgs[i*10+j] = new Image();""")
				out.append("""			cs_imgs[i*10+j].src = "chart.cgi?host="+vhost+"&amp;port="+vport+"&amp;id="+id;""")
				out.append("""		}""")
				out.append("""	}""")
				out.append("""	function cs_change(num) {""")
				out.append("""		for (i=0 ; i<cs_inames.length ; i++) {""")
				out.append("""			var name = "cs_"+cs_inames[i];""")
				out.append("""			document.images[name].src = cs_imgs[i*10+num].src;""")
				out.append("""		}""")
				out.append("""	}""")
				out.append("""//--><!]]>""")
				out.append("""</script>""")
				out.append("""<table id="nodispl" class="FRA table table-bordered table-hover toggle-circle tablet breakpoint footable-loaded footable" cellspacing="0" summary="Server stats">""")
				out.append("""	<tr class="info">""")
				out.append("""		<th><a href="javascript:cs_change(0);">short range</a></th>""")
				out.append("""		<th><a href="javascript:cs_change(1);">medium range</a></th>""")
				out.append("""		<th><a href="javascript:cs_change(2);">long range</a></th>""")
				out.append("""		<th><a href="javascript:cs_change(3);">very long range</a></th>""")
				out.append("""	</tr>""")
				for cshost,csport,name,desc in servers:
					out.append("""	<tr class="C2">""")
					out.append("""		<td align="center" colspan="4">""")
					out.append("""			%s:<br/>""" % (desc))
					out.append("""			<img src="chart.cgi?host=%s&amp;port=%s&amp;id=%u" width="1000" height="120" id="cs_%s" alt="%s" />""" % (cshost,csport,chid*10,name,name))
					out.append("""		</td>""")
					out.append("""	</tr>""")
				out.append("""</table>""")
				out.append("""			<span id="csvurl">chart.cgi?host=%s&amp;port=%s&amp;id=%u</span>""" % (cshost,csport,chid*10+90000))
				out.append("""<div id="clientshow"></div>""")
		print "\n".join(out)
	except Exception:
		print """<table class="FRA table table-bordered table-hover toggle-circle tablet breakpoint footable-loaded footable" cellspacing="0" summary="Exception">"""
		print """<tr><td align="left"><pre>"""
		traceback.print_exc(file=sys.stdout)
		print """</pre></td></tr>"""
		print """</table>"""

	print """<br/>"""

def print_file(name):
	f=open(name)
	for line in f:
		print line

if "HELP" in sectionset:
	# FIXME(kulek@lizardfs.org) - it should be in separate file help.html however we are waiting for CMAKE to make it happen.
	#print_file("/usr/share/mfscgi/help.html")
	print """please contact with help@lizardfs.com"""
	print """<br/>"""



print """</div> <!-- end of container -->"""
print """<script src="js/mfs.js"></script>"""
print """</body>"""
print """</html>"""
