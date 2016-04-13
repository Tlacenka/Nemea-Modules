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

#define IPV4_BYTES 4
#define IPV6_BYTES 16
#define IPV4_BITS 32
#define IPV6_BITS 128

#define IN 0
#define OUT 1
#define INOUT 2

/* Example: ./ip_activity -i "t:12345" ..... */

#define MODULE_BASIC_INFO(BASIC) \
   BASIC("IP Activity module", "This module scans incoming flows and stores info about IP activity in a given range of IP.", 1,0)

#define MODULE_PARAMS(PARAM) \
   PARAM('t', "time_interval", "Time unit for storing data to bitmap (default 5 minutes). [min]", required_argument, "uint32") \
   PARAM('V', "ip_version", "IP version (4 or 6, 4 by default)", no_argument, "none") \
   PARAM('p', "print", "Show progress - print a dot every interval.", no_argument, "none") \
   PARAM('g', "granularity", "Granularity in range of IP addresses (netmask).", required_argument, "uint32") \
   PARAM('r', "range", "Range of processed IP addresses that must correspond chosen granularity (First address,Last address), entire IP space by default.", required_argument, "string") \
   PARAM('f', "filename", "Name of bitmap files.", required_argument, "string")

static int stop = 0;

// Declaration of structure prototype for printing progress
NMCM_PROGRESS_DECL;

// Function to handle SIGTERM and SIGINT signals (used to stop the module)
TRAP_DEFAULT_SIGNAL_HANDLER(stop = 1);

/** TODO alarm signal */

/**
 * \brief Multiplication of characters in string
 * \param [in] n Multiplicator.
 * \param [in] str String to be multiplied
 * \return Multiplied string
 */
/*http://stackoverflow.com/questions/11843226/multiplying-a-string-by-an-int-in-c*/
std::string operator*(const std::string& str, unsigned int n)
{
   std::stringstream result;
   while (n--) {
      result << str;
   }
   return result.str();
}
std::string operator*(unsigned int n, const std::string& str)
{
   return str * n;
}

/**
 * \brief Converts address based on chosen granularity
 * \param [in] addr IP address to be checked.
 * \return True upon success.
 */
void convert_to_granularity (IPaddr_cpp *addr, int granularity) {
   std::vector<uint8_t> bytes = addr->get_bytes();
   int version = addr->get_version();
   // How many zeros at the end
   int zeros = (version == 4) ? (IPV4_BITS - granularity) : (IPV6_BITS - granularity);

   if (zeros == 0) {
      return;
   }

   // Goes from right to left
   for (int i = ((version == 4) ? 3 : 15); i >= 0; i--) {

      // More bytes to go, the byte equals 0
      if (zeros >= 8) {
         bytes[i] = 0;
         zeros -= 8;
      } else if (zeros == 0) { // done
         break;
      } else {
         // Convert needed part
         for (int b = 0; (zeros > 0) && (b < 8) ; b++, zeros--) {
            bytes[i] &= ~(1 << b);
         }
      }
   }

   addr->set_bytes(bytes, true);
   return;
}

/**
 *  \brief Power function for integers.
 *  \param [in] base, exp (exponent)
 *  \return Result of base ^ exp
 */
 /* http://stackoverflow.com/questions/101439/the-most-efficient-way-to-implement-an-integer-based-power-function-powint-int */
int int_power(int base, int exp) {
   int result = 1;
   while (exp) {
      if (exp & 1) {
         result *= base;
      }
      exp >>= 1;
      base *= base;
   }
   return result;
}

/**
 * \brief Return size of address space between two addresses in set granularity
 * \param [in] addr1, addr2 start and end of considered range
 * \param [in] granularity  granularity of addresses inside said range.
 * \return Size of bit vector
 */
 
