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


if __name__ == '__main__':
   handler = activity_visualisation.Visualisation_Handler()
   print(handler.bit_vector_size)
