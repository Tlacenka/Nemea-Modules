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
from bitarray import bitarray
import cgi
import ipaddress
import logging
import math
import os
import yaml # pyyaml
import sys

# Python 2.x BaseHTTPServer is in http.server in Python 3.x
if sys.version_info[0] == 2:
   from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
else:
   from http.server import BaseHTTPRequestHandler, HTTPServer

MAX_WINDOW = 1000
MAX_VECTOR_SIZE = 1000

SRC = 0
DST = 1
SRC_DST = 2


def create_request_handler(args):
   ''' Creates class for handling requests, adds needed variables '''

   # Read configuration file
   try:
      with open(args['config'], 'r') as fd:
         config_file = yaml.load(fd.read())
   except IOError:
      print('File ' + args['config'] + ' could not be opened.')
      sys.exit(1)

   # Check if node with filename exists:
   if args['filename'] not in config_file:
      print('Bitmap files not found.', file=sys.stderr)
      sys.exit(1) 

   # Check if node contains required keys
   if (not(set(['time', 'addresses'])<= set(config_file[args['filename']].keys())) or
      not(set(['first', 'last', 'granularity']) <= set(config_file[args['filename']]['addresses'].keys())) or
      not(set(['granularity', 'intervals']) <= set(config_file[args['filename']]['time'].keys()))):
      print('Configuration file structure is invalid.', file=sys.stderr)

   # Get IPs
   first_ipaddr = None
   last_ipaddr = None
   if sys.version_info[0] == 2:
      first_ipaddr = ipaddress.ip_address(unicode(config_file[args['filename']]['addresses']['first'],
                                                  "utf-8"))
      last_ipaddr = ipaddress.ip_address(unicode(config_file[args['filename']]['addresses']['last'],
                                                 "utf-8"))

   else:
      first_ipaddr = ipaddress.ip_address(config_file[args['filename']]['addresses']['first'])

      last_ipaddr = ipaddress.ip_address(config_file[args['filename']]['addresses']['last'])

   ip_granularity = int(config_file[args['filename']]['addresses']['granularity'])

   # Adjust IPs to granularity
   ip_size = first_ipaddr.max_prefixlen
   shifted_first = ipaddress.ip_address((int(first_ipaddr) >> (ip_size - ip_granularity)))
   shifted_last = ipaddress.ip_address((int(last_ipaddr) >> (ip_size - ip_granularity)))

   # Get vector size
   vector_size = int(shifted_first) - int(shifted_last)

   # Get time window
   window = int(config_file[args['filename']]['time']['intervals'])

   # Create empty bitmaps
   bitmap_src = {}
   for i in range(vector_size):
      bitmap_s[i] = bitarray()

   bitmap_dst = {}
   for i in range(vector_size):
      bitmap_dst[i] = bitarray()

   bitmap_srcdst = {}
   for i in range(vector_size):
      bitmap_srcdst[i] = bitarray()

   # Create additional attributes and methods in handler
   class My_RequestHandler(BaseHTTPRequestHandler):

      # Input information
      arguments = args

      # IPs + subnet size
      first_ip = first_ipaddr
      last_ip = last_ipaddr
      granularity = ip_granularity

      # Size of bit vectors (rows) in file [b]
      bit_vector_size = vector_size
      byte_vector_size = int(math.ceil(bit_vector_size / 8))

      # Time unit and window size
      time_interval = int(config_file[args['filename']]['time']['granularity'])
      time_window = window
      
      # Bitmaps
      bitmap_s = bitmap_src
      bitmap_d = bitmap_dst
      bitmap_sd = bitmap_srcdst

      def binary_read(self, filename):
         ''' Returns 2D bitarray of updated, transposed bitmap '''

         filesize = os.path.getsize(filename)
         rows = filesize / byte_vector_size

         # Temporary bitmap for rows vectors
         tmp_bitmap = {}
         for i in range(rows):
            tmp_bitmap[i] = bitarray()


         # Reads file row by row (by intervals), fill tmp_bitmap
         # 1 row == the whole address space in 1 time interval
         try:
            with open(filename, 'rb') as fd:
               for r in range(rows):
                     byte_vector = fd.read(byte_vector_size)
                     tmp_bitmap[r].frombytes(byte_vector)

         except IOError:
            print('File ' + args['config'] + ' could not be opened.')
            sys.exit(1)

         # Remove padding from the end of the vector if needed
         trim_size = 8-(bit_vector_size % 8)
         if trim_size < 8:
            for r in range(rows):
               tmp_bitmap[r] = tmp_bitmap[r][:-trim]

         # Transpose bitmap
         # 1 row == 1 IP in all intervals
         transp_bitmap = {}
         for i in range(bit_vector_size):
            transp_bitmap[i] = bitarray()

         # Go through intervals in tmp_bitmap, append to transposed
         for r in range(rows):
            for b in range(bit_vector_size):
               transp_bitmap[b].append(tmp_bitmap[r][b])

         return transp_bitmap
   
      def do_GET(self):
         ''' Handle a HTTP GET request. '''

         print('GET ' + self.path)
   
         # Parse URL arguments
         index = self.path.find('?')
   
         if index >= 0:
            get_path = self.path[:index]
            query = cgi.parse_qs(self.path[index+1:])
   
         # Print out logging information about the path and args.
         if 'content-type' in self.headers:
            ctype, _ = cgi.parse_header(self.headers['content-type'])
            print('TYPE ' + ctype)
   
         print('PATH ' + self.path)

         if self.path == "/":

            self.send_response(200)  # OK
            self.send_header('Content-type', 'text/html')
            self.end_headers()

            try:
               with open(args['dir'] + self.path + 'frontend.html', 'r') as fd:
                  self.send_response(200)
                  self.send_header('Content-type', 'text/html')
                  self.end_headers()

                  self.wfile.write(fd.read())
            except IOError:
               print('File ' + args['dir'] + self.path + ' could not be opened.', file=sys.stderr)
               self.send_response(404)
               sys.exit(1)

         else:
            self.send_response(200)  # OK
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            try:
               with open(args['dir'] + self.path, 'r') as fd:
                  self.send_response(200)
                  self.send_header('Content-type', 'text/html')
                  self.end_headers()

                  self.wfile.write(fd.read())
            except IOError:
               print('File ' + args['dir'] + self.path + ' could not be opened.', file=sys.stderr)
               self.send_response(404)
               sys.exit(1)
            

   return My_RequestHandler