uint64_t calculate_vector_size (IPaddr_cpp addr1, IPaddr_cpp addr2, int granularity)
{
   // Check IP validity, same version
   if ((addr1.get_version() != addr2.get_version()) ||
       (addr1.get_version() == 0)) {
      return 0;
   }

   int size = addr1.get_bytes().size();

   // Create bytes representation for better handling
   std::vector<uint8_t> addr1_bytes = addr1.get_bytes();
   std::vector<uint8_t> addr2_bytes = addr2.get_bytes();

   if ((addr1_bytes.size() == 0) || (addr2_bytes.size() == 0) ||
       (addr1_bytes.size() != addr2_bytes.size())) {
      return 0;
   }

   // Substraction result
   std::vector<uint8_t> substr_bytes;
   substr_bytes.resize(size);
   uint8_t borrow = 0;

   // Substract IPs (base 256) > each byte = "digit" of the result
   // Go from right to left
   for (int i = size-1; i >= 0; i--) {
      // Normal substraction, no borrow
      if (addr2_bytes[i] >= (addr1_bytes[i] + borrow)) {
         substr_bytes[i] = addr2_bytes[i] - addr1_bytes[i] - borrow;
         borrow = 0;
      } else {
         // Add radix to remain positive result, add borrow
         substr_bytes[i] = (addr2_bytes[i] + 256) - addr1_bytes[i] - borrow;
         borrow = 1;
      }
   }

   // Result in case of  IPv4 (Bk = Byte on index k): 
   // B0 * 2^24 + B1 * 2 ^ 16 + B2 * 2^8 + B3
   // Both addresses were written in said granularity
   // - so it didn't influence the substraction 
   // - and it will cause a remainder 0 when divided by it

   // TODO: Check if it is greater than 2^64 (uint64_max)

   uint64_t result = 0;
   int exp;
   // At first, go after octets fron left to right and add:
   // x * 2 ^ ((32 - (i+1)*8) - (32 - granularity))
   // x * 2 ^ (granularity - (i+1)*8)

   // Go through bytes
   for (int i = 0;  i < size; i++) {
      exp = (i + 1) * 8;

      // Last bit of current byte does not exceed granularity
      if (exp < granularity) {
         result += substr_bytes[i] * int_power(2, granularity - exp);
      } else if (exp == granularity) {
         // Last bit is at subnet limit
         result += substr_bytes[i];
         break;
      } else {
         // Take the remainder to subnet limit, add it up
         // Convert octet to binary
         std::string tmp = std::bitset<8>(substr_bytes[i]).to_string();

         // Keep only part before granularity line
         tmp = tmp.substr(0, 8 - (exp - granularity));

         // Add it to the result
         result += std::strtol(tmp.c_str(), NULL, 2);
         break;
      }
   }

   return result;
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
   int interval = 300;
   bool print_progress = false;
   int granularity = 8;
   int ip_version = 4;
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
            break;
         case 'p':
            print_progress = true;
            break;
         case 'g':
            granularity = atoi(optarg);
            break;
         case 'V':
            ip_version = atoi(optarg);
            if ((ip_version != 4) && (ip_version != 6)) {
               fprintf(stderr, "Error: IP version - bad format.\n");
               return 1;
            }
            break;
         case 'r':
            tmp_range.assign(optarg);
            index = tmp_range.find(delim);

            if (index == std::string::npos) {
               return 1;
            }

            // Convert all IPs to ip_addr_t
            range[FIRST_ADDR].fromString(tmp_range.substr(0, index));
            tmp_range.erase(0, index + delim.length());
            range[LAST_ADDR].fromString(tmp_range);

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

   // Check netmask
   if (((ip_version == 4) && (granularity > IPV4_BITS)) ||
       ((ip_version == 6) && (granularity > IPV6_BITS))) {
      fprintf(stderr, "Error: Granularity - IPv%d netmask value cannot be greater than %d.\n",
              ip_version, ((ip_version == 4) ? 32 : 128));
      return 1;
   }

   // Create mask
   IPaddr_cpp mask;
   std::string tmp_ip = (ip_version == 4) ? "255.255.255.255" :
                        "ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff";
   mask.fromString(tmp_ip);
   convert_to_granularity(&mask, granularity);

   // If no range entered, used the entire range at /8 by default
   if (!rflag) {
      range[FIRST_ADDR].fromString("0.0.0.0");
      range[LAST_ADDR].fromString("255.0.0.0");
   } else {

      // Check if IPs are valid
      if (((ip_version == 4) && (!range[FIRST_ADDR].is_ipv4() ||
                                 !range[LAST_ADDR].is_ipv4())) ||
          ((ip_version == 6) && (!range[FIRST_ADDR].is_ipv6() ||
                                 !range[LAST_ADDR].is_ipv6()))) {

         fprintf(stderr, "Error: IPv%ds inserted as range are not valid.",
                 ip_version);
         return 1;
      }

      // Convert range to granularity
      convert_to_granularity(&range[FIRST_ADDR], granularity);
      convert_to_granularity(&range[LAST_ADDR], granularity);

      std::cout << range[FIRST_ADDR].toString() << " and " << range[LAST_ADDR].toString() << std::endl;

      if (range[FIRST_ADDR] == range[LAST_ADDR]) {
         fprintf(stderr, "Error: Range is smaller than one subnet /%d",
               granularity);
         return 1;
      }
   }

   // Get time
   std::time_t start_time = std::time(NULL);
   struct tm* time_struct = localtime(&start_time);
   char str_time[20];


   /** Create/open YAML configuration file  and bitmaps */
   FILE *fp = fopen("config.yaml", "a+");
   if (!fp) {
      fprintf(stderr, "Error: File could not be opened/created.\n");
      return 1;
   }
   fclose(fp);

   // Load file to YAML parser
   YAML::Node config_file = YAML::LoadFile("config.yaml");

   std::ofstream bitmaps[3];

   // Set bitmap options for server
   config_file[filename]["addresses"]["version"] = (ip_version == 4) ? "IPv4" : "IPv6";
   config_file[filename]["addresses"]["granularity"] = granularity;
   config_file[filename]["addresses"]["min"] = range[FIRST_ADDR].toString();
   config_file[filename]["addresses"]["max"] = range[LAST_ADDR].toString();

   config_file[filename]["time"]["granularity"] = interval;
   std::strftime(str_time, sizeof(str_time), "%d-%m-%Y %H:%M:%S", time_struct);
   config_file[filename]["time"]["beginning"] = str_time;

    std::ofstream fout("config.yaml");
    fout << config_file;

   // Create bitmap files
   std::ostringstream name;

   name << filename << "_i.bmap";
   bitmaps[IN].open(name.str().c_str(),
                    std::ofstream::out | std::ofstream::app);
   name.str("");

   name << filename << "_o.bmap";
   bitmaps[OUT].open(name.str().c_str(),
                     std::ofstream::out | std::ofstream::app);
   name.str("");

   name << filename << "_io.bmap";
   bitmaps[INOUT].open(name.str().c_str(),
                       std::ofstream::out | std::ofstream::app);
   name.str("");

   // Get size of bit vector
   int vector_size = calculate_vector_size(range[FIRST_ADDR],
                                           range[LAST_ADDR], granularity);

   /** Main loop */
   while (!stop) {
      const void *rec;
      uint16_t rec_size;
      IPaddr_cpp ip(false);

      std::vector<bool> bits; // initialized with zeros
      bits.resize(vector_size);

      // Receive data from input interface
      ret = TRAP_RECEIVE(0, rec, rec_size, tmplt);
      // Handle possible errors
      TRAP_DEFAULT_RECV_ERROR_HANDLING(ret, continue, break);

      
      ip.set_IP(&ur_get(tmplt, rec, F_SRC_IP));
      std::cout << "SRC IP: " << ip.toString() << std::endl;

      // Check if IP is in range
      if ((ip >= range[FIRST_ADDR]) && (ip <= range[LAST_ADDR])) {
         // Determine version
         if (ip.is_ipv4()) {
            // 0000:0000:0000:0000:<IPv4>:ffff:ffff - in 9th-12th byte
            // stored in ip.data->ui32[2]
         } else {
            // ...
         }
         // Set bit in vector
      }
      
      ip.set_IP(&ur_get(tmplt, rec, F_DST_IP));
      std::cout << "DST IP: " << ip.toString() << std::endl;

      // Set corresponding bit in vector

      // Set alarm each interval for storing data to bitmap file

   }

   /* Cleanup */
   TRAP_DEFAULT_FINALIZATION();
   FREE_MODULE_INFO_STRUCT(MODULE_BASIC_INFO, MODULE_PARAMS)

   return 0;
}
