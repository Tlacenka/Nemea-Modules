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
      self.undefined = 105 # colour for undefined areas (0x69)

      # IP variables
      self.first_ip = None
      self.last_ip = None
      self.ip_size = 0
      self.ip_granularity = 0
      self.bit_vector_size = 0
      self.byte_vector_size = 0

      # Time variables
      self.time_window = 0
      self.intervals = 0
      self.time_granularity = 0
      self.time_first = None
      self.time_last = None
      self.time_format = '%Y-%m-%d %H:%M:%S'

      # Selected area variables
      self.selected_first_ip = None
      self.selected_last_ip = None
      self.selected_bit_vector_size = 0
      
      self.selected_first_int = 0
      self.selected_last_int = 0


   def load_config(self, directory, bitmap_name, config_name):
      ''' Initializes all values from the configuration file
          directory   - path to directory with bitmaps and configuration
          bitmap_name - bitmap filename (excluding suffixes)
          config_nam  - name of the configuration file (including suffixes)
      '''

      self.config_name = config_name + '.yaml'
      self.bitmap_filename = bitmap_name
      self.directory = directory

      # Read configuration file
      config_file = self.validate_config(self.directory, self.config_name, 'online')

      if config_file is None:
         sys.exit(1)

      # Get time window and interval
      self.time_window = int(config_file[self.bitmap_filename]['time']['window'])
      self.time_granularity = int(config_file[self.bitmap_filename]['time']['granularity'])
      self.time_first = datetime.datetime.strptime(str(
                        config_file[self.bitmap_filename]['time']['first']),
                        self.time_format)
      self.intervals = int(config_file[self.bitmap_filename]['time']['intervals'])


      # Check mode
      if (('end' in config_file[self.bitmap_filename]['module']) and
          ('last' in config_file[self.bitmap_filename]['time'])):
         self.mode = 'offline'
         if config_file[self.bitmap_filename]['time']['last'] == 'undefined':
            print('Last record time is undefined > less than one flow recorded.', file=sys.stderr)
            sys.exit(1)
         self.time_last = datetime.datetime.strptime(str(
                          config_file[self.bitmap_filename]['time']['last']),
                          self.time_format)
      elif (('end' in config_file[self.bitmap_filename]['module']) or
            ('last' in config_file[self.bitmap_filename]['time'])):
         print('Configuration file structure is invalid.', file=sys.stderr)
         sys.exit(1)
      else:
         # Calculate intervals from elapsed time and interval length
         # Last time is current time
         self.mode = 'online'
         length = (self.time_window if (self.intervals > self.time_window) else self.intervals)
         self.time_last = self.time_first + datetime.timedelta(seconds=length * self.time_granularity)

      # Get IPs
      if sys.version_info[0] == 2:
         self.first_ip = ipaddress.ip_address(unicode(
                         config_file[self.bitmap_filename]['addresses']['first'],
                         "utf-8"))
         self.last_ip = ipaddress.ip_address(unicode(
                        config_file[self.bitmap_filename]['addresses']['last'],
                        "utf-8"))
   
      else:
         self.first_ip = ipaddress.ip_address(
                         config_file[self.bitmap_filename]['addresses']['first'])
   
         self.last_ip = ipaddress.ip_address(
                        config_file[self.bitmap_filename]['addresses']['last'])
   
      self.ip_granularity = int(config_file[self.bitmap_filename]['addresses']['granularity'])
      self.ip_size = self.first_ip.max_prefixlen
   
      self.bit_vector_size  = self.get_index_from_ip(str(self.first_ip),
                              str(self.last_ip), self.ip_granularity)
      self.byte_vector_size = int(math.ceil(self.bit_vector_size / 8))
      return

   def validate_config(self, directory, config_name, mode):
      ''' Validates configuration structure 
           directory   - path to directory containing configuration
           config_name - filename of configuration file (inclufing suffix)
           mode        - online/offline
      '''

      # Read configuration file
      try:
         with open(directory + '/' + config_name, 'r') as fd:
            config_file = yaml.load(fd.read())
      except IOError:
         print('File ' + directory + '/' + config_name +
               ' could not be opened.', file=sys.stderr)
         return None
   
      # Check if node with filename exists:
      if self.bitmap_filename not in config_file:
         print('Bitmap files not found.', file=sys.stderr)
         return None
   
      # Check if node contains required keys
      if (not(set(['time', 'addresses','module'])<= set(config_file[self.bitmap_filename].keys())) or
         not(set(['first', 'last', 'granularity']) <= set(config_file[self.bitmap_filename]['addresses'].keys())) or
         not(set(['granularity', 'first', 'window', 'intervals']) <= set(config_file[self.bitmap_filename]['time'].keys())) or
         not('start' in config_file[self.bitmap_filename]['module'])):

         print('Configuration file structure is invalid.', file=sys.stderr)
         return None

      if mode == 'offline':
         if (not('end' in config_file[self.bitmap_filename]['module']) or
             not('last' in config_file[self.bitmap_filename]['time'])):
            return None

      return config_file

   def update_config(self):
      ''' Updates configuration - mainly focuses on mode and time range'''
      changed = False

      # Check online -> offline
      if self.mode == 'online':
         config_file = self.validate_config(self.directory, self.config_name, 'offline')
         if config_file is not None:
            changed = True
            self.mode = 'online offline'

      # Check current mode validity
      if not changed:
         config_file = self.validate_config(self.directory, self.config_name, self.mode)
         if config_file is None:
            return False

      # Update values
      if (self.mode == 'online') or changed:
         self.intervals = config_file[self.bitmap_filename]['time']['intervals']
         self.time_first = datetime.datetime.strptime(str(
                              config_file[self.bitmap_filename]['time']['first']),
                              self.time_format)
         if changed:
            self.time_last = datetime.datetime.strptime(str(
                                config_file[self.bitmap_filename]['time']['last']),
                                self.time_format)
         else:
            length = (self.time_window if (self.intervals > self.time_window) else self.intervals)
            self.time_last = self.time_first + datetime.timedelta(seconds=length * self.time_granularity)

      return True

   def binary_read(self, bitmap_name):
      ''' Returns 2D bitarray of updated, transposed bitmap
          bitmap_name - bitmap filename (including suffixes)
      '''

      # Check if file exists and its size is bigger than 0
      if os.path.isfile(self.directory + '/' + bitmap_name):
         filesize = os.path.getsize(self.directory + '/' + bitmap_name)
      else:
         print("Bitmap file does not exist.", file=sys.stderr)
         return None

      if filesize == 0:
         print("File size is 0.", file=sys.stderr)
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

      # Shift by number of intervals from the beginning to get offset in
      # circular buffer
      if self.intervals > self.time_window:
         index = self.intervals % self.time_window
         for r in range(self.bit_vector_size):
            transp_bitmap[r] = transp_bitmap[r][index:] + transp_bitmap[r][:index]

      return transp_bitmap


   def get_ip_from_index(self, first_ip, index, granularity):
      ''' Calculates IP at index from first_ip considering granularity
          Handles IPs as strings.
          first_ip    - first ip subnet in range
          index       - index of wanted IP
          granularity - subnet size
      '''
   
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
      ''' Calculates offset from first ip to current one (passed as strings)
          first_ip    - first IP in range
          curr_ip     - current IP value for calculating index
          granularity - subnet size
      '''
   
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

   def get_time_from_index(self, first_time, index, granularity):
      ''' Returns time string at index
          first_time  - first interval in range
          index       - index of interval
          granularity - time unit in seconds
      '''
      return first_time + datetime.timedelta(seconds=index * granularity)
         
   def get_index_from_times(self, time1, time2, granularity):
      ''' Returns intervals between time1 and time2
          time1       - first time in specified range
          time2       - last time in specified range (at wanted index)
          granularity - interval length in seconds
      '''
      return int(math.floor((time2 - time1).total_seconds() / granularity))

   def create_image(self, bitmap, filename, scaleR, scaleC, height, width, selected):
      ''' Create black and white image from bitmap
          Scales bitmap - scaleR:1 for rows, scaleC:1 for columns
          Fills bitmap with gray until it is width x height
          bitmap   - matrix of bitmap defined for visualisation
          filename - name of final image file
          scaleR   - scaling of rows in scaleR:1 ration
          scaleC   - scaling of columns in scaleC:1 ration
          height   - height of the final image
          width    - width of the final image
          selected - if image is to be in the selected area (boolean)
      '''

      print ("height: " + str(height),"width: " + str(width))

      bitmap_height = len(list(bitmap))
      if bitmap_height == 0:
         return

      bitmap_width = len(bitmap[0])
      if bitmap_width == 0:
         return

      # Size of the image:
      # height = address space, width = intervals in bitmap
      if selected:
         fill_height = height - scaleR*bitmap_height
         fill_width = width - scaleC*bitmap_width
      else:
         fill_height = (height - bitmap_height) if (height > bitmap_height) else 0
         fill_width = (width - bitmap_width) if (width > bitmap_width) else 0

      print("width: bitmap-" + str(bitmap_width) + " scale-" + str(scaleC) + " fill-" + str(fill_width))
      print("height: bitmap-" + str(bitmap_height) + " scale-" + str(scaleR) + " fill-" + str(fill_height))

      print ('Creating image', str(height) + 'x' + str(width),
             'rows: ' + str(scaleR) + ':1', 'cols: ' + str(scaleC) + ':1')

      # Save bitmap to buffer as integers
      img_buffer = []

      for r in range(bitmap_height):
         for rs in range(scaleR):
            # Add data
            for c in range(bitmap_width):
               for cs in range(scaleC):
                  img_buffer.append(255 if bitmap[r][c] else 0)

            # Add padding
            for cfill in range(fill_width):
               # Same here - scaling applies only to original bitmap
               if not selected:
                  for cs in range(scaleC):
                     img_buffer.append(self.undefined)
               else:
                  img_buffer.append(self.undefined)

      # For original bitmap, add scaled rows
      if not selected:
         for rfill in range(fill_height):
            for rs in range(scaleR):
               # Fill the whole line with padding
               for c in range(width):
                     for cs in range(scaleC):
                        img_buffer.append(self.undefined)

      else:
         # For selected bitmap, scaling is already considered
         for rfill in range(fill_height):
            for c in range(width):
               img_buffer.append(self.undefined)

      # Create and save image
      img_data = struct.pack('B'*len(img_buffer), *img_buffer)
      if selected:
         image = Image.frombuffer('L', (width, height), img_data, 'raw', ('L', 0, 1))
      else:
         image = Image.frombuffer('L', (width * scaleC, height * scaleR), img_data, 'raw', ('L', 0, 1))
      image.save(self.directory + '/images/' + filename + '.png')


   def edit_bitmap(self, query):
      ''' Can involve selecting area, changing size
          query - received request query
      '''

      # Check if original bitmap exists
      if self.original_bitmap is None:
         return

      tmp_bitmap = copy.deepcopy(self.original_bitmap)

      # Do magic...editing here
      print ('Editing bitmap')

      # Save selected IP range
      if sys.version_info[0] == 2:
         self.selected_first_ip = ipaddress.ip_address(
                                  unicode(query['first_ip'][0], "utf-8"))
         self.selected_last_ip = ipaddress.ip_address(
                                 unicode(query['last_ip'][0], "utf-8"))
      else:
         self.selected_first_ip = ipaddress.ip_address(query['first_ip'][0])
         self.selected_last_ip = ipaddress.ip_address(query['last_ip'][0])
   

      # Adjust IP range (deleting rows)
      ip1_index = self.get_index_from_ip(str(self.first_ip),
                                         query['first_ip'][0], self.ip_granularity)
      ip2_index = self.get_index_from_ip(str(self.first_ip),
                                         query['last_ip'][0], self.ip_granularity)
      
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
      self.selected_first_int = datetime.datetime.strptime(query['first_int'][0], self.time_format)
      self.selected_last_int = datetime.datetime.strptime(query['last_int'][0], self.time_format)

      # Delete intervals out of range from rows
      first_index = self.get_index_from_times(self.time_first,
                                              self.selected_first_int,
                                              self.time_granularity)
      last_index = self.get_index_from_times(self.time_first,
                                             self.selected_last_int,
                                             self.time_granularity)
      for r in range(self.selected_bit_vector_size):
         tmp_bitmap[r] = tmp_bitmap[r][first_index:last_index]

      self.selected_bitmap = tmp_bitmap


if __name__ == '__main__':
   ''' Create an instance, try out printing an attribute value '''
   handler = Visualisation_Handler()
   print(handler.bitmap_filename)
