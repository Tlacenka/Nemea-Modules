#!/usr/bin/python
#
# Copyright (C) 2013-2016 CESNET
#
# LICENSE TERMS
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
# 3. Neither the name of the Company nor the names of its contributors
#    may be used to endorse or promote products derived from this
#    software without specific prior written permission.
#
# ALTERNATIVELY, provided that this notice is retained in full, this
# product may be distributed under the terms of the GNU General Public
# License (GPL) version 2 or later, in which case the provisions
# of the GPL apply INSTEAD OF those given above.
#
# This software is provided ``as is'', and any express or implied
# warranties, including, but not limited to, the implied warranties of
# merchantability and fitness for a particular purpose are disclaimed.
# In no event shall the company or contributors be liable for any
# direct, indirect, incidental, special, exemplary, or consequential
# damages (including, but not limited to, procurement of substitute
# goods or services; loss of use, data, or profits; or business
# interruption) however caused and on any theory of liability, whether
# in contract, strict liability, or tort (including negligence or
# otherwise) arising in any way out of the use of this software, even
# if advised of the possibility of such damage.

import sys
import os.path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "python"))
import trap
import unirec
from optparse import OptionParser

import smtplib
import email
import time

""""
Email reporter module

TODO:
- print warning if template contains invalid references
"""


module_info = trap.CreateModuleInfo(
   "Email reporter", # Module name
"""\
Each UniRec record received is transformed to an email of specified 
template and send to specified address.

Usage:
   python email_reporter.py -i "ifc_spec" [options] CONFIG_FILE 

Parameters:
   CONFIG_FILE    File with configuration. It should contain information about 
                  SMTP server to connect to and a template of the message.
                  Format of this file is given below.
   -d, --dry-run  Dry-run mode - nothing is sent, messages are printed to 
                  stdout instead.
   --skip-smtp-test  By default, the module tries to connect to specified SMTP 
                     server on startup to check that the connection (and login
                     credentials, if specified) works. You can skip the test 
                     using this option.
"""
#   --limit=N  Set maximal number of emails sent per hour. If more records arrive on input,...
"""\

The config file has two sections. First, there is specification of required 
UniRec fields, SMTP server to be used, optionally login credentials and so on.
Format of this section is given by example below. You can use comments (start
them with '#') in this section. 

The second section starts after a blank line and it contains template of
an email message in RFC2822 format. That is: headers (e.g. From, To, Subject),
blank line and message body. The "Date:" header is added automatically.
The template may contain references to fields of UniRec record which will be 
substituted by corresponding values in each message. References are made using
'$' followed by name of the field.

An example of config file:
  unirec=ipaddr SRC_IP,ipaddr DST_IP,string FILENAME,time TIMESTAMP
  server=smtp.example.com
  port=25  # optional, default: 25
  starttls=1 # optional, default: 0
  login=username:password  # optional, default: no login

  From: NEMEA <nemea@example.com>
  To: Main Recipient <recipient1@example.com>
  Cc: <recipient2@example.com>
  Bcc: <recipient4@example.com>
  Subject: [Nemea-alert] $SRC_IP sent a picture of cat

  NEMEA system has detected a picture of cat being sent over the internet.
  Details:
    Source:            $SRC_IP
    Destination:       $DST_IP
    File name:         $FILENAME
    Time of detection: $TIMESTAMP
  -----
  This is automatically generated email, don't reply.
  You can contact Nemea administrators at nobody@example.com.
""",
   1, # Number of input interfaces
   0  # Number of output interfaces
)

# A message to send when a limit on number of messages per hour is reached
EMERGENCY_STOP_SUBJECT = "[Nemea] EMERGENCY STOP"
EMERGENCY_STOP_MESSAGE = """\
Nemea EmailReporter has sent more than a defined maximal number of messages 
during the last hour. Further messages will be supressed in order to not flood
your inbox.

This is not a normal situation. Something probably went wrong and some module 
in the Nemea system started to send messages much more often than expected.
Please contact Nemea administrators to solve this problem.
"""

