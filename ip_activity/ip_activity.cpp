/**
 * \file ip_activity.cpp
 * \brief Module for storing IP activity
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

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#include <getopt.h>
#include <inttypes.h>
#include <math.h>
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
#include <sstream>
#include <string>

#include "yaml-cpp/yaml.h"

#include <libtrap/trap.h>
#include <unirec/unirec.h>
#include <unirec/ipaddr_cpp.h>

#include "fields.h"
#include "ip_activity.hpp"

UR_FIELDS (
   ipaddr DST_IP,
   ipaddr SRC_IP,
   time TIME_FIRST
)


trap_module_info_t *module_info = NULL;

/* Example: ./ip_activity -i "t:12345" ..... */

#define MODULE_BASIC_INFO(BASIC) \
   BASIC("IP Activity module", "This module scans incoming flows and stores info about IP activity in a given range of IP.", 1,0)

#define MODULE_PARAMS(PARAM) \
   PARAM('c', "config", "Name + path to configuration file. (./config.yaml by default)", required_argument, "string") \
   PARAM('f', "filename", "Name of bitmap files. (bitmap by default)", required_argument, "string") \
   PARAM('g', "granularity", "Granularity in range of IP addresses (netmask).", required_argument, "uint32") \
   PARAM('r', "range", "Range of processed IP addresses that must correspond format (First address,Last address).", required_argument, "string") \
   PARAM('t', "time_interval", "Time unit for storing data to bitmap (default 5 minutes). [sec]", required_argument, "uint32") \
   PARAM('w', "time_window", "Time window for storing data to bitmap (default 100 intervals). [intervals]", required_argument, "uint32")
   

static int stop = 0;

// Function to handle SIGTERM and SIGINT signals (used to stop the module)
TRAP_DEFAULT_SIGNAL_HANDLER(stop = 1);

/**
 * \brief Converts address based on chosen granularity (shifts to right)
 * \param [in] addr IP address to be checked.
 * \param [in] granularity To which granularity the IP is to be converted.
 */
void convert_to_granularity (IPaddr_cpp *addr, int granularity) {

   int version = addr->get_version();
   // How many zeros at the end
   int zeros = (version == 4) ? (IPV4_BITS - granularity) : (IPV6_BITS - granularity);

   if (zeros == 0) {
      return;
   }

   // IPv4
   if (version == 4) {
      uint32_t tmp_ip = addr->get_ipv4_int();

      // Shift
      tmp_ip >>= zeros;
      addr->set_ipv4_int(tmp_ip);
   } else {
      // IPv6
      std::bitset<IPV6_BITS> tmp_ip = addr->get_bits_ipv6();

      // Shift
      tmp_ip >>= zeros;
      addr->set_bits_ipv6(tmp_ip);
   }
   return;
}

/**
 * \brief Return size of address space between two addresses in set granularity
 * \param [in] addr1, addr2 start and end of considered range
 * \param [in] granularity  granularity of addresses inside said range.
 * \return addr2/granularity - addr1/granularity
 */
uint32_t ip_substraction (IPaddr_cpp addr1, IPaddr_cpp addr2)
{
   // Check IP validity, same version
   if ((addr1.get_version() != addr2.get_version()) ||
       (addr1.get_version() == 0)) {
      return 0;
   }
   int version = addr1.get_version();

   if (addr1 > addr2) {
      return 0;
   }

   if (version == 4) {
      // IPv4, substract uint32_t
      uint32_t ip1 = addr1.get_ipv4_int();
      uint32_t ip2 = addr2.get_ipv4_int();
      return ip2-ip1;

   } else {
      // IPv6, substract uint32_t 4x
      std::vector<uint32_t> ip1 = addr1.get_ipv6_int();
      std::vector<uint32_t> ip2 = addr2.get_ipv6_int();
      std::vector<uint32_t> substr;
      substr.resize(4);
      uint8_t borrow = 0;

      if ((ip1.size() != 4) || (ip2.size() != 4)) {
         return 0;
      }

      // Go from right to left substraction of 32b parts
      for (int i = 3; i >= 0; i--) {
         // Normal substraction, no borrow
         if (ip2[i] >= (ip1[i] + borrow)) {
            substr[i] = ip2[i] - ip1[i] - borrow;
            borrow = 0;
         } else {
            // Add radix to remain positive result, add borrow
            substr[i] = (ip2[i] + UINT32_MAX) - ip1[i] - borrow;
            borrow = 1;
         }
      }
      // Max allowed value is below 2^32 -> only the last part can be occupied
      if (substr[0] || substr[1] || substr[2]) {
         return 0;
      }
      return substr[3];
   }
}

