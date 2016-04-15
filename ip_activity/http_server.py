#!/usr/bin/python
#coding=UTF-8

## @package html_server
#  Web server for visualising bitmaps in form of images.
#  Author: Katerina Pilatova <xpilat05@stud.fit.vutbr.cz>
#  Date: 2016
#

# Copyright (C) 2016 CESNET
#
# LICENSE TERMS
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
# 3. Neither the name of the Company nor the names of its contributors
#    may be used to endorse or promote products derived from this
#    software without specific prior written permission.
#
# ALTERNATIVELY, provided that this notice is retained in full, this
# product may be distributed under the terms of the GNU General Public
# License (GPL) version 2 or later, in which case the provisions
# of the GPL apply INSTEAD OF those given above.
#
# This software is provided ``as is'', and any express or implied
# warranties, including, but not limited to, the implied warranties of
# merchantability and fitness for a particular purpose are disclaimed.
# In no event shall the company or contributors be liable for any
# direct, indirect, incidental, special, exemplary, or consequential
# damages (including, but not limited to, procurement of substitute
# goods or services; loss of use, data, or profits; or business
# interruption) however caused and on any theory of liability, whether
# in contract, strict liability, or tort (including negligence or
# otherwise) arising in any way out of the use of this software, even
# if advised of the possibility of such damage.
#

import argparse
import BaseHTTPServer
import cgi
import logging
import os
import sys

from __future__ import print_function, division, with_statement

class ip_activity_RequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
   def __init__(self, args):
      ''' Saves options for later use '''
      self.arguments = args

   def do_GET(self):
      ''' Handle a HTTP GET request. '''
      logging.debug('GET %s' % (self.path))

      # Parse URL arguments
      index = self.path.find('?')

      if index >= 0:
         get_path = self.path[:index]
         query = cgi.parse_qs(self.path[index+1:])
      else:
         get_path = self.path

      # Print out logging information about the path and args.
      if 'content-type' in self.headers:
         ctype, _ = cgi.parse_header(self.headers['content-type'])
         logging.debug('TYPE %s' % (ctype))

      logging.debug('PATH %s' % (rpath))
      logging.debug('ARGS %d' % (len(args)))
      if len(args):
         i = 0
         for key in sorted(args):
            logging.debug('ARG[%d] %s=%s' % (i, key, args[key]))
            i += 1

      # Check to see whether the file is stored locally,
      # if it is, display it.

       # Get the file path.
       new_path = ip_activity_RequestHandler.arguments['dir'] + get_path

       dirpath = None
       logging.debug('FILE %s' % (path))

       # If it is a directory look for index.html
       # or process it directly if there are 3
       # trailing slashed.
       if rpath[-3:] == '///':
          dirpath = path
       elif os.path.exists(path) and os.path.isdir(path):
          dirpath = path  # the directory portion
          index_files = ['/index.html', '/index.htm', ]
          for index_file in index_files:
             tmppath = path + index_file
             if os.path.exists(tmppath):
                path = tmppath
                break

       # Allow the user to type "///" at the end to see the
       # directory listing.
       if os.path.exists(path) and os.path.isfile(path):
          # This is valid file, send it as the response
          # after determining whether it is a type that
          # the server recognizes.
          _, ext = os.path.splitext(path)
          ext = ext.lower()
          content_type = {
             '.css': 'text/css',
             '.gif': 'image/gif',
             '.htm': 'text/html',
             '.html': 'text/html',
             '.jpeg': 'image/jpeg',
             '.jpg': 'image/jpg',
             '.js': 'text/javascript',
             '.png': 'image/png',
             '.text': 'text/plain',
             '.txt': 'text/plain',
          }

          # If it is a known extension, set the correct
          # content type in the response.
          if ext in content_type:
             self.send_response(200)  # OK
             self.send_header('Content-type', content_type[ext])
             self.end_headers()

             with open(path) as ifp:
                self.wfile.write(ifp.read())
          else:
             # Unknown file type or a directory.
             # Treat it as plain text.
             self.send_response(200)  # OK
             self.send_header('Content-type', 'text/plain')
             self.end_headers()

             with open(path) as ifp:
                self.wfile.write(ifp.read())
       else:
          if dirpath is None or self.m_opts.no_dirlist == True:
             # Invalid file path, respond with a server access error
             self.send_response(500)  # generic server error for now
             self.send_header('Content-type', 'text/html')
             self.end_headers()

             self.wfile.write('<html>')
             self.wfile.write('  <head>')
             self.wfile.write('    <title>Server Access Error</title>')
             self.wfile.write('  </head>')
             self.wfile.write('  <body>')
             self.wfile.write('    <p>Server access error.</p>')
             self.wfile.write('    <p>%r</p>' % (repr(self.path)))
             self.wfile.write('    <p><a href="%s">Back</a></p>' % (rpath))
             self.wfile.write('  </body>')
             self.wfile.write('</html>')
          else:
             # List the directory contents. Allow simple navigation.
             logging.debug('DIR %s' % (dirpath))

             self.send_response(200)  # OK
             self.send_header('Content-type', 'text/html')
             self.end_headers()

             self.wfile.write('<html>')
             self.wfile.write('  <head>')
             self.wfile.write('    <title>%s</title>' % (dirpath))
             self.wfile.write('  </head>')
             self.wfile.write('  <body>')
             self.wfile.write('    <a href="%s">Home</a><br>' % ('/'));

             # Make the directory path navigable.
             dirstr = ''
             href = None
             for seg in rpath.split('/'):
                if href is None:
                   href = seg
                else:
                   href = href + '/' + seg
                   dirstr += '/'
                dirstr += '<a href="%s">%s</a>' % (href, seg)
             self.wfile.write('    <p>Directory: %s</p>' % (dirstr))

             # Write out the simple directory list (name and size).
             self.wfile.write('    <table border="0">')
             self.wfile.write('      <tbody>')
             fnames = ['..']
             fnames.extend(sorted(os.listdir(dirpath), key=str.lower))
             for fname in fnames:
                self.wfile.write('        <tr>')
                self.wfile.write('          <td align="left">')
                path = rpath + '/' + fname
                fpath = os.path.join(dirpath, fname)
                if os.path.isdir(path):
                   self.wfile.write('            <a href="%s">%s/</a>' % (path, fname))
                else:
                   self.wfile.write('            <a href="%s">%s</a>' % (path, fname))
                self.wfile.write('          <td>&nbsp;&nbsp;</td>')
                self.wfile.write('          </td>')
                self.wfile.write('          <td align="right">%d</td>' % (os.path.getsize(fpath)))
                self.wfile.write('        </tr>')
             self.wfile.write('      </tbody>')
             self.wfile.write('    </table>')
             self.wfile.write('  </body>')
             self.wfile.write('</html>')