def is_over_msg_per_hour_limit():
   """Check whether we would reach a limit by sending another message now."""
   global message_send_times
   if max_msg_per_hour <= 0:
      return False # Limit is disabled
   
   now = time.time()
   # Remove messages older than one hour from message_send_times
   message_send_times = [t for t in message_send_times if t > now-3600]
   # Check number of messages sent during last hour
   if len(message_send_times) >= max_msg_per_hour:
      return True
   # Add current time to message_send_times
   message_send_times.append(now)
   return False



# ********** Parse parameters **********
# TODO: Help should be generated by OptionParser (or better ArgParse)
parser = OptionParser()
parser.add_option("-d", "--dry-run", action="store_true")
parser.add_option("--skip-smtp-test", action="store_true")
parser.add_option("--limit", metavar="N", type=int, default=20)

# Extract TRAP parameters
try:
   ifc_spec = trap.parseParams(sys.argv, module_info)
except trap.EBadParams, e:
   if "Interface specifier (option -i) not found." in str(e):
      print 'Usage:\n   python email_reporter.py -i "ifc_spec" [options] CONFIG_FILE'
      exit(1)
   else:
      raise e

# Parse the other parameters
opt, args = parser.parse_args()

if len(args) != 1:
   print 'Usage:\n   python email_reporter.py -i "ifc_spec" [options] CONFIG_FILE'
   exit(1) 

config_file = args[0]

max_msg_per_hour = opt.limit # Maximal number of messages sent per hour
message_send_times = [] # Times when messages were sent during last hour
supress_messages = False # Whether to supress all messages (set to True when limit is reached)

# ********** Initialize module **********
trap.init(module_info, ifc_spec)
trap.registerDefaultSignalHandler()

# Defaults
unirecfmt = None
server = None
port = 25
starttls = False
login = None

# ********** Parse config file **********
config, msg_header, msg_body = open(config_file, "r").read().split("\n\n", 2)

for i,line in enumerate(config.splitlines()):
   # Cut off comments and leading/trailing whitespaces
   line = line.partition('#')[0].strip() # FIXME: in this way, password can't contain '#'
   if line == "":
      continue

   var,_,val = line.partition('=')
   if val == "":
      print >> sys.stderr, 'Error in config file (line %i): Each line in first section must have format "varibale=value".' % i
      exit(1)
   var = var.strip()
   val = val.strip()

   if var == "unirec":
      unirecfmt = val
   elif var == "server":
      server = val
   elif var == "port":
      port = int(val)
   elif var == "starttls":
      starttls = (val == "1" or val.lower() == "true")
   elif var == "login":
      login = val.partition(':')
      login = (login[0], login[2])
   else:
      print >> sys.stderr, 'Error in config file (line %i): Unknown variable "%s".' % (i,var)
      exit(1)

if unirecfmt is None:
   print >> sys.stderr, 'Error in config file: UniRec template must be set ("unirec=..." not found).'
   exit(1)
if server is None:
   print >> sys.stderr, 'Error in config file: SMTP server must be set ("server=..." not found).'
   exit(1)


# Set required input format
trap.set_required_fmt(0, trap.TRAP_FMT_UNIREC, unirecfmt)

# Create UniRec template containing required fields
UniRecType = unirec.CreateTemplate("UniRecType", unirecfmt)

# ********** Parse email template **********
sender = None
recipients = []

headers = email.message_from_string(msg_header)

# Find sender address
if 'from' in headers:
   sender = headers['from']
else:
   print >> sys.stderr, 'Error in message template: "From:" header not found.'
   exit(1)

# Find all recipients
recipients.extend(headers.get_all('to', []))
recipients.extend(headers.get_all('cc', []))
recipients.extend(headers.get_all('bcc', []))
if len(recipients) == 0:
   print >> sys.stderr, 'Error in message template: No recipient (headers "To:", "Cc:" or "Bcc:") found.'
   exit(1)