/** Main function */
int main(int argc, char **argv)
{
   int ret;

   // Initialise TRAP
   INIT_MODULE_INFO_STRUCT(MODULE_BASIC_INFO, MODULE_PARAMS)
   TRAP_DEFAULT_INITIALIZATION(argc, argv, *module_info);

   // Register signal handler.
   TRAP_REGISTER_DEFAULT_SIGNAL_HANDLER();

   // Create template
   ur_template_t *tmplt = ur_create_input_template(0, "DST_IP,SRC_IP,TIME_FIRST", NULL);

   if (tmplt == NULL) {
      fprintf(stderr, "Error: Template could not be created.\n");
      return -1;
   }

   // Initialization of default values
   int time_interval = 300, time_window = 100;
   int granularity = 8;
   int ip_version = 4; // by default, primarily to be deduced from input IPs
   IPaddr_cpp range[2];
   bool rflag = false;
   std::string filename = "bitmap", configname = "config.yaml";

   /** Parse Arguments */
   char opt;
   size_t index;
   std::string delim = ",", tmp_range;
   const char hex_str[] = "0123456789abcdefABCDEF:.";

   while ((opt = TRAP_GETOPT(argc, argv, module_getopt_string, long_options)) != -1) {
      switch (opt) {
          case 'c':
            configname.assign(optarg);
            break;
          case 'f':
            filename.assign(optarg);
            break;
          case 'g':
            granularity = atoi(optarg);
            break;
         case 'r':
            tmp_range.assign(optarg);
            index = tmp_range.find(delim);

            if (index == std::string::npos) {
               fprintf(stderr, "Error: IP range - bad format.\n");
               return 1;
            }

            // Convert all IPs to ip_addr_t
            if (strspn(tmp_range.substr(0, index).c_str(), hex_str) != index) {
               fprintf(stderr, "Error: IP range - bad format of the first IP.\n");
               return 1;
            }
            range[FIRST_ADDR].fromString(tmp_range.substr(0, index));
            tmp_range.erase(0, index + delim.length());
            if (strspn(tmp_range.c_str(), hex_str) != tmp_range.length()) {
               fprintf(stderr, "Error: IP range - bad format of the second IP.\n");
               return 1;
            }
            range[LAST_ADDR].fromString(tmp_range);
            rflag = true;
            break;

         case 't':
            time_interval = atoi(optarg);
            if ((time_interval < 0) || (time_interval > MAX_INTERVAL)) {
               fprintf(stderr, "Error: Time interval - invalid value %d.\n", time_interval);
               return 1;
            }
            break;
         case 'w':
            time_window = atoi(optarg);
            if ((time_window < 0) || (time_window > MAX_WINDOW)) {
               fprintf(stderr, "Error: Time window - invalid value %d.\n", time_window);
               return 1;
            }
            break;
         default:
            fprintf(stderr, "Error: Unknown parameter -%c.\n", opt);
            return 1;
      }
   }

   // If no range entered, used the entire range of IPv4 at /8 by default
   if (!rflag) {
      range[FIRST_ADDR].fromString("1.0.0.0");
      range[LAST_ADDR].fromString("255.0.0.0");
   } else {
      // Deduce IP version
      if (range[FIRST_ADDR].is_ipv4() && range[LAST_ADDR].is_ipv4()) {
         ip_version = 4;
      } else if (range[FIRST_ADDR].is_ipv6() && range[LAST_ADDR].is_ipv6()) {
         ip_version = 6;
      } else {
         fprintf(stderr, "Error: Range does not contain two valid IPs of the same version.\n");
         return 1;
      }

      if (range[FIRST_ADDR] >= range[LAST_ADDR]) {
         std::cout << range[FIRST_ADDR].toString() << " " << range[LAST_ADDR].toString() << std::endl;
         fprintf(stderr, "Error: Range is smaller than one subnet /%d\n",
               granularity);
         return 1;
      }
   }


   // Check netmask
   if (((ip_version == 4) && (granularity > IPV4_BITS)) ||
       ((ip_version == 6) && (granularity > IPV6_BITS))) {
      fprintf(stderr, "Error: Granularity - IPv%d netmask value cannot be greater than %d.\n",
              ip_version, ((ip_version == 4) ? IPV4_BITS : IPV6_BITS));
      return 1;
   }

   /** Create/open YAML configuration file  and bitmaps */

   std::fstream config;
   config.open(configname, std::ios_base::out | std::ios_base::in);
   if (!config.is_open()) {
      fprintf(stderr, "Error: File could not be opened/created.\n");
      return 1;
   }
   config.close();

   // Load file to YAML parser
   YAML::Node config_file = YAML::LoadFile(configname);

   // Remove first and last if they exist (when rewriting, ! <!> appeared)
   if (config_file[filename]["addresses"]["first"]) {
      config_file[filename]["addresses"].remove("first");
   }
   if (config_file[filename]["addresses"]["last"]) {
      config_file[filename]["addresses"].remove("last");
   }
   if (config_file[filename]["module"]["start"]) {
      config_file[filename]["module"].remove("start");
   }
   if (config_file[filename]["module"]["end"]) {
      config_file[filename]["module"].remove("end");
   }
   if (config_file[filename]["time"]["intervals"]) {
      config_file[filename]["time"].remove("intervals");
   }
   if (config_file[filename]["time"]["first"]) {
      config_file[filename]["time"].remove("first");
   }
   if (config_file[filename]["time"]["last"]) {
      config_file[filename]["time"].remove("last");
   }

   // Set bitmap options for server
   config_file[filename]["addresses"]["granularity"] = granularity;

   config_file[filename]["addresses"]["first"] = range[FIRST_ADDR].toString();
   config_file[filename]["addresses"]["last"] = range[LAST_ADDR].toString();

   config_file[filename]["time"]["granularity"] = time_interval;
   config_file[filename]["time"]["window"] = time_window;
   config_file[filename]["time"]["intervals"] = 0;
   config_file[filename]["module"]["start"] = get_formatted_time(std::time(NULL));

   // Save changes to config file
   std::ofstream config_out(configname);
   config_out << config_file;
   config_out.close();

   // Create bitmap files
   std::fstream bitmap;
   std::string suffix[3] = {"_s.bmap", "_d.bmap", "_sd.bmap"};
   std::ostringstream name;
   name.str("");

   // If they aren't empty, their content is truncated
   for (int i = 0; i < 3; i++) {
      name << filename << suffix[i];
      bitmap.open(name.str().c_str(),
                      std::ios_base::out | std::ios_base::trunc);
      bitmap.close();
      name.str("");
   }

   // Convert IPs to granularity
   convert_to_granularity(&range[FIRST_ADDR], granularity);
   convert_to_granularity(&range[LAST_ADDR], granularity);

   std::cout << range[FIRST_ADDR].toString() << " and " << range[LAST_ADDR].toString() << std::endl;


   // Get size of bit vector
   uint32_t vector_size = ip_substraction(range[FIRST_ADDR], range[LAST_ADDR]);

   if ((vector_size == 0) || vector_size > MAX_VECTOR_SIZE) {
      fprintf(stderr, "Error: Address space must be between 1 and 1000 subnets.\n");
      return 1;
   }

   std::cout << "vector size: " << vector_size << std::endl;

   // Create bit vectors and basis for open modes.
   std::vector<std::vector<bool>> bits (3, std::vector<bool>(vector_size, 0));
   bool rewrite = false;
   std::ios_base::openmode mode = std::ios_base::binary | std::ios_base::out |
                                  std::ios_base::in | std::ios_base::app;


   int intervals = 0; // it is a number of intervals
   bool first = true; // for setting start time in configuration file
   time_t time_first = std::time(NULL), time_curr = std::time(NULL);
   std::ostringstream intervals_str;

   /** Main loop */
   while (!stop) {
      const void *rec;
      uint16_t rec_size;
      IPaddr_cpp ip(false);

      // Receive data from input interface
      ret = TRAP_RECEIVE(0, rec, rec_size, tmplt);
      // Handle possible errors
      TRAP_DEFAULT_RECV_ERROR_HANDLING(ret, continue, break);

      // Get TIME_FIRST of the first record for the configuration file
      if (first) {
         time_first = ur_time_get_sec(ur_get(tmplt, rec, F_TIME_FIRST));
         time_curr = time_first;

         // Load time to config file
         config_write(configname, std::vector<std::string>({filename,
                                  "time", "first"}), get_formatted_time(time_first));
         first = false;
      } else {         
         time_curr = ur_time_get_sec(ur_get(tmplt, rec, F_TIME_FIRST));

         // Check if the record is older > it is skipped
         if (time_curr < time_first + (intervals * time_interval)) {
            continue;
         }

         // Check if the record is still in the interval
         // If an interval is skipped, fill the rest with 0s
         while ((time_first + ((intervals+1) * time_interval)) < time_curr) {
            for (int i = 0; i < 3; i++) {
               binary_write(filename + suffix[i], bits[i], mode, intervals % time_window);
               // Clear vector values
               bits[i].assign(bits[i].size(), 0);
            }

            // Update configuration file
            if (rewrite) {
               config_write(configname, std::vector<std::string>({filename,
                           "time", "first"}),
                           get_formatted_time(time_first + ((intervals - time_window) * time_interval)));
            }

            intervals_str.str("");
            intervals_str.clear();
            intervals_str << intervals;
            config_write(configname, std::vector<std::string>({filename,
                           "time", "intervals"}), intervals_str.str());

            // When the buffer is full, turn off appending
            if (!rewrite && ((intervals + 1) == time_window)) {
               rewrite = true;
               mode = mode & (~(std::ios_base::app));
            }

            intervals++;
         }
      }

      // Check SRC and DST IP
      for (int i = 0; i < 2; i++) {
         if (i == SRC) {
            ip.set_IP(&ur_get(tmplt, rec, F_SRC_IP), true);
         } else {
            ip.set_IP(&ur_get(tmplt, rec, F_DST_IP), true);
         }

         // Check IP version
         if (ip.get_version() == ip_version) {
            convert_to_granularity(&ip, granularity);

            // Check if IP is in range
            if ((ip >= range[FIRST_ADDR]) && (ip <= range[LAST_ADDR])) {

               // Calculate index in bit vector
               //std::cout << "ip: " << origin << std::endl;
               uint64_t index = ip_substraction(range[FIRST_ADDR], ip);
               //std::cout << "index: " << index << std::endl;

               // Set bit in vector (would condition that it is 0 make it any faster?)
               bits[i][index] = 1;
               bits[SRC_DST][index] = 1;
            
            }
         }
      }
   }

   // Store the rest of data to bitmaps
   for (int i = 0; i < 3; i++) {
      binary_write(filename + suffix[i], bits[i], mode, intervals % time_window);
   }

   if (rewrite) {
      config_write(configname, std::vector<std::string>({filename,
                  "time", "first"}),
                  get_formatted_time(time_first + ((intervals - time_window) * time_interval)));
   }

   // Load end time and intervals to config file
   config_write(configname, std::vector<std::string>({filename,
                            "module", "end"}), get_formatted_time(std::time(NULL)));
   intervals_str.str("");
   intervals_str.clear();
   intervals_str << intervals;

   config_write(configname, std::vector<std::string>({filename,
                            "time", "intervals"}), intervals_str.str());
   config_write(configname, std::vector<std::string>({filename,
                            "time", "last"}), (first ? "undefined" : get_formatted_time(time_curr)));

   /* Cleanup */
   TRAP_DEFAULT_FINALIZATION();
   FREE_MODULE_INFO_STRUCT(MODULE_BASIC_INFO, MODULE_PARAMS)

   return 0;
}
