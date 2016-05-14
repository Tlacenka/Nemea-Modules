/**
 * \file backend.hpp
 * \brief Header file for backend module.
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

#ifndef IP_ACTIVITY_H
#define IP_ACTIVITY_H

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

/* Macros */
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
#define MAX_INTERVAL 86400
#define MAX_VECTOR_SIZE 1000

#define TIME_LEN 20


/**
 * \brief Write bit vector to file.
 * \param [out] bitmap Target file.
 * \param [in]  bits   Bit vector to be stored;
 * \param [in]  index  Offset of row in bitmap (unit is vector_size);
 * \param [in]  mode   Open mode.
 */
/*http://stackoverflow.com/questions/29623605/how-to-dump-stdvectorbool-in-a-binary-file*/
void binary_write(std::string filename, std::vector<bool> bits,
                  std::ios_base::openmode mode, uint32_t index);

/**
 * \brief Writes value to configuration file.
 * \param [in] configname Name of the configuration file.
 * \param [in] keys       Access path in configuration file structure.
 * \param [in] value      Value to be inserted.
 * \return If the operation is successful, returns true.
 */
bool config_write (std::string configname, std::vector<std::string> keys,
                   std::string value);

/**
 * Formats raw time as string - %d-%m-%Y %H:%M:%S
 * @param [in] raw_time Time as raw seconds.
 * @return Time as a formatted string.
 */
std::string get_formatted_time(time_t raw_time);

#endif
