/**
 * \file dnsplugin.h
 * \brief Plugin for parsing DNS traffic.
 * \author Jiri Havranek <havraji6@fit.cvut.cz>
 * \date 2015
 */
/*
 * Copyright (C) 2014-2015 CESNET
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

#ifndef DNSPLUGIN_H
#define DNSPLUGIN_H

#include <string>
#include <sstream>

#include "fields.h"
#include "flowifc.h"
#include "flowcacheplugin.h"
#include "packet.h"
#include "flow_meter.h"

using namespace std;

#define DNS_TYPE_A      1
#define DNS_TYPE_NS     2
#define DNS_TYPE_CNAME  5
#define DNS_TYPE_SOA    6
#define DNS_TYPE_PTR    12
#define DNS_TYPE_HINFO  13
#define DNS_TYPE_MINFO  14
#define DNS_TYPE_MX     15
#define DNS_TYPE_TXT    16
#define DNS_TYPE_ISDN   20
#define DNS_TYPE_AAAA   28
#define DNS_TYPE_SRV    33
#define DNS_TYPE_DNAME  39
#define DNS_TYPE_DS     43
#define DNS_TYPE_RRSIG  46
#define DNS_TYPE_DNSKEY 48

#define DNS_TYPE_OPT    41

#define DNS_HDR_GET_QR(flags)       (((flags) & (0x1 << 15)) >> 15) // Return question/answer bit.
#define DNS_HDR_GET_OPCODE(flags)   (((flags) & (0xF << 11)) >> 11) // Return opcode bits.
#define DNS_HDR_GET_AA(flags)       (((flags) & (0x1 << 10)) >> 10) // Return authoritative answer bit.
#define DNS_HDR_GET_TC(flags)       (((flags) & (0x1 << 9)) >> 9) // Return truncation bit.
#define DNS_HDR_GET_RD(flags)       (((flags) & (0x1 << 8)) >> 8) // Return recursion desired bit.
#define DNS_HDR_GET_RA(flags)       (((flags) & (0x1 << 7)) >> 7) // Return recursion available bit.
#define DNS_HDR_GET_Z(flags)        (((flags) & (0x1 << 6)) >> 6) // Return reserved bit.
#define DNS_HDR_GET_AD(flags)       (((flags) & (0x1 << 5)) >> 5) // Return authentication data bit.
#define DNS_HDR_GET_CD(flags)       (((flags) & (0x1 << 4)) >> 4) // Return checking disabled bit.
#define DNS_HDR_GET_RESPCODE(flags) ((flags) & 0xF) // Return response code bits.

#define DNS_HDR_LENGTH 12

/**
 * \brief Struct containing DNS header fields.
 */
struct dns_hdr {
   uint16_t id;
   union {
      struct {
#if __BYTE_ORDER == __LITTLE_ENDIAN
         uint16_t recursion_desired:1;
         uint16_t truncation:1;
         uint16_t authoritative_answer:1;
         uint16_t op_code:4;
         uint16_t query_response:1;
         uint16_t response_code:4;
         uint16_t checking_disabled:1;
         uint16_t auth_data:1;
         uint16_t reserved:1;
         uint16_t recursion_available:1;
#elif __BYTE_ORDER == __BIG_ENDIAN
         uint16_t query_response:1;
         uint16_t op_code:4;
         uint16_t authoritative_answer:1;
         uint16_t truncation:1;
         uint16_t recursion_desired:1;
         uint16_t recursion_available:1;
         uint16_t reserved:1;
         uint16_t auth_data:1;
         uint16_t checking_disabled:1;
         uint16_t response_code:4;
#endif
      };
      uint16_t flags;
   };
   uint16_t question_rec_cnt;
   uint16_t answer_rec_cnt;
   uint16_t name_server_rec_cnt;
   uint16_t additional_rec_cnt;
};

/**
 * \brief Struct containing DNS question.
 */
struct dns_question {
   /* name */
   uint16_t qtype;
   uint16_t qclass;
};

/**
 * \brief Struct containing DNS answer.
 */
struct dns_answer {
   /* name */
   uint16_t atype;
   uint16_t aclass;
   uint32_t ttl;
   uint16_t rdlength;
   /* rdata */
};

/**
 * \brief Struct containing DNS SOA record.
 */
