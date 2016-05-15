/**
 * \file backend_functions.cpp
 * \brief Functions for backend
 * \author Katerina Pilatova <xpilat05@stud.fit.vutbr.cz>
 * \date 2016
 */
/*
 * Copyright (C) 2016 CESNET
 *
 * LICENSE TERMS
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 * 1. Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in
 *    the documentation and/or other materials provided with the
 *    distribution.
 * 3. Neither the name of the Company nor the names of its contributors
 *    may be used to endorse or promote products derived from this
 *    software without specific prior written permission.
 *
 * ALTERNATIVELY, provided that this notice is retained in full, this
 * product may be distributed under the terms of the GNU General Public
 * License (GPL) version 2 or later, in which case the provisions
 * of the GPL apply INSTEAD OF those given above.
 *
 * This software is provided ``as is'', and any express or implied
 * warranties, including, but not limited to, the implied warranties of
 * merchantability and fitness for a particular purpose are disclaimed.
 * In no event shall the company or contributors be liable for any
 * direct, indirect, incidental, special, exemplary, or consequential
 * damages (including, but not limited to, procurement of substitute
 * goods or services; loss of use, data, or profits; or business
 * interruption) however caused and on any theory of liability, whether
 * in contract, strict liability, or tort (including negligence or
 * otherwise) arising in any way out of the use of this software, even
 * if advised of the possibility of such damage.
 *
 */

#include <inttypes.h>
#include <signal.h>
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#include <bitset>
#include <ctime>
#include <fstream>
#include <iostream>
#include <string>

#include "yaml-cpp/yaml.h"
#include "ip_activity.hpp"

/* Storing bytes to file */
/*http://stackoverflow.com/questions/29623605/how-to-dump-stdvectorbool-in-a-binary-file*/
void binary_write(std::string filename, std::vector<bool> bits,
                  std::ios_base::openmode mode, uint32_t index)
{
   std::fstream bitmap;
   uint32_t size = bits.size();
   std::ostringstream name;
   name << filename;

   bitmap.open(name.str().c_str(), mode);

   // If rewriting is set, find the offset first
   if (!(mode & std::ofstream::app)) {
      uint32_t size_bytes = (size % 8) ? (size/8 + 1) : (size/8);
      bitmap.seekp(index * size_bytes, std::ios_base::beg);
   }

   for (uint64_t i = 0; i < size;) {
      uint8_t byte = 0;

      // Store each 8 bits to byte
      for (uint8_t mask = 128; (mask > 0) && (i < size); i++, mask >>= 1) {
         if (bits[i]) {
                byte |= mask;
         }
      }

      // Stream after bytes to file
      bitmap.write((const char*)&byte, sizeof(uint8_t));
   }

   bitmap.close();
   return;
}

/* Writing information to configuration file */
bool config_write (std::string configpath, std::vector<std::string> keys,
                   std::string value)
{
   if (keys.size() == 0) {
      return true;
   }

   // Load file in YAML
   YAML::Node config_yaml = YAML::LoadFile(configpath);
   // Create vector of nodes for hierarchy
   std::vector<YAML::Node> nodes(keys.size());
   nodes[0] = config_yaml[keys[0]];

   // Save hierarchy in nodes
   for (unsigned k = 1; k < keys.size(); k++) {
      nodes[k] = nodes[k-1][keys[k]];
   }
   // Assign value to the final node
   nodes[keys.size()-1] = value;

   // Save changes to file
   std::ofstream config_out(configpath);
   if (!config_out.is_open()) {
      return false;
   }
   config_out << config_yaml;
   config_out.close();
   return true;
}

/* Formats time to string - %d-%m-%Y %H:%M:%S */
std::string get_formatted_time(time_t raw_time) {
   struct tm* time_struct = localtime(&raw_time);
   char time_str[TIME_LEN];
   std::strftime(time_str, sizeof(time_str), "%Y-%m-%d %H:%M:%S", time_struct);
   return time_str;
}
