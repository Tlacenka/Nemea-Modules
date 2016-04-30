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
import ipaddress
import logging
import math
import os
from PIL import Image # Pillow needed for compatibility
import signal
import struct
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

# Global variables
# IP variables
g_first_ip = None
g_last_ip = None
g_ip_size = 0
g_granularity = 0
g_bit_vector_size = 0
g_byte_vector_size = 0

#Time variables
g_time_interval = 0
g_time_window = 0


#Bitmaps
g_bitmap = None

# Selected area
g_selected_first_ip = None
g_selected_last_ip = None
g_selected_bit_vector_size = 0

g_selected_granularity = 0
g_selected_first_int = 0
g_selected_last_int = 0
g_selected_time_interval = 0

g_selected_bitmap = None

def get_ip_from_index(first_ip, index, granularity):
   ''' Calculates IP at index from first_ip considering granularity
       Handles IPs as strings '''
   global g_ip_size

   # Shift IP, increment and shift back
   # Expicitly state IPv6:
   # > Python implicitly converts to IPv4 if the value fits in 32 bits
   if sys.version_info[0] == 2:
      if g_ip_size == 128:
         ip = ipaddress.IPv6Address(unicode(first_ip, "utf-8"))
      else:
         ip = ipaddress.ip_address(unicode(first_ip, "utf-8"))
   else:
      if g_ip_size == 128:
         ip = ipaddress.IPv6Address(first_ip)
      else:
         ip = ipaddress.ip_address(first_ip)

   if g_ip_size == 128:
      ip = ipaddress.IPv6Address((int(ip) >> (g_ip_size- granularity)))
   else:
      ip = ipaddress.ip_address((int(ip) >> (g_ip_size - granularity)))

   ip += index
   
   if g_ip_size == 128:
      ip = ipaddress.IPv6Address((int(ip) << (g_ip_size - granularity)))
   else:
      ip = ipaddress.ip_address((int(ip) << (g_ip_size - granularity)))


   return str(ip)

def get_index_from_ip(first_ip, curr_ip, granularity):
   ''' Calculates offset from first ip to current one (passed as strings) '''
   global g_ip_size

   # Get IPs
   if sys.version_info[0] == 2:
      if g_ip_size == 128:
         ip1 = ipaddress.IPv6Address(unicode(first_ip, "utf-8"))
         ip2 = ipaddress.IPv6Address(unicode(curr_ip, "utf-8"))
      else:
         ip1 = ipaddress.ip_address(unicode(first_ip, "utf-8"))
         ip2 = ipaddress.ip_address(unicode(curr_ip, "utf-8"))
   else:
      if g_ip_size == 128: 
         ip1 = ipaddress.IPv6Address(first_ip)
         ip2 = ipaddress.IPv6Address(curr_ip)
      else:
         ip1 = ipaddress.ip_address(first_ip)
         ip2 = ipaddress.ip_address(curr_ip)

   # Adjust IPs to granularity, shift
   shift = ip1.max_prefixlen - granularity

   shifted_1 = ipaddress.ip_address(int(ip1) >> shift)
   shifted_2 = ipaddress.ip_address(int(ip2) >> shift)

   # Get index
   return int(shifted_2) - int(shifted_1)

# SIGTERM
def sigterm_handler(signal, frame):
    sys.exit(0)

