#!/usr/bin/python
#coding=UTF-8

## @package activity_visualisation
#  Class for visualising bitmaps in form of images.
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

from bitarray import bitarray
import copy
import datetime
import ipaddress
import math
import os
from PIL import Image # Pillow needed for compatibility
import struct
import time
import yaml # pyyaml
import sys

# Class for handling bitmap, visualisation
class Visualisation_Handler:
   def __init__(self):
      ''' Constructor '''

      # Paths and filenames
      self.config_name = ''
      self.directory = ''
      self.bitmap_filename = 'bitmap'

      # Bitmap variables
      self.original_bitmap = None
      self.selected_bitmap = None
      self.mode = ''

      # IP variables
      self.first_ip = None
      self.last_ip = None
      self.ip_size = 0
      self.ip_granularity = 0

      # Time variables
      self.time_window = 0
      self.intervals = 0
      self.time_granularity = 0
      self.time_first = None

      # Selected area variables
      self.selected_first_ip = None
      self.selected_last_ip = None
      self.selected_bit_vector_size = 0
      
      self.selected_ip_granularity = 0
      self.selected_time_granularity = 0
      self.selected_first_int = 0
      self.selected_last_int = 0


   def load_config(self, directory, bitmap_name, config_name):
      ''' Initializes all values from the configuration file '''

      self.config_name = config_name
      self.bitmap_filename = bitmap_name
      self.directory = directory
      self.sasa = 2

      # Read configuration file
      try:
         with open(self.directory + '/' + self.config_name, 'r') as fd:
            config_file = yaml.load(fd.read())
      except IOError:
         print('File ' + self.directory + '/' + self.config_name +
               ' could not be opened.', file=sys.stderr)
         sys.exit(1)
   
      # Check if node with filename exists:
      if self.bitmap_filename not in config_file:
         print('Bitmap files not found.', file=sys.stderr)
         sys.exit(1) 
   
      # Check if node contains required keys
      if (not(set(['time', 'addresses','module'])<= set(config_file[self.bitmap_filename].keys())) or
         not(set(['first', 'last', 'granularity']) <= set(config_file[self.bitmap_filename]['addresses'].keys())) or
         not(set(['granularity', 'first', 'window']) <= set(config_file[self.bitmap_filename]['time'].keys())) or
         not('start' in config_file[self.bitmap_filename]['module'])):

         print('Configuration file structure is invalid.', file=sys.stderr)
         sys.exit(1)

      # Get time window and interval
      self.time_window = int(config_file[self.bitmap_filename]['time']['window'])
      self.time_granularity = int(config_file[self.bitmap_filename]['time']['granularity'])
      self.time_first = datetime.datetime.strptime(config_file[self.bitmap_filename]['time']['first'], '%d-%m-%Y %H:%M:%S')

      # Check mode
      if (('end' in config_file[self.bitmap_filename]['module']) and
          ('intervals' in config_file[self.bitmap_filename]['time'])):
         self.mode = 'offline'
         self.intervals = config_file[self.bitmap_filename]['time']['intervals']
      elif (('end' in config_file[self.bitmap_filename]['module']) or
            ('intervals' in config_file[self.bitmap_filename]['time'])):
         print('Configuration file structure is invalid.', file=sys.stderr)
         sys.exit(1)
      else:
         # Calculate intervals from elapsed time and interval length
         self.mode = 'online'
         #start = datetime.datetime.timedelta(seconds=self.time_first.total_seconds())
         now = datetime.datetime.now()
         self.intervals = int(math.floor((now - self.time_first).total_seconds()/self.time_granularity))

         print(datetime.datetime.strftime(self.time_first, '%d-%m-%Y %H:%M:%S'))
         print(datetime.datetime.strftime(now, '%d-%m-%Y %H:%M:%S'))
         print("interval length", self.time_granularity)
         print("intervals", self.intervals)
   
      # Get IPs
      if sys.version_info[0] == 2:
         self.first_ip = ipaddress.ip_address(unicode(config_file[self.bitmap_filename]['addresses']['first'],
                                                     "utf-8"))
         self.last_ip = ipaddress.ip_address(unicode(config_file[self.bitmap_filename]['addresses']['last'],
                                                    "utf-8"))
   
      else:
         self.first_ip = ipaddress.ip_address(config_file[self.bitmap_filename]['addresses']['first'])
   
         self.last_ip = ipaddress.ip_address(config_file[self.bitmap_filename]['addresses']['last'])
   
      self.ip_granularity = int(config_file[self.bitmap_filename]['addresses']['granularity'])
      self.ip_size = self.first_ip.max_prefixlen
   
      self.bit_vector_size  = self.get_index_from_ip(str(self.first_ip), str(self.last_ip), self.ip_granularity)
      self.byte_vector_size = int(math.ceil(self.bit_vector_size / 8))

   def binary_read(self, bitmap_name):
      ''' Returns 2D bitarray of updated, transposed bitmap '''
      # xxd [[-b] bitmap_name

      # Check if file exists and its size is bigger than 0
      if os.path.isfile(self.directory + '/' + bitmap_name):
         filesize = os.path.getsize(self.directory + '/' + bitmap_name)
      else:
         return None

      if filesize == 0:
         return None
         
      rows = int(filesize / self.byte_vector_size)

      # Temporary bitmap for rows vectors
      tmp_bitmap = {}
      for i in range(rows):
         tmp_bitmap[i] = bitarray()


      # Reads file row by row (by intervals), fill tmp_bitmap
      # 1 row == the whole address space in 1 time interval
      try:
         with open(self.directory + '/' + bitmap_name, 'rb') as fd:
            for r in range(rows):
               byte_vector = fd.read(self.byte_vector_size)
               tmp_bitmap[r].frombytes(byte_vector)

      except IOError:
         print('File ' + self.directory + '/' + bitmap_name + ' could not be opened.')
         sys.exit(1)

      # Remove padding from the end of the vector if needed
      trim_size = 8-(self.bit_vector_size % 8)
      if trim_size < 8:
         for r in range(rows):
            tmp_bitmap[r] = tmp_bitmap[r][:-trim_size]

      # Transpose bitmap
      # 1 row == 1 IP in all intervals
      transp_bitmap = {}

      for i in range(self.bit_vector_size):
         transp_bitmap[i] = bitarray()

      # Go through intervals in tmp_bitmap, append to transposed
      for r in range(rows):
         for b in range(self.bit_vector_size):
            transp_bitmap[b].append(tmp_bitmap[r][b])

      # Shift by number of intervals from the beginning if online mode
      index = (datetime.datetime.now() - self.time_first).total_seconds()
      print("seconds from the start:", index)
      #for r in range(rows):
      #   transp_bitmap[r] = 

      return transp_bitmap


   def get_ip_from_index(self, first_ip, index, granularity):
      ''' Calculates IP at index from first_ip considering granularity
          Handles IPs as strings '''
   
      # Shift IP, increment and shift back
      # Expicitly state IPv6:
      # > Python implicitly converts to IPv4 if the value fits in 32 bits
      if sys.version_info[0] == 2:
         if self.ip_size == 128:
            ip = ipaddress.IPv6Address(unicode(first_ip, "utf-8"))
         else:
            ip = ipaddress.ip_address(unicode(first_ip, "utf-8"))
      else:
         if self.ip_size == 128:
            ip = ipaddress.IPv6Address(first_ip)
         else:
            ip = ipaddress.ip_address(first_ip)
   
      if self.ip_size == 128:
         ip = ipaddress.IPv6Address((int(ip) >> (self.ip_size- granularity)))
         ip += index
         ip = ipaddress.IPv6Address((int(ip) << (self.ip_size - granularity)))
      else:
         ip = ipaddress.ip_address((int(ip) >> (self.ip_size - granularity)))
         ip += index
         ip = ipaddress.ip_address((int(ip) << (self.ip_size - granularity)))

      return str(ip)


   def get_index_from_ip(self, first_ip, curr_ip, granularity):
      ''' Calculates offset from first ip to current one (passed as strings) '''
   
      # Get IPs
      if sys.version_info[0] == 2:
         if self.ip_size == 128:
            ip1 = ipaddress.IPv6Address(unicode(first_ip, "utf-8"))
            ip2 = ipaddress.IPv6Address(unicode(curr_ip, "utf-8"))
         else:
            ip1 = ipaddress.ip_address(unicode(first_ip, "utf-8"))
            ip2 = ipaddress.ip_address(unicode(curr_ip, "utf-8"))
      else:
         if self.ip_size == 128: 
            ip1 = ipaddress.IPv6Address(first_ip)
            ip2 = ipaddress.IPv6Address(curr_ip)
         else:
            ip1 = ipaddress.ip_address(first_ip)
            ip2 = ipaddress.ip_address(curr_ip)
   
      # Adjust IPs to granularity, shift
      shift = ip1.max_prefixlen - granularity

      if self.ip_size == 128:
         shifted_1 = ipaddress.IPv6address(int(ip1) >> shift)
         shifted_2 = ipaddress.IPv6address(int(ip2) >> shift)
      else:
         shifted_1 = ipaddress.ip_address(int(ip1) >> shift)
         shifted_2 = ipaddress.ip_address(int(ip2) >> shift)
   
      # Get index
      return int(shifted_2) - int(shifted_1)


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
      image.save(self.directory + '/images/' + filename + '.png')


   def edit_bitmap(self, query):
      ''' Can involve selecting area, changing size '''

      # Check if original bitmap exists
      if self.original_bitmap is None:
         return

      tmp_bitmap = copy.deepcopy(self.original_bitmap)

      # Do magic here
      print ('Editing bitmap')

      # Save selected IP range
      if sys.version_info[0] == 2:
         self.selected_first_ip = ipaddress.ip_address(unicode(query['first_ip'][0], "utf-8"))
         self.selected_last_ip = ipaddress.ip_address(unicode(query['last_ip'][0], "utf-8"))
      else:
         self.selected_first_ip = ipaddress.ip_address(query['first_ip'][0])
         self.selected_last_ip = ipaddress.ip_address(query['last_ip'][0])
   

      # Adjust IP range (deleting rows)
      ip1_index = self.get_index_from_ip(str(self.first_ip), query['first_ip'][0], int(query['subnet_size'][0]))
      ip2_index = self.get_index_from_ip(str(self.first_ip), query['last_ip'][0], int(query['subnet_size'][0]))
      
      # Save IP range length
      self.selected_bit_vector_size = ip2_index - ip1_index

      # Move bitmap [ip1_index - ip2_index] to [0 - self.selected_bit_vector_size]
      for i in range(ip1_index, ip2_index):
         tmp_bitmap[i-ip1_index] = tmp_bitmap[i]

      # Delete the rest
      for i in range(self.selected_bit_vector_size, len(self.original_bitmap)):
         del tmp_bitmap[i]

      # Adjust Interval range (deleting columns)

      # Save interval range
      self.selected_first_int = int(query['first_int'][0])
      self.selected_last_int = int(query['last_int'][0])

      # Delete intervals out of range from rows
      for r in range(self.selected_bit_vector_size):
         tmp_bitmap[r] = tmp_bitmap[r][self.selected_first_int:self.selected_last_int]

      self.selected_bitmap = tmp_bitmap


if __name__ == '__main__':
   ''' Create an instance, try out printing an attribute value '''
   handler = Visualisation_Handler()
   print(handler.bitmap_filename)