# Remove Bcc headers
del headers['bcc']

# Add Date header
headers.add_header("Date", "$_DATETIME_") # $_DATETIME_ will be replaced by current date-time before a message is sent


if trap.getVerboseLevel() >= 0:
   print "Information parsed from config:"
   print "  UniRec template:", repr(unirecfmt)
   print "  SMTP server address:", repr(server)
   print "  SMTP server port:", repr(port)
   print "  Use STARTTLS:", repr(starttls)
   print "  Login credentials:", repr(login)
   print "  Sender:", repr(sender)
   print "  Recipients:", repr(recipients)


msg_template = headers.as_string() + msg_body

msg_template = msg_template.replace("%", "%%")
# Get names of all UniRec fields in the template and sort them from the longest
# to shortest (to solve a problem when there are fields ABC and ABCD and we 
# should substitute $ABCD)
fields = UniRecType.fields()
fields.sort(lambda a,b: cmp(len(a),len(b)), reverse=True)
fields.append('_DATETIME_')
# Substitute all occurences of '$FIELD_NAME' by '%(FIELD_NAME)s'
for f in fields:
   msg_template = msg_template.replace("$"+f, "%("+f+")s")


if trap.getVerboseLevel() >= 0:
   print fields
   print "Message template:"
   print msg_template
   print "--------------------"

# ********** Test connection to the server **********
if not opt.skip_smtp_test and not opt.dry_run:
   s = smtplib.SMTP()
   if trap.getVerboseLevel() >= 0:
      s.set_debuglevel(True)
      print "Trying to connect to the server..."
   try:
      s.connect(server, port)
   except smtplib.socket.error, e:
      print >> sys.stderr, "Error when trying to connect to '%s:%i':" % (server, port)
      print >> sys.stderr, e
      exit(1)
   if starttls:
      s.starttls()
   if login:
      s.login(login[0], login[1])
   s.quit()
   if trap.getVerboseLevel() >= 0:
      print "--------------------"




# ********** Main loop **********
while not trap.stop:
   # *** Read data from input interface ***
   try:
      data = trap.recv(0)
   except trap.EFMTMismatch:
      sys.stderr.write("Error: input data format mismatch\n")
      break
   except trap.EFMTChanged as e:
      # TODO: This should be handled by trap.recv transparently
      # Get negotiated input data format
      (_, fmtspec) = trap.get_data_fmt(trap.IFC_INPUT, 0)
      if trap.getVerboseLevel() >= 0:
         print "New UniRec template:", fmtspec
      UniRecType = unirec.CreateTemplate("UniRecType", fmtspec)
      data = e.data
   except trap.ETerminated:
      break

   # Check for "end-of-stream" record
   if len(data) <= 1:
      if trap.getVerboseLevel() >= 0:
         print "EOS received, exitting."
      break

   # Convert data to UniRec
   rec = UniRecType(data)

   # *** Prepare email body ***
   unirec_dict = rec.todict()
   unirec_dict['_DATETIME_'] = time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime())
   message = msg_template % unirec_dict


   # *** Send email ***
   if not opt.dry_run:
      s = smtplib.SMTP()
      if trap.getVerboseLevel() >= 0:
         s.set_debuglevel(True)
      try:
         s.connect(server, port)
      except smtplib.socket.error, e:
         print >> sys.stderr, "Error when trying to connect to '%s:%i':" % (server, port)
         print >> sys.stderr, e
         exit(1)
      if starttls:
         s.starttls()
      if login:
         s.login(login[0], login[1])
      s.sendmail(sender, recipients, message)
      s.quit()
   else:
      print "-----------------------------------------------------------------------"
      print "TIME:", time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())
      print "FROM:", sender
      print "RECIPIENTS:", ', '.join(recipients)
      print "              ----- MESSAGE STARTS ON THE NEXT LINE -----              "
      print message