def create_request_handler(args):
   ''' Creates class for handling requests'''

   # Create additional attributes and methods in handler
   class My_RequestHandler(BaseHTTPRequestHandler):

      arguments = args # Input information

      def binary_read(self, filename):
         ''' Returns 2D bitarray of updated, transposed bitmap '''
         global g_byte_vector_size, g_bit_vector_size
         # xxd [[-b] bitmap_name

         filesize = os.path.getsize(self.arguments['dir'] + '/' + filename)
         rows = int(filesize / g_byte_vector_size)

         # Temporary bitmap for rows vectors
         tmp_bitmap = {}
         for i in range(rows):
            tmp_bitmap[i] = bitarray()


         # Reads file row by row (by intervals), fill tmp_bitmap
         # 1 row == the whole address space in 1 time interval
         try:
            with open(self.arguments['dir'] + '/' + filename, 'rb') as fd:
               for r in range(rows):
                  byte_vector = fd.read(g_byte_vector_size)
                  tmp_bitmap[r].frombytes(byte_vector)

         except IOError:
            print('File ' + self.arguments['dir'] + '/' + filename + ' could not be opened.')
            sys.exit(1)

         # Remove padding from the end of the vector if needed
         trim_size = 8-(g_bit_vector_size % 8)
         if trim_size < 8:
            for r in range(rows):
               tmp_bitmap[r] = tmp_bitmap[r][:-trim_size]

         # Transpose bitmap
         # 1 row == 1 IP in all intervals
         transp_bitmap = {}

         for i in range(g_bit_vector_size):
            transp_bitmap[i] = bitarray()

         # Go through intervals in tmp_bitmap, append to transposed
         for r in range(rows):
            for b in range(g_bit_vector_size):
               transp_bitmap[b].append(tmp_bitmap[r][b])

         return transp_bitmap

      def create_image(self, bitmap, filename):
         ''' Create black and white image from bitmap '''
         # http://stackoverflow.com/questions/5672756/binary-list-to-png-in-python

         # Size of the image:
         # height = address space, width = intervals in bitmap
         height = len(list(bitmap))
         width = len(bitmap[0])
         print ('Creating image', height,'x', width)

         # Save bitmap to buffer
         img_buffer = []
         for r in reversed(range(height)):
            for b in range(width):
               img_buffer.append(bitmap[r][b])
            #print(bitmap[r])

         # Create and save image
         img_data = struct.pack('B'*len(img_buffer), *[p*255 for p in img_buffer])
         image = Image.frombuffer('L', (width, height), img_data)
         image.save(self.arguments['dir'] + '/images/' + filename + '.png')
         return

      def edit_bitmap(self, query):
         ''' Can involve selecting area, changing size '''
         global g_bitmap, g_selected_bitmap, g_first_ip
         global g_selected_first_ip, g_selected_last_ip, g_selected_bit_vector_size

         tmp_bitmap = copy.deepcopy(g_bitmap)

         # Do magic here
         print ('Editing bitmap')

         # Save selected IP range
         if sys.version_info[0] == 2:
            g_selected_first_ip = ipaddress.ip_address(unicode(query['first_ip'][0], "utf-8"))
            g_selected_last_ip = ipaddress.ip_address(unicode(query['last_ip'][0], "utf-8"))
         else:
            g_selected_first_ip = ipaddress.ip_address(query['first_ip'][0])
            g_selected_last_ip = ipaddress.ip_address(query['last_ip'][0])
      

         # Adjust IP range (deleting rows)
         ip1_index = get_index_from_ip(str(g_first_ip), query['first_ip'][0], int(query['subnet_size'][0]))
         ip2_index = get_index_from_ip(str(g_first_ip), query['last_ip'][0], int(query['subnet_size'][0]))
         
         # Save IP range length
         g_selected_bit_vector_size = ip2_index - ip1_index

         # Move bitmap [ip1_index - ip2_index] to [0 - g_selected_bit_vector_size]
         for i in range(ip1_index, ip2_index):
            tmp_bitmap[i-ip1_index] = tmp_bitmap[i]

         # Delete the rest
         for i in range(g_selected_bit_vector_size, len(g_bitmap)):
            del tmp_bitmap[i]

         # Adjust Interval range (deleting columns)

         # Save interval range
         g_selected_first_int = int(query['first_int'][0])
         g_selected_last_int = int(query['last_int'][0])

         # Delete intervals out of range from rows
         for r in range(g_selected_bit_vector_size):
            tmp_bitmap[r] = tmp_bitmap[r][g_selected_first_int:g_selected_last_int]

         g_selected_bitmap = tmp_bitmap

      def do_GET(self):
         ''' Handle a HTTP GET request. '''
         global g_granularity, g_first_ip, g_last_ip, g_time_interval
         global g_time_window, g_bitmap, g_selected_bitmap

         if (self.path == '/') or (self.path == '/index.html') or (self.path == '/frontend.html'):

            # Load source bitmap
            g_bitmap = self.binary_read(self.arguments['filename'] + '_s.bmap')
            #for b in range(g_bit_vector_size):
            #   print(g_bitmap[b])
            self.create_image(g_bitmap, "image_s")

            # Open main HTML file
            try:
               with open('frontend.html', 'r') as fd:
                  self.send_response(200)
                  self.send_header('Content-type', 'text/html')
                  self.end_headers()

                  # Find block for characteristics
                  html_file = BeautifulSoup(fd.read(), 'html.parser')

                  # Insert characteristics
                  html_file.find('td', 'subnet_size').append("/" + str(g_granularity))
                  html_file.find('td', 'range').append(str(g_first_ip) + " - " + str(g_last_ip))
                  html_file.find('td', 'int_range').append(str(len(g_bitmap[0])) + " intervals")
                  html_file.find('td', 'time_interval').append(str(g_time_interval) + " seconds")
                  html_file.find('td', 'time_window').append(str(g_time_window) + " intervals")

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

            # Parse URL arguments
            query = None
            index = self.path.find('?')
            if index >= 0:
               query = cgi.parse_qs(self.path[index+1:])
               self.path = self.path[:index]

               # If bitmap update required, update
               if 'update' in query:
                  # Find out bitmap type (filename_<type>.bmap)
                  bmap_type = self.path.split('_')[1].split('.')[0]
                  g_bitmap = self.binary_read(self.arguments['filename'] +
                                               '_' + bmap_type + '.bmap')
                  self.create_image(g_bitmap, 'image_' + bmap_type)

               # If IP index is required
               if (('calculate_index' in query) and ('bitmap_type' in query) and
                   ('first_ip' in query) and ('ip_index' in query) and
                   ('interval' in query) and ('granularity' in query)):

                  # Get IPs and subnet
                  tmp_ip = query['first_ip'][0]
                  tmp_granularity = int(query['granularity'][0])
                  tmp_index = int(query['ip_index'][0])
                  bitmap_type = query['bitmap_type'][0]
                  tmp_ip = get_ip_from_index(tmp_ip, tmp_index, tmp_granularity)

                  # Get colour at coordinates
                  x = tmp_index
                  y = int(query['interval'][0])

                  tmp_bitmap = g_bitmap if bitmap_type == 'origin' else g_selected_bitmap

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
                  self.edit_bitmap(query)
                  self.create_image(g_selected_bitmap, 'selected')

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

            # Send appropriate file
            try:
               with open('.' + self.path, open_mode) as fd:
                  self.send_response(200)
                  self.send_header('Content-type', content_type)

                  if (query is not None) and ('update' in query):
                     self.send_header('Interval_range',
                                     str(len(g_bitmap[0]) if ((g_bitmap is not None) and (len(g_bitmap) > 0)) else 0))

                  self.end_headers()

                  # If image is sent via AJAX, encode to base64
                  if ((content_type == 'image/png') and (query is not None) and
                     (('update' in query) or ('select_area' in query))):
                     self.wfile.write(base64.b64encode(fd.read()))
                  else:
                     self.wfile.write(fd.read())

            except IOError:
               print('File .' + self.path + ' could not be opened.', file=sys.stderr)
               self.send_response(404)
               sys.exit(1)


   return My_RequestHandler

