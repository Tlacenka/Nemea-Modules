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

#include <stdio.h>
#include <signal.h>
#include <getopt.h>
#include <time.h>
#include <inttypes.h>

#include <fstream>
#include <iostream>
#include <ctime>
#include <string>

#include <libtrap/trap.h>
#include <unirec/unirec.h>
#include <nemea-common.h>
#include <unirec/ipaddr_cpp.h>
#include "fields.h"

#include "yaml-cpp/yaml.h"

UR_FIELDS (
   ipaddr DST_IP,
   ipaddr SRC_IP
)


trap_module_info_t *module_info = NULL;

#define FIRST_ADDR 0
#define LAST_ADDR 1

#define IPV4 0
#define IPv6 1

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
   PARAM('r', "range", "Range of processed IP addresses (First address,Last address), entire IP space by default.", required_argument, "string") \
   PARAM('f', "filename", "Name of bitmap files.", required_argument, "string")

static int stop = 0;

// Declaration of structure prototype for printing progress
NMCM_PROGRESS_DECL;

// Function to handle SIGTERM and SIGINT signals (used to stop the module)
TRAP_DEFAULT_SIGNAL_HANDLER(stop = 1);

/** TODO alarm signal */

int main(int argc, char **argv)
{
   int ret;
   

   // Initialise TRAP
   INIT_MODULE_INFO_STRUCT(MODULE_BASIC_INFO, MODULE_PARAMS)
   TRAP_DEFAULT_INITIALIZATION(argc, argv, *module_info);

   // Register signal handler.
   TRAP_REGISTER_DEFAULT_SIGNAL_HANDLER();

   // Create template
   //ur_template_t *tmplt = ur_create_input_template(0, "DST_IP,SRC_IP,TIME_FIRST,TIME_LAST,PACKETS,SRC_PORT,DST_PORT", NULL);
   ur_template_t *tmplt = ur_create_input_template(0, "DST_IP,SRC_IP", NULL);

   if (tmplt == NULL) {
      fprintf(stderr, "Error: Template could not be created x.x .\n");
      return -1;
   }

   // Declare progress structure, pointer to this struct, initialize progress limit
   NMCM_PROGRESS_DEF;

   // Initialization of default values
   int interval = 300;
   bool print_progress = false;
   int granularity = 32;
   int ip_version = 4;
   IPaddr_cpp range[2];
   bool rflag = false;

   std::string filename = "bitmap";

   // Parse Arguments
   char opt;
   size_t index;
   std::string delim = ",", tmp_range;
   int i;

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
            // Convert all IPs to ip_addr_t
            for (i = 0; ((index = tmp_range.find(delim)) != std::string::npos) && (i < 2); i++) {
               range[i].fromString(tmp_range.substr(0, index));
               tmp_range.erase(0, index + delim.length());
            }
            if (i != 2) {
               fprintf(stderr, "Error: IP range - bad format.\n");
               return 1;
            }
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
   if (((ip_version == 4) && (granularity > 32)) ||
       ((ip_version == 6) && (granularity > 128))) {
      fprintf(stderr, "Error: Granularity - IPv%d netmask bigger than %d.\n",
              ip_version, ((ip_version == 4) ? 32 : 128));
      return 1;
   }

   // If no range entered, used the entire range by default
   if (!rflag) {
      range[0].fromString("0.0.0.0");
      range[1].fromString("255.255.255.255");
   }

   // Get time
   std::time_t start_time = std::time(NULL);
   struct tm* time_struct = localtime(&start_time);
   char str_time[20];

   // Create/open YAML configuration file
   FILE *fp = fopen("config.yaml", "a+");
   if (!fp) {
      fprintf(stderr, "Error: File could not be opened/created.\n");
      return 1;
   }
   fclose(fp);

   // Load file to YAML parser
   YAML::Node config_file = YAML::LoadFile("config.yaml");

   std::fstream bitmaps[3];

   // Set bitmap options for server
   config_file[filename]["addresses"]["version"] = (ip_version == 4) ? "IPv4" : "IPv6";
   config_file[filename]["addresses"]["granularity"] = granularity;
   config_file[filename]["addresses"]["min"] = range[FIRST_ADDR].toString();
   config_file[filename]["addresses"]["max"] = range[LAST_ADDR].toString();

   config_file[filename]["time"]["granularity"] = interval;
   std::strftime(str_time, sizeof(str_time), "%d-%m-%Y %I:%M:%S", time_struct); // ?
   config_file[filename]["time"]["beginning"] = str_time;

    std::ofstream fout("config.yaml");
    fout << config_file;

   // Create bitmap files
   std::ostringstream name;

   name << filename << "_i.bmp";
   bitmaps[IN].open(name.str().c_str());
   name.clear();

   name << filename << "_o.bmp";
   bitmaps[OUT].open(name.str().c_str());
   name.clear();

   name << filename << "_io.bmp";
   bitmaps[INOUT].open(name.str().c_str());
   name.clear();

   // size of bit vector
   // int vector_size = <number of addresses between first and last IP> / granularity;

   /* Main loop */
   while (!stop) {
      const void *rec;
      uint16_t rec_size;
      IPaddr_cpp ip(false);
      // bit vector with size of range/granularity

      // Receive data from input interface
      ret = TRAP_RECEIVE(0, rec, rec_size, tmplt);
      // Handle possible errors
      TRAP_DEFAULT_RECV_ERROR_HANDLING(ret, continue, break);

      // Check if IP is in range
      ip.set_IP(&ur_get(tmplt, rec, F_SRC_IP));
      std::cout << "SRC IP: " << ip.toString() << std::endl;
      ip.set_IP(&ur_get(tmplt, rec, F_DST_IP));
      std::cout << "DST IP: " << ip.toString() << std::endl;

      // Set corresponding bit in vector

      // Set alarm each interval for storing data to bitmap file
      

      // Read FOO and BAR from input record and compute their sum
      //uint32_t baz = ur_get(in_tmplt, in_rec, F_FOO) +
      //               ur_get(in_tmplt, in_rec, F_BAR);

   }

   /* Cleanup */
   TRAP_DEFAULT_FINALIZATION();
   FREE_MODULE_INFO_STRUCT(MODULE_BASIC_INFO, MODULE_PARAMS)

   return 0;
}
