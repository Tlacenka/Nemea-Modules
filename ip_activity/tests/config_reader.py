#!/usr/bin/python

## @package config_reader
#  File testing reading configuration
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
   handler.load_config(path, 'test1', 'config_test.yaml')

def test2():
   handler = activity_visualisation.Visualisation_Handler()
   handler.load_config(path, 'test2', 'config_test.yaml')

def test3():
   handler = activity_visualisation.Visualisation_Handler()
   handler.load_config(path, 'test3', 'config_test.yaml')

def test4():
   handler = activity_visualisation.Visualisation_Handler()
   handler.load_config(path, 'test4', 'config_test.yaml')

def test5():
   handler = activity_visualisation.Visualisation_Handler()
   handler.load_config(path, 'test5', 'config_test.yaml')

def test6():
   handler = activity_visualisation.Visualisation_Handler()
   handler.load_config(path, 'test6', 'config_test.yaml')

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