def main():
   ''' Main function for the lifecycle of the server. '''
   global g_first_ip, g_last_ip, g_ip_size, g_granularity, g_bit_vector_size
   global g_byte_vector_size, g_time_interval, g_time_window, g_bitmap

   # Parse arguments
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

   # Read configuration file
   try:
      with open(args['dir'] + '/' + args['config'], 'r') as fd:
         config_file = yaml.load(fd.read())
   except IOError:
      print('File ' + args['dir'] + args['config'] + ' could not be opened.', file=sys.stderr)
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

   # Get needed values

   # Get IPs
   if sys.version_info[0] == 2:
      g_first_ip = ipaddress.ip_address(unicode(config_file[args['filename']]['addresses']['first'],
                                                  "utf-8"))
      g_last_ip = ipaddress.ip_address(unicode(config_file[args['filename']]['addresses']['last'],
                                                 "utf-8"))

   else:
      g_first_ip = ipaddress.ip_address(config_file[args['filename']]['addresses']['first'])

      g_last_ip = ipaddress.ip_address(config_file[args['filename']]['addresses']['last'])

   g_granularity = int(config_file[args['filename']]['addresses']['granularity'])
   g_ip_size = g_first_ip.max_prefixlen

   g_bit_vector_size  = get_index_from_ip(str(g_first_ip), str(g_last_ip), g_granularity)
   g_byte_vector_size = int(math.ceil(g_bit_vector_size / 8))

   # Get time window and interval
   g_time_window = int(config_file[args['filename']]['time']['intervals'])
   g_time_interval = int(config_file[args['filename']]['time']['granularity'])


   # Create the server
   ip_activity_RequestHandler = create_request_handler(args)

   server = HTTPServer((args['hostname'], args['port']), ip_activity_RequestHandler)

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