def main():
   ''' Main function for the lifecycle of the server. '''

   # Parse arguments
   parser = argparse.ArgumentParser()
   parser.add_argument('-i', '--input', action='store_true', help='Fetch input bitmap.')
   parser.add_argument('-o', '--output', action='store_true', help='Fetch output bitmap.')
   parser.add_argument('-b', '--bidirectional', action='store_true', help='Fetch bidirectional (io) bitmap.')
   parser.add_argument('-a', '--all', action='store_true', help='Fetch all types of bitmaps.')
   parser.add_argument('-p', '--port', type=int, default=8080,
                       help='Server port, (8080 by default)')
   parser.add_argument('-H', '--hostname', type=str, default='localhost',
                       help='Server hostname (localhost by default).')
   parser.add_argument('-d', '--dir', type=str, default='.',
                       help='Path to directory with web client files (HTML, CSS, JS) (current directory by default).')
   parser.add_argument('-c', '--config', type=str, default='.', required=True,
                       help='Path to configuration file (current directory by default).')
   parser.add_argument('-f', '--filename', type=str, default='bitmap', required=False,
                       help='Filename of bitmap storage files (bitmap by default).')
   args = vars(parser.parse_args())

   # Check their validity
   if not os.path.isfile(args['config']):
      print('Configuration file does not exist.', file=sys.stderr)
      sys.exit(1)

   if not os.path.isdir(args['dir']):
      print('Directory for web client files does not exist.', file=sys.stderr)
      sys.exit(1)

   if (args['port'] > 65535) or (args['port'] < 1): # Skip registered?
      print('Port not within allowed range.', file=sys.stderr)
      sys.exit(1)

   # Create the server
   ip_activity_RequestHandler = create_request_handler(args)

   server = HTTPServer((args['hostname'], args['port']), ip_activity_RequestHandler)

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
