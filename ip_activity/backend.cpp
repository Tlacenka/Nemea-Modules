/**
 * \file backend.cpp
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
#include <stdlib.h>
#include <time.h>

#include <bitset>
#include <ctime>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <utility> 

#include "yaml-cpp/yaml.h"

#include <libtrap/trap.h>
#include <unirec/unirec.h>
#include <nemea-common.h>
#include <unirec/ipaddr_cpp.h>
#include "fields.h"

UR_FIELDS (
   ipaddr DST_IP,
   ipaddr SRC_IP
)


trap_module_info_t *module_info = NULL;

#define FIRST_ADDR 0
#define LAST_ADDR 1

#define IPV4 0
#define IPv6 1

#define IPV4_BITS 32
#define IPV6_BITS 128

#define SRC 0
#define DST 1
#define SRC_DST 2

#define MAX_WINDOW 1000
#define MAX_VECTOR_SIZE 1000

/* Example: ./ip_activity -i "t:12345" ..... */

#define MODULE_BASIC_INFO(BASIC) \
   BASIC("IP Activity module", "This module scans incoming flows and stores info about IP activity in a given range of IP.", 1,0)

#define MODULE_PARAMS(PARAM) \
   PARAM('t', "time_interval", "Time unit for storing data to bitmap (default 5 minutes). [sec]", required_argument, "uint32") \
   PARAM('w', "time_window", "Time window for storing data to bitmap (default 100 intervals). [intervals]", required_argument, "uint32") \
   PARAM('p', "print", "Show progress - print a dot every interval.", no_argument, "none") \
   PARAM('g', "granularity", "Granularity in range of IP addresses (netmask).", required_argument, "uint32") \
   PARAM('r', "range", "Range of processed IP addresses that must correspond format (First address,Last address).", required_argument, "string") \
   PARAM('f', "filename", "Name of bitmap files. (bitmap by default)", required_argument, "string")

static int stop = 0;
static int save_vectors = 0;

// Declaration of structure prototype for printing progress
NMCM_PROGRESS_DECL;

// Function to handle SIGTERM and SIGINT signals (used to stop the module)
TRAP_DEFAULT_SIGNAL_HANDLER(stop = 1);

/**
 * \brief SIGALRM handler
 * Sets flag for storing data to bitmap every interval.
 */
void IPactivity_signal_handler (int sig) {
   switch (sig) {
      case SIGALRM:
         save_vectors = 1;
         break;
      default:
         break;
   }
}

/**
 * \brief Converts address based on chosen granularity (shifts to right)
 * \param [in] addr IP address to be checked.
 * \return True upon success.
 */
void convert_to_granularity (IPaddr_cpp *addr, int granularity) {
   int version = addr->get_version();
   

   // How many zeros at the end
   int zeros = (version == 4) ? (IPV4_BITS - granularity) : (IPV6_BITS - granularity);

   if (zeros == 0) {
      return;
   }
   //std::cout << "before: " << addr->toString() << std::endl;

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

   //std::cout << "after: " << addr->toString() << std::endl;
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

      //std::cout << ip2-ip1 << std::endl;
      return ip2-ip1;

   } else {
      // IPv6, substract uint32_t 4x
      // Substraction result
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

      // Since the maximum allowed value is definitely below 2^32,
      // only the last 4 bytes can be occupied
      if (substr[0] || substr[1] || substr[2]) {
         return 0;
      }

      return substr[3];
   }
}

/**
 * \brief Write bit vector to file.
 * \param [out] bitmap Target file.
 * \param [in]  bits   Bit vector to be stored;
 * \param [in]  index  Offset of row in bitmap (unit is vector_size);
 * \param [in]  mode   Open mode.
 */
