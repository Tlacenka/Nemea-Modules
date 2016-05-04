#!/usr/bin/python
#coding=UTF-8

## @package html_server
#  Web server for visualising bitmaps in form of images.
#  Author: Katerina Pilatova <xpilat05@stud.fit.vutbr.cz>
#  Date: 2016
#

# Copyright (C) 2016 CESNET
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
#

from __future__ import print_function, division, with_statement

import argparse
import base64
from bitarray import bitarray
from bs4 import BeautifulSoup # https://www.crummy.com/software/BeautifulSoup/
import cgi
import copy
import datetime
import ipaddress
import logging
import math
import os
import signal
import time
import activity_visualisation
import yaml # pyyaml
import sys

# Python 2.x BaseHTTPServer is in http.server in Python 3.x
# Python 2.x PIL.Image is in Image in Python 3.x
if sys.version_info[0] == 2:
   from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
else:
   from http.server import BaseHTTPRequestHandler, HTTPServer

MAX_WINDOW = 1000
MAX_VECTOR_SIZE = 1000

SRC = 0
DST = 1
SRC_DST = 2

# SIGTERM
def sigterm_handler(signal, frame):
    sys.exit(0)


def create_handler(args, handler):

   # Create additional attributes and methods in handler
   class My_RequestHandler(BaseHTTPRequestHandler):
   
      arguments = args
      visualisation_handler = handler
   
      def do_GET(self):
         ''' Handle a HTTP GET request. '''

         # Check if mode is online
         if self.visualisation_handler.mode == 'online':
            # Check if config file has "end"
            try:
               with open(self.arguments['dir'] + '/' + self.arguments['config'], 'r+') as fd:
                  config_file = yaml.load(fd.read())
                  if config_file is None:
                     print('File ' + self.arguments['dir'] + '/' + self.arguments['config'] + ' failed.', file=sys.stderr)
                     sys.exit(1)
                  elif (('end' in config_file[self.arguments['filename']]['module']) and
                        ('intervals' in config_file[self.arguments['filename']]['time'])):
                     self.visualisation_handler.mode = 'offline'
                     self.visualisation_handler.intervals = config_file[self.arguments['filename']]['time']['intervals']
                     
            except IOError:
               print('File ' + self.arguments['dir'] + '/' + self.arguments['config'] + ' could not be opened.', file=sys.stderr)
               sys.exit(1)
            
   
         if (self.path == '/') or (self.path == '/index.html') or (self.path == '/frontend.html'):
   
            # Load source bitmap
            #self.visualisation_handler.original_bitmap = self.visualisation_handler.binary_read(self.arguments['filename'] + '_s.bmap')
            #for b in range(self.visualisation_handler.bit_vector_size):
            #   print(self.visualisation_handler.original_bitmap[b])
            #self.visualisation_handler.create_image(self.visualisation_handler.original_bitmap, "image_s")
   
            # Open main HTML file
            try:
               with open('frontend.html', 'r') as fd:
                  self.send_response(200)
                  self.send_header('Content-type', 'text/html')
                  self.end_headers()
   
                  # Find block for characteristics
                  html_file = BeautifulSoup(fd.read(), 'html.parser')
   
                  # Insert characteristics
                  html_file.find('td', 'subnet_size').append("/" + str(self.visualisation_handler.ip_granularity))
                  html_file.find('td', 'range').append(str(self.visualisation_handler.first_ip) + " - " + str(self.visualisation_handler.last_ip))
                  html_file.find('td', 'int_range').append(str(self.visualisation_handler.intervals) + " intervals")
                  html_file.find('td', 'time_interval').append(str(self.visualisation_handler.time_granularity) + " seconds")
                  html_file.find('td', 'time_window').append(str(self.visualisation_handler.time_window) + " intervals")
                  html_file.find('td', 'mode').append(self.visualisation_handler.mode)
   
                  #new_node = html_file.new_tag('td', src='image_s.png')
                  #html_node.append(new_node)
   
                  self.wfile.write(html_file)
                  
            except IOError:
               print('File ' + self.arguments['dir'] + self.path + ' could not be opened.', file=sys.stderr)
               self.send_response(404)
               sys.exit(1)
   
         # Get rid of favicon requests
         elif self.path == '/favicon.ico':
            self.send_response(200)
            self.send_header('Content-type', 'image/x-icon')
            self.end_headers()
   
         else:
            print('GET ' + self.path)
   
            # Parse URL self.arguments
            query = None
            index = self.path.find('?')
            if index >= 0:
               query = cgi.parse_qs(self.path[index+1:])
               self.path = self.path[:index]
   
               # If bitmap update required, update
               if 'update' in query:
                  # Find out bitmap type (filename_<type>.bmap)
                  bmap_type = self.path.split('_')[1].split('.')[0]
                  self.visualisation_handler.original_bitmap = self.visualisation_handler.binary_read(
                                        self.arguments['dir'] + '/' +
                                        self.arguments['filename'] + '_' +
                                        bmap_type + '.bmap')
                  if self.visualisation_handler.original_bitmap is not None:
                     self.visualisation_handler.create_image(self.visualisation_handler.original_bitmap, 'image_' + bmap_type)
   
               # If IP index is required
               if (('calculate_index' in query) and ('bitmap_type' in query) and
                   ('first_ip' in query) and ('ip_index' in query) and
                   ('interval' in query) and ('granularity' in query)):
   
                  # Get IPs and subnet
                  tmp_ip = query['first_ip'][0]
                  tmp_granularity = int(query['granularity'][0])
                  tmp_index = int(query['ip_index'][0])
                  bitmap_type = query['bitmap_type'][0]
                  tmp_ip = self.visualisation_handler.get_ip_from_index(tmp_ip, tmp_index, tmp_granularity)
   
                  # Get colour at coordinates
                  x = tmp_index
                  y = int(query['interval'][0])
   
                  tmp_bitmap = (self.visualisation_handler.original_bitmap if (bitmap_type == 'origin')
                                else self.visualisation_handler.selected_bitmap)
   
                  # Decrease to avoid overflow
                  if x >= len(tmp_bitmap):
                     x = len(tmp_bitmap) - 1
                  if y >= len(tmp_bitmap[0]):
                     y = len(tmp_bitmap[0]) - 1
                  colour = ("white" if ((tmp_bitmap is not None) and tmp_bitmap[x][y]) else "black")
   
                  # Send needed information
                  self.send_response(200)
                  self.send_header('Content-type', 'text/plain')
                  self.send_header('IP_index', tmp_ip)
                  self.send_header('Cell_colour', colour)
                  self.end_headers()
                  return
   
               # If selected area is required
               if (('select_area' in query) and ('bitmap_type' in query) and
                   ('subnet_size' in query) and ('first_ip' in query) and
                   ('last_ip' in query) and ('first_int' in query) and
                   ('last_int' in query) and ('time_interval' in query)):
   
                  # Edit bitmap
                  self.visualisation_handler.edit_bitmap(query)
                  if self.visualisation_handler.selected_bitmap is not None:
                     self.visualisation_handler.create_image(self.visualisation_handler.selected_bitmap, 'selected')
                     # Set path to selected image
                     self.path = '/images/selected.png' # TODO will it be changed?
   
            print('PATH ' + self.path)
   
            open_mode = 'r'
   
            # Detect type
            if self.path.endswith(".html"):
               content_type = 'text/html'
            elif self.path.endswith(".png"):
               content_type = 'image/png'
               open_mode = 'rb'
            elif self.path.endswith(".js"):
               content_type = 'application/javascript'
            elif self.path.endswith(".css"):
               content_type = 'text/css'
            else:
               print("Path " + self.path + " was not recognized.", file=sys.stderr)
               self.send_response(404)
               sys.exit(1)
   
            # If bitmaps do not exist
            if ((query is not None) and
                ((('update' in query) and (self.visualisation_handler.original_bitmap is None)) or
                 (('selected_area' in query) and (self.visualisation_handler.selected_bitmap is None)))):
               self.send_response(200)
               self.send_header('Content-type', 'text/plain')
               self.send_header('Bitmap', 'none')
               self.end_headers()
            else:
               # Send appropriate file if exists
               try:
                  with open('.' + self.path, open_mode) as fd:
                     self.send_response(200)
                     self.send_header('Content-type', content_type)
   
                     # Send updated interval range and mode
                     if (query is not None) and ('update' in query):
                        self.send_header('Interval_range',
                                        str(len(self.visualisation_handler.original_bitmap[0]) if (
                                       (self.visualisation_handler.original_bitmap is not None) and (len(self.visualisation_handler.original_bitmap) > 0)) else 0))
                        self.send_header('Mode', self.visualisation_handler.mode)
                        print (self.visualisation_handler.mode)
   
                     # If image is sent via AJAX, encode to base64
                     if ((content_type == 'image/png') and (query is not None) and
                        (('update' in query) or ('select_area' in query))):
                        self.send_header('Bitmap', 'ok')
                        self.end_headers()
                        self.wfile.write(base64.b64encode(fd.read()))
                     else:
                        self.end_headers()
                        self.wfile.write(fd.read())
   
               except IOError:
                  print('File .' + self.path + ' could not be opened.', file=sys.stderr)
                  self.send_response(404)
                  sys.exit(1)

   return My_RequestHandler

