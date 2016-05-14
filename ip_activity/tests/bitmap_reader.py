#!/usr/bin/python

## @package bitmap_reader
#  File testing reading bitmap
#  Author: Katerina Pilatova <xpilat05@stud.fit.vutbr.cz>
#  Date: 2016
#

from __future__ import print_function, division, with_statement

import argparse
from bitarray import bitarray
import copy
import datetime
import ipaddress
import math
import os
import sys
import time
import yaml # pyyaml

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
import activity_visualisation


path = os.path.dirname(__file__)

def test1():
   handler = activity_visualisation.Visualisation_Handler()
   handler.directory = os.path.dirname(__file__)
   handler.byte_vector_size = 2
   handler.bit_vector_size = 16
   handler.intervals = 10
   handler.time_window = 11
   bitmap = handler.binary_read("test1.bmap")

   if bitmap is None:
      sys.exit(1)

   for i in range(16):
      print(str(bitmap[i]))

def test2():
   handler = activity_visualisation.Visualisation_Handler()
   handler.directory = os.path.dirname(__file__)
   handler.byte_vector_size = 12
   handler.bit_vector_size = 95
   handler.intervals = 10
   handler.time_window = 11
   bitmap = handler.binary_read("test2.bmap")

   if bitmap is None:
      sys.exit(1)

   for i in range(95):
      print(str(bitmap[i]))

def test3():
   handler = activity_visualisation.Visualisation_Handler()
   handler.directory = os.path.dirname(__file__)
   handler.byte_vector_size = 2
   handler.bit_vector_size = 9
   handler.intervals = 5
   handler.time_window = 6
   bitmap = handler.binary_read("test3.bmap")

   if bitmap is None:
      sys.exit(1)

   for i in range(9):
      print(str(bitmap[i]))

def test4():
   handler = activity_visualisation.Visualisation_Handler()
   handler.directory = os.path.dirname(__file__)
   handler.byte_vector_size = 2
   handler.bit_vector_size = 12
   handler.intervals = 8
   handler.time_window = 9
   bitmap = handler.binary_read("test4.bmap")

   if bitmap is None:
      sys.exit(1)

   for i in range(9):
      print(str(bitmap[i]))

def test5():
   handler = activity_visualisation.Visualisation_Handler()
   handler.directory = os.path.dirname(__file__)
   handler.byte_vector_size = 2
   handler.bit_vector_size = 16
   handler.intervals = 10
   handler.time_window = 7
   bitmap = handler.binary_read("test5.bmap")

   if bitmap is None:
      sys.exit(1)

   for i in range(16):
      print(str(bitmap[i]))
def test6():
   return

if __name__ == '__main__':
   # Parse self.arguments
   parser = argparse.ArgumentParser()
   parser.add_argument('-t', '--test', type=int, default=0,
                       help='Number of test to be run. All by default.')

   arguments = vars(parser.parse_args())

   if arguments['test'] == 1:
      test1()
   elif arguments['test'] == 2:
      test2()
   elif arguments['test'] == 3:
      test3()
   elif arguments['test'] == 4:
      test4()
   elif arguments['test'] == 5:
      test5()
   elif arguments['test'] == 6:
      test6()
   else:
      test1()
      test2()
      test3()
      test4()
      test5()
      test6()
   
   sys.exit(0)