/*http://stackoverflow.com/questions/29623605/how-to-dump-stdvectorbool-in-a-binary-file*/
/** Maybe use dynamic bitset? */
void binary_write(std::string filename, std::vector<bool> bits,
                  std::ios_base::openmode mode, uint32_t index)
{
   std::ofstream bitmap;
   uint32_t size = bits.size();
   std::ostringstream name;
   name << filename;

   bitmap.open(name.str().c_str(), mode);

   // If rewriting is set, find the offset first
   if (!(mode & std::ofstream::app)) {
      uint32_t size_bytes = (size % 8) ? (size/8 + 1) : (size/8);
      bitmap.seekp(index * size_bytes);
   }

   for (uint64_t i = 0; i < size;) {
      uint8_t byte = 0;

      // Store each 8 bits to byte
      for (uint8_t mask = 1; (mask > 0) && (i < size); i++, mask <<= 1) {
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
   ur_template_t *tmplt = ur_create_input_template(0, "DST_IP,SRC_IP", NULL);

   if (tmplt == NULL) {
      fprintf(stderr, "Error: Template could not be created x.x .\n");
      return -1;
   }

   // Declare progress structure
   NMCM_PROGRESS_DEF;

   // Initialization of default values
   int interval = 300, window = 100;
   bool print_progress = false;
   int granularity = 8;
   int ip_version = 4; // by default, primarily to be deduced from input IPs
   IPaddr_cpp range[2];
   bool rflag = false;
   std::string filename = "bitmap";

   /** Parse Arguments */
   char opt;
   size_t index;
   std::string delim = ",", tmp_range;

   while ((opt = TRAP_GETOPT(argc, argv, module_getopt_string, long_options)) != -1) {
      switch (opt) {
         case 't':
            interval = atoi(optarg);
            if (interval < 0) {
               fprintf(stderr, "Error: Time interval - invalid value %d.\n", interval);
               return 1;
            }
            break;
         case 'w':
            window = atoi(optarg);
            if ((window < 0) || (window > MAX_WINDOW)) {
               fprintf(stderr, "Error: Time window - invalid value %d.\n", window);
               return 1;
            }
            break;
         case 'p':
            print_progress = true;
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
            range[FIRST_ADDR].fromString(tmp_range.substr(0, index));
            tmp_range.erase(0, index + delim.length());
            range[LAST_ADDR].fromString(tmp_range);
            //std:: cout << range[0].toString() << " " << range[1].toString() << std::endl;

            rflag = true;
            break;
         case 'f':
            filename.assign(optarg);
            break;
         default:
            fprintf(stderr, "Error: Unknown parameter -%c.\n", opt);
            return 1;
      }
   }

   // Set printing progress
   if (print_progress) {
      NMCM_PROGRESS_INIT(interval, return 1);
   }

   // If no range entered, used the entire range of IPv4 at /8 by default
   if (!rflag) {
      range[FIRST_ADDR].fromString("0.0.0.0");
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
   // Get time
   //std::time_t start_time = std::time(NULL);
   //struct tm* time_struct = localtime(&start_time);
   //char str_time[20];


   /** Create/open YAML configuration file  and bitmaps */
   FILE *fp = fopen("config.yaml", "a+");
   if (!fp) {
      fprintf(stderr, "Error: File could not be opened/created.\n");
      return 1;
   }
   fclose(fp);

   // Load file to YAML parser
   YAML::Node config_file = YAML::LoadFile("config.yaml");

   // Set bitmap options for server
   config_file[filename]["addresses"]["version"] = (ip_version == 4) ? "IPv4" : "IPv6";
   config_file[filename]["addresses"]["granularity"] = granularity;

   // Remove first and last if they exist (when rewriting, ! <!> appeared)
   if (config_file[filename]["addresses"]["first"]) {
      config_file[filename]["addresses"].remove("first");
   }
   if (config_file[filename]["addresses"]["last"]) {
      config_file[filename]["addresses"].remove("last");
   }
   config_file[filename]["addresses"]["first"] = range[FIRST_ADDR].toString();
   config_file[filename]["addresses"]["last"] = range[LAST_ADDR].toString();

   config_file[filename]["time"]["granularity"] = interval;
   //std::strftime(str_time, sizeof(str_time), "%d-%m-%Y %H:%M:%S", time_struct);
   config_file[filename]["time"]["intervals"] = window;

    std::ofstream fout("config.yaml");
    fout << config_file;
    fout.close();

   // Create bitmap files
   std::ofstream bitmap;
   std::string suffix[3] = {"_s.bmap", "_d.bmap", "_sd.bmap"};
   std::ostringstream name;
   name.str("");

   // If they aren't empty, their content is truncated
   for (int i = 0; i < 3; i++) {
      name << filename << suffix[i];
      bitmap.open(name.str().c_str(),
                      std::ofstream::out | std::ofstream::trunc);
      bitmap.close();
      name.str("");
   }

   // Convert IPs to granularity
   convert_to_granularity(&range[FIRST_ADDR], granularity);
   convert_to_granularity(&range[LAST_ADDR], granularity);

   //std::cout << range[FIRST_ADDR].toString() << " and " << range[LAST_ADDR].toString() << std::endl;


   // Get size of bit vector
   uint32_t vector_size = ip_substraction(range[FIRST_ADDR], range[LAST_ADDR]);

   if ((vector_size == 0) || vector_size > MAX_VECTOR_SIZE) {
      fprintf(stderr, "Error: Address space must be between 1 and 1000 subnets.\n");
      return 1;
   }

   std::vector<std::vector<bool>> bits (3, std::vector<bool>(vector_size, 0));
   bool rewrite = false;
   std::ios_base::openmode mode = std::ofstream::out | std::ofstream::app;

   // Start the alarm
   signal(SIGALRM, IPactivity_signal_handler);
   alarm(interval);

   int intervals = 0; // it is a number mod time window

   /** Main loop */
   while (!stop) {
      const void *rec;
      uint16_t rec_size;
      IPaddr_cpp ip(false);

      // Receive data from input interface
      ret = TRAP_RECEIVE(0, rec, rec_size, tmplt);
      // Handle possible errors
      TRAP_DEFAULT_RECV_ERROR_HANDLING(ret, continue, break);

      // Check SRC and DST IP
      for (int i = 0; i < 2; i++) {
         if (i == SRC) {
            ip.set_IP(&ur_get(tmplt, rec, F_SRC_IP), true);
         } else {
            ip.set_IP(&ur_get(tmplt, rec, F_DST_IP), true);
         }

         // Check IP version
         if (ip.get_version() == ip_version) {
            //std::string origin = ip.toString();
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

      // Each interval, store data to bitmaps
      if (save_vectors) {
         for (int i = 0; i < 3; i++) {
            binary_write(filename + suffix[i], bits[i], mode, intervals);
            bits[i].assign(bits[i].size(), 0);
         }

         // When the buffer is full, turn off appending
         /** Find out if offset without append would do */
         if (!rewrite) {
            std::cout << intervals;
            if ((intervals + 1) == window) {
               rewrite = true;
               mode = mode & (~(std::ofstream::app));
            }
         }

         save_vectors = false;
         intervals = (intervals + 1) % window;
         alarm(interval);
      }

   }

   // Store the rest of data to bitmaps
   for (int i = 0; i < 3; i++) {
      binary_write(filename + suffix[i], bits[i], mode, intervals);
   }
   
   /* Cleanup */
   TRAP_DEFAULT_FINALIZATION();
   FREE_MODULE_INFO_STRUCT(MODULE_BASIC_INFO, MODULE_PARAMS)

   return 0;
}
