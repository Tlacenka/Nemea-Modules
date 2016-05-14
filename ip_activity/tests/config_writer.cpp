/**
 * \file config_writer.cpp
 * \brief Test file for writing data to configuration file.
 * \author Katerina Pilatova <xpilat05@stud.fit.vutbr.cz>
 * \date 2016
 */

#include <getopt.h>
#include <inttypes.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#include <ctime>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <utility>

#include "yaml-cpp/yaml.h"
#include "../ip_activity.hpp"

#define CONFIGNAME "config_test.yaml"

bool test3()
{
   // Open/create existing file
   std::fstream config;
   if (std::ifstream(CONFIGNAME).good()) {
      config.open(CONFIGNAME, std::ios_base::out | std::ios_base::in);
   } else {
      config.open(CONFIGNAME, std::ios_base::out | std::ios_base::trunc);
   }

   if (!config.is_open()) {
      fprintf(stderr, "Error: File could not be opened/created.\n");
      return false;
   }
   config.close();

   // Write to file
   config_write(CONFIGNAME, std::vector<std::string>({"test3",
               "node1", "node2"}), "123456someothervalue");
   
   return true;
}

/* Write 10 rows of 95x"1" + 1x"0" as padding*/
bool test2()
{
   // Open/create existing file
   std::fstream config;
   if (std::ifstream(CONFIGNAME).good()) {
      config.open(CONFIGNAME, std::ios_base::out | std::ios_base::in);
   } else {
      config.open(CONFIGNAME, std::ios_base::out | std::ios_base::trunc);
   }

   if (!config.is_open()) {
      fprintf(stderr, "Error: File could not be opened/created.\n");
      return false;
   }
   config.close();

   // Write to file
   config_write(CONFIGNAME, std::vector<std::string>({"test2",
                "time", "now"}), get_formatted_time(std::time(NULL)));
   return true;
}

/* Writes 10 rows of 16x"1" */
bool test1 ()
{
   // Open/create existing file
   std::fstream config;
   if (std::ifstream(CONFIGNAME).good()) {
      config.open(CONFIGNAME, std::ios_base::out | std::ios_base::in);
   } else {
      config.open(CONFIGNAME, std::ios_base::out | std::ios_base::trunc);
   }

   if (!config.is_open()) {
      fprintf(stderr, "Error: File could not be opened/created.\n");
      return false;
   }
   config.close();

   // Write to file
   config_write(CONFIGNAME, std::vector<std::string>({"test1"}), "somevalue");
   return true;
}

int main(int argc, char** argv) {

   int test_nr = 0;

   // Parse arguments
   char opt;
   
   while ((opt = getopt(argc, argv, "t:")) != -1) {
      switch (opt) {
         case 't':
            test_nr = atoi(optarg);
            break;
         default:
            fprintf(stderr, "Error: Unknown parameter -%c.\n", opt);
            return 1;
      }
   }

   // Perform tests
   switch (test_nr) {
      case 1:
         if (!test1()) return 1;
         break;
      case 2:
         if (!test2()) return 1;
         break;
      case 3:
         test3();
         break;
      default:
         if (!test1() || !test2() || !test3()) return 1;
         break;
   }

   return 0;
}
