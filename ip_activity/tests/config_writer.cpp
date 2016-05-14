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

bool test6()
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
   config_write(CONFIGNAME, std::vector<std::string>({"test6",
               "module", "start"}), "2016-05-01 2:01:00");

   config_write(CONFIGNAME, std::vector<std::string>({"test6",
               "time", "intervals"}), "50");
   config_write(CONFIGNAME, std::vector<std::string>({"test6",
               "time", "granularity"}), "200");
   config_write(CONFIGNAME, std::vector<std::string>({"test6",
               "time", "first"}), "2016-05-01 1:01:20");
   config_write(CONFIGNAME, std::vector<std::string>({"test6",
               "time", "window"}), "1234");

   config_write(CONFIGNAME, std::vector<std::string>({"test6",
               "addresses", "first"}), "18.0.0.0");
   config_write(CONFIGNAME, std::vector<std::string>({"test6",
               "addresses", "last"}), "20.0.0.0");
   
   return true;
}

bool test5()
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
   config_write(CONFIGNAME, std::vector<std::string>({"test5",
               "module", "start"}), "2016-05-01 22:33:00");

   config_write(CONFIGNAME, std::vector<std::string>({"test5",
               "time", "intervals"}), "1230");
   config_write(CONFIGNAME, std::vector<std::string>({"test5",
               "time", "granularity"}), "250");
   config_write(CONFIGNAME, std::vector<std::string>({"test5",
               "time", "first"}), "2016-05-01 21:33:20");
   config_write(CONFIGNAME, std::vector<std::string>({"test5",
               "time", "window"}), "200");

   config_write(CONFIGNAME, std::vector<std::string>({"test5",
               "addresses", "first"}), "8.0.0.0");
   config_write(CONFIGNAME, std::vector<std::string>({"test5",
               "addresses", "last"}), "200.0.0.0");
   config_write(CONFIGNAME, std::vector<std::string>({"test5",
               "addresses", "granularity"}), "9");
   
   return true;
}

bool test4()
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
   config_write(CONFIGNAME, std::vector<std::string>({"test4",
               "module", "start"}), "2016-01-05 11:42:00");
   config_write(CONFIGNAME, std::vector<std::string>({"test4",
               "module", "end"}),get_formatted_time(std::time(NULL)));

   config_write(CONFIGNAME, std::vector<std::string>({"test4",
               "time", "intervals"}), "123456789");
   config_write(CONFIGNAME, std::vector<std::string>({"test4",
               "time", "granularity"}), "500");
   config_write(CONFIGNAME, std::vector<std::string>({"test4",
               "time", "first"}), "2016-01-05 11:42:20");
   config_write(CONFIGNAME, std::vector<std::string>({"test4",
               "time", "last"}), get_formatted_time(std::time(NULL)));
   config_write(CONFIGNAME, std::vector<std::string>({"test4",
               "time", "window"}), "1000");

   config_write(CONFIGNAME, std::vector<std::string>({"test4",
               "addresses", "first"}), "123.0.0.0");
   config_write(CONFIGNAME, std::vector<std::string>({"test4",
               "addresses", "last"}), "180.0.0.0");
   config_write(CONFIGNAME, std::vector<std::string>({"test4",
               "addresses", "granularity"}), "8");
   
   return true;
}

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
               "node1", "node2", "node3", "node4", "node5", "node6", "node7"}),
               "123456someothervalue");
   
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
                "now"}), get_formatted_time(std::time(NULL)));
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
      case 4:
         test4();
         break;
      case 5:
         test5();
         break;
      case 6:
         test6();
         break;
      default:
         if (!test1() || !test2() || !test3() || !test4() || !test5() ||
             !test6()) {
            return 1;
         }
         break;
   }

   return 0;
}