struct dns_soa {
   /* primary NS */
   /* admin MB */
   uint32_t serial;
   uint32_t refresh;
   uint32_t retry;
   uint32_t expiration;
   uint32_t ttl;
};

/**
 * \brief Struct containing DNS SRV record.
 */
struct dns_srv {
   /* _service._proto.name*/
   uint16_t priority;
   uint16_t weight;
   uint16_t port;
   /* target */
};

/**
 * \brief Struct containing DNS DS record.
 */
struct dns_ds {
   uint16_t keytag;
   uint8_t algorithm;
   uint8_t digest_type;
   /* digest */
};

/**
 * \brief Struct containing DNS RRSIG record.
 */
struct dns_rrsig {
   uint16_t type;
   uint8_t algorithm;
   uint8_t labels;
   uint32_t ttl;
   uint32_t sig_expiration;
   uint32_t sig_inception;
   uint16_t keytag;
   /* signer's name */
   /* signature */
};

/**
 * \brief Struct containing DNS DNSKEY record.
 */
struct dns_dnskey {
   uint16_t flags;
   uint8_t protocol;
   uint8_t algorithm;
   /* public key */
};

/**
 * \brief Flow record extension header for storing parsed DNS packets.
 */
struct FlowRecordExtDNS : FlowRecordExt {
   uint16_t dns_id;
   uint16_t dns_answers;
   uint8_t dns_rcode;
   char dns_qname[128];
   uint16_t dns_qtype;
   uint16_t dns_qclass;
   uint32_t dns_rr_ttl;
   uint16_t dns_rlength;
   char dns_data[160];
   uint16_t dns_psize;
   uint8_t dns_do;

   /**
    * \brief Constructor.
    */
   FlowRecordExtDNS() : FlowRecordExt(dns), dns_qtype(0)
   {
      dns_id = 0;
      dns_answers = 0;
      dns_rcode = 0;
      dns_qname[0] = 0;
      dns_qtype = 0;
      dns_qclass = 0;
      dns_rr_ttl = 0;
      dns_rlength = 0;
      dns_data[0] = 0;
      dns_psize = 0;
      dns_do = 0;
   }

   virtual void fillUnirec(ur_template_t *tmplt, void *record)
   {
         ur_set(tmplt, record, F_DNS_ID, dns_id);
         ur_set(tmplt, record, F_DNS_ANSWERS, dns_answers);
         ur_set(tmplt, record, F_DNS_RCODE, dns_rcode);
         ur_set_string(tmplt, record, F_DNS_NAME, dns_qname);
         ur_set(tmplt, record, F_DNS_QTYPE, dns_qtype);
         ur_set(tmplt, record, F_DNS_CLASS, dns_qclass);
         ur_set(tmplt, record, F_DNS_RR_TTL, dns_rr_ttl);
         ur_set(tmplt, record, F_DNS_RLENGTH, dns_rlength);
         //ur_set_string(tmplt, record, F_DNS_RDATA, dns_data);
         ur_set_var(tmplt, record, F_DNS_RDATA, dns_data, dns_rlength);
         ur_set(tmplt, record, F_DNS_PSIZE, dns_psize);
         ur_set(tmplt, record, F_DNS_DO, dns_do);
   }
};

/**
 * \brief Flow cache plugin for parsing DNS packets.
 */
class DNSPlugin : public FlowCachePlugin
{
public:
   DNSPlugin(const options_t &module_options);
   DNSPlugin(const options_t &module_options, vector<plugin_opt> plugin_options);
   int post_create(FlowRecord &rec, const Packet &pkt);
   int pre_update(FlowRecord &rec, Packet &pkt);
   void finish();
   std::string get_unirec_field_string();

private:
   bool parse_dns(const char *data, int payload_len, FlowRecordExtDNS *rec);
   void add_ext_dns(const char *data, int payload_len, FlowRecord &rec);
   std::string get_name(const char *begin, const char *data, int counter) const;
   void process_srv(string &str) const;
   void process_rdata(const char *data_begin, const char *record_begin, const char* data, std::ostringstream &rdata, uint16_t type, size_t length) const;
   size_t get_name_length(const char *data, bool total_length) const;

   bool statsout;       /**< Indicator whether to print stats when flow cache is finishing or not. */
   uint32_t queries;    /**< Total number of parsed DNS queries. */
   uint32_t responses;  /**< Total number of parsed DNS responses. */
   uint32_t total;      /**< Total number of parsed DNS packets. */
};

#endif