def main():
   ''' Main function for the lifecycle of the server. '''

   # Parse arguments
   parser = argparse.ArgumentParser()
   parser.add_argument('-i', '--input', action='store_true', help='Fetch input bitmap.')
   parser.add_argument('-o', '--output', action='store_true', help='Fetch output bitmap.')
   parser.add_argument('-b', '--bidirectional', action='store_true', help='Fetch bidirectional (io) bitmap.')
   parser.add_argument('-a', '--all', action='store_true', help='Fetch all types of bitmaps.')
   parser.add_argument('-p', '--port', type=int, default=8080,
                       help='Server port, (8080 by default)')
   parser.add_argument('-h', '--hostname', type=str, default='localhost',
                       help='Server hostname (localhost by default).')
   parser.add_argument('-d', '--dir', type=str, default='./', required=True,
                       help='Path to directory with web client files (HTML, CSS, JS) (current directory by default).')
   parser.add_argument('-c', '--config', type=str, default='./', required=True,
                       help='Path to configuration file (current directory by default).')
   args = vars(parser.parse_args())

   # Check their validity
   if not os.path.isfile(args['config']):
      print('Configuration file does not exist.', file=sys.stderr)
      sys.exit(1)

   if not os.path.isdir(args['dir']):
      print('Directory for web client files does not exist.', file=sys.stderr)
      sys.exit(1)

   if (args['port'] > 65535) or (args['port'] < 1): # Skip registered?
      print('Port not within allowed range.', file=sys.stderr)
      sys.exit(1)

   # Create the server
   server = BaseHTTPServer.HTTPServer((args['hostname'], args['port']),
                                      ip_activity_RequestHandler)

   # Serve forever
   try:
      server.serve_forever()
   except KeyboardInterrupt:
      pass

   # Close server
   server.server_close()
   

if __name__ == '__main__':
   main()
