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