def main():
   ''' Main function for the lifecycle of the server. '''

   # Parse self.arguments
   parser = argparse.ArgumentParser()
   parser.add_argument('-p', '--port', type=int, default=8080,
                       help='Server port, (8080 by default)')
   parser.add_argument('-H', '--hostname', type=str, default='localhost',
                       help='Server hostname (localhost by default).')
   parser.add_argument('-d', '--dir', type=str, default='.',
                       help='Path to directory with bitmaps and configuration file (current directory by default).')
   parser.add_argument('-c', '--config', type=str, default='config.yaml',
                       help='Path to configuration file (current directory by default).')
   parser.add_argument('-f', '--filename', type=str, default='bitmap',
                       help='Filename of bitmap storage files (bitmap by default).')
   arguments = vars(parser.parse_args())

   # Check their validity
   if not os.path.isfile(arguments['config']):
      print('Configuration file does not exist.', file=sys.stderr)
      sys.exit(1)

   if not os.path.isdir(arguments['dir']):
      print('Directory for web client files does not exist.', file=sys.stderr)
      sys.exit(1)

   if (arguments['port'] > 65535) or (arguments['port'] < 1): # Skip registered?
      print('Port not within allowed range.', file=sys.stderr)
      sys.exit(1)

   # Validate configuration file, create values
   visualisation_handler = activity_visualisation.Visualisation_Handler()
   visualisation_handler.load_config(arguments['dir'], arguments['filename'], arguments['config'])

   # Create handler
   server = HTTPServer((arguments['hostname'], arguments['port']),create_handler(arguments, visualisation_handler))

   # Set SIGTERM handler
   signal.signal(signal.SIGTERM, sigterm_handler)

   print("Starting server")

   # Serve forever
   try:
      server.serve_forever()
   except KeyboardInterrupt:
      pass

   # Close server
   server.server_close()


if __name__ == '__main__':
   main()
