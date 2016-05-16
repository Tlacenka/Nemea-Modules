/*
 * \file frontend.js
 * \brief Frontend - interactive interface
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

// Main function
$(document).ready(function() {

   var update_interval = 30000; // 30 seconds by default

   // Start updating bitmap if online mode
   var timeout_handler = null;
   var mode = '';
   if ($('.bitmap_stats td.mode').html() == 'online') {
      mode = 'online';
      timeout_handler = auto_update();
   } else {
      // Only update bitmap once
      mode = 'offline';
      update_bitmap();
   }

   var time_range_min = Date.parse($('.bitmap_stats td.first_time').text().replace(" ", "T"));
   var time_range_max = Date.parse($('.bitmap_stats td.last_time').text().replace(" ", "T"));

   // IP index and colour initialisation
   // Original bitmap
   var curr_IP = $('.bitmap_stats td.range').html().split(" ")[0];
   var curr_colour = 'black';
   var curr_interval = $('.bitmap_stats td.first_time').text();
   document.getElementById('origin_curr_IP').innerHTML = curr_IP +
                                                  $('.bitmap_stats td.subnet_size').html();
   document.getElementById('origin_curr_interval').innerHTML = curr_interval;
   $('th.origin_curr_colour').css({
      'background': 'black',
      'color': 'white'
   });

   var down_ip = curr_IP;
   var down_int = curr_interval;

   // Initialise IP version
   var ip_version = 4;
   if ($('.bitmap_stats td.range').html().split(" ")[0].indexOf(":") != -1) {
      ip_version = 6;
   }

   // Mouse position for drag event
   var mouse_X = -1;
   var mouse_Y = -1;
   var mouse_down = false;

   // Initialize form values
   $('.bitmap_options input.first_ip').val($('.bitmap_stats td.range').html().split(" ")[0]);
   $('.bitmap_options input.last_ip').val($('.bitmap_stats td.range').html().split(" ")[2]);
   $('.bitmap_options input.first_int').val($('.bitmap_stats td.first_time').text());
   $('.bitmap_options input.last_int').val($('.bitmap_stats td.last_time').text());

   // Hide selected area
   $('#selected').hide();

   // When changing bitmap type, get new bitmap, update CSS
   $('.bitmap_list li').click(function() {

      if (!($(this).hasClass('chosen'))) {

         // Switch class to current type
         $('#' + $(this).closest('ul').attr('id') + ' li.chosen').removeClass();
         $(this).addClass('chosen');

         // Update bitmap immediately
         if (mode === 'online') {
            console.log('online');
            // Restart automatic update
            clearTimeout(timeout_handler);
            auto_update();
         } else {
            // Send one request
            console.log('offline');
            update_bitmap();
         }
      }
   });

   // Call update every interval
   function auto_update() {
      update_bitmap();
      timeout_handler = setTimeout(auto_update, update_interval);
   }

   // Update bitmap by sending GET request
   function update_bitmap() {

      // Filename to be added
      var image = 'images/image_' + get_bitmap_type() + '.png';
      var query = 'update=true&scale=' + get_bitmap_scale('origin').split(" ")[0];
      http_GET(image, set_bitmap, query);
   }

   // Returns bitmap type
   function get_bitmap_type () {

      var value = $('#bitmap_type li.chosen').html();
      var type = '';

      if (value === 'Source IPs') {
         type = 's';
      } else if (value === 'Destination IPs') {
         type = 'd';
      } else if (value === 'Both') {
         type = 'sd';
      }

      return type;
   }

   // Returns scale for both dimensions "<scale for x> <scale for y>"
   function get_bitmap_scale(type) {
      if (type === 'origin') {
         var scale = $('#bitmap_size li.chosen').html().split(":")[0];
         scale = scale + " " + scale;
      } else {
         var scale = $('#selected_time_unit').text() + " " +
                     $('#selected_ip_unit').text();
      }
      return scale;
   }

   // Universal function for all asynchronous GET requests
   function http_GET(url, callback, arguments, content_type)
   {
      // Initialise arguments
      if (typeof(arguments)==='undefined') {
         arguments = "";
      } else if (arguments.length > 0) {
         url = url + "?" + arguments;
      }
      if (typeof(content_type)==='undefined') {
         content_type = 'application/x-www-form-urlencoded';
      }

      // Create request
      var http_request = new XMLHttpRequest();
      http_request.open('GET', url, true);
      http_request.onreadystatechange = function() {
         if ((http_request.readyState == 4) && (http_request.status == 200)) {
            callback(http_request);
         } else if ((http_request.readyState == 4) && (http_request.status == 404)) {
            console.log('Response 404: Bitmap not found');
         }
      }

      // Send request
      http_request.send();
   }


   // Validate and submit form
   $('.submit').click(function(event) {
      event.preventDefault();

      // Create http GET request

      // Get area parameters
      var type = get_bitmap_type(),
          first_ip = $('#bitmap_form input.first_ip').val(),
          last_ip = $('#bitmap_form input.last_ip').val(),
          first_int = Date.parse($('#bitmap_form input.first_int').val().replace(" ", "T")), 
          last_int = Date.parse($('#bitmap_form input.last_int').val().replace(" ", "T"));

      // Validate time range
      if (isNaN(first_int) || isNaN(first_int) ||
         (first_int < time_range_min) || (first_int > time_range_max) ||
         (last_int < time_range_min) || (last_int > time_range_max)) {
         //console.log("Inserted: " + first_int + " " + last_int);
         //console.log("Allowed: " + time_range_min + " " + time_range_max);
         alert('Intervals must be between ' + $('#bitmap_form input.first_int').val().replace(" ", "T") +
               ' and ' + $('#bitmap_form input.last_int').val().replace(" ", "T") + '.');
         return;
      }
      if (parseInt(first_int) == parseInt(last_int)) {
         alert('Size of interval range must be greater than 0.');
         return;
      }
      // Validate IP range
      if (!compare_ips(first_ip, last_ip) ||
          !compare_ips($('.bitmap_stats td.range').html().split(" ")[0], first_ip) ||
          !compare_ips(last_ip, $('.bitmap_stats td.range').html().split(" ")[2])) {
         alert('IPs muset be between ' + $('.bitmap_stats td.range').html().split(" ")[0] +
              ' and ' + $('.bitmap_stats td.range').html().split(" ")[2]);
         return;
      }
      if (first_ip == last_ip) {
         alert('Number of IP range must be greater than 0.');
         return;
      }

      // Send GET request
      var arguments = 'select_area=true' +
                      '&bitmap_type=' + type +
                      '&first_ip=' +  first_ip +
                      '&last_ip=' +  last_ip +
                      '&first_int=' +  $('#bitmap_form input.first_int').val() +
                      '&last_int=' + $('#bitmap_form input.last_int').val();

      http_GET("", set_selected_area, arguments);

      // Update characteristics of selected area
      $('#selected').show();
      document.getElementById('selected_type').innerHTML = $('#bitmap_type li.chosen').html();
      document.getElementById('selected_ip_range').innerHTML = first_ip + ' - ' + last_ip;
      document.getElementById('selected_int_range_first').innerHTML = $('#bitmap_form input.first_int').val();
      document.getElementById('selected_int_range_last').innerHTML = $('#bitmap_form input.last_int').val();

      // Set current position
      var curr_IP = $('.selected_stats #selected_ip_range').html().split(" ")[0];
      var curr_colour = 'black';
      document.getElementById('selected_curr_IP').innerHTML = curr_IP +
                                                     $('.bitmap_stats td.subnet_size').html();
      document.getElementById('selected_curr_interval').innerHTML = $('.selected_stats #selected_int_range_first').text();
      $('th.selected_curr_colour').css({
         'background': 'black',
         'color': 'white'
      });

   
   });

   // Sets up selected area, inserts image
   function set_selected_area(http_request) {

      if (http_request.getResponseHeader('Bitmap') === 'ok') {
         // Add selected section
         $('#selected').css("display", "block");
         $('#origin').css("padding-bottom", "0");
   
         // Remove previous image if exists
         if ($('#selected_area').has('img')) {
            $('#selected_area img').remove();
         }
   
         // Set selected area image
         $('#selected_area').show();
         $('#selected_area').html('<img class="hover_coords selected_area" alt="Activity Image" src="data:image/png;base64,' + http_request.responseText + '" />');
         $('#selected_area img').css({
            'border': '1px solid SlateGray',
            'display': 'block',
            'margin': 'auto'
         });
         $('#selected_area').css({
            'margin-top': '50px'
         });

         // Set scale ratio
         document.getElementById('selected_time_unit').innerHTML = http_request.getResponseHeader('Time_unit');
         document.getElementById('selected_ip_unit').innerHTML = http_request.getResponseHeader('IP_unit');

      }
   }

   // Set bitmap if sent
   function set_bitmap(http_request)
   {
      // Change image
      if (http_request.getResponseHeader('Bitmap') === 'ok') {
         $('#bitmap_inner').show();
         $('#bitmap_inner img').remove();
         $('#bitmap_inner').html('<img class="hover_coords origin" alt="Activity Image" src="data:image/png;base64,' + http_request.responseText + '" />');
         $('#bitmap_inner img').css({
            'border': '1px solid SlateGray',
            'display': 'block',
            'margin': 'auto'
         });
         $('#bitmap_inner').css({
            'margin-top': '50px'
         });

         // Update characteristics

         // Number of visible and total intervals
         if (parseInt($('#visible_int').text()) <
            parseInt($('.bitmap_stats td.time_window').html().split(" ")[0])) {
            if (parseInt(http_request.getResponseHeader('Interval_range')) <= 
                parseInt($('.bitmap_stats td.time_window').html().split(" ")[0])) {
               document.getElementById("visible_int").innerHTML = http_request.getResponseHeader('Interval_range');
            } else {
               document.getElementById("visible_int").innerHTML = parseInt($('.bitmap_stats td.time_window').html().split(" ")[0]);
            }

            //console.log($('#visible_int').text());
            //console.log($('.bitmap_stats td.time_window').html().split(" ")[0]);
         }

         document.getElementById("total_int").innerHTML = http_request.getResponseHeader('Interval_range');

         // In online mode, update first and last time
         if ($('.bitmap_stats td.mode').html() == 'online') {
            time_range_min = Date.parse(http_request.getResponseHeader('Time_first').replace(" ", "T"));
            time_range_max = Date.parse(http_request.getResponseHeader('Time_last').replace(" ", "T"));

            document.getElementById('stat_first_time').innerHTML = http_request.getResponseHeader('Time_first');
            document.getElementById('stat_last_time').innerHTML = http_request.getResponseHeader('Time_last');
            $('.bitmap_options input.first_int').val(http_request.getResponseHeader('Time_first'));
            $('.bitmap_options input.last_int').val(http_request.getResponseHeader('Time_last'));

            // Online > offline
            if (http_request.getResponseHeader('Mode') == 'offline') {
               document.getElementById("mode").innerHTML = http_request.getResponseHeader('Mode');
               mode = 'offline';
               console.log("change to offline");
               // Cancel periodic update
               clearTimeout(timeout_handler);
            }
         }
      }
   }

   // Set IP index and cell colour
   function set_curr_position(http_request) {
      curr_IP = http_request.getResponseHeader('IP_index');
      curr_colour = http_request.getResponseHeader('Cell_colour');
      curr_interval = http_request.getResponseHeader('Time_index');
   }


   // Show parameters for each pair of coordinates - images with class 'hover_coords'
   // Also when dragging, extend rectangle
   // http://jsfiddle.net/pSVXz/12/
   $(document).on('mousemove', 'img.hover_coords', function(event) {

      // Displaying coordinates
      var x = parseInt(event.pageX - $(this).position().left - 1);
      var y = parseInt(event.pageY - $(this).position().top - 1);

      // Do not update position if it is out of boundaries (frame)
      if ((x < 1) || (y < 1) || (x >= $(this).width()) ||
          (y >= $(this).height())) {
         return;
      }

      // Origin x selected
      var classname = '';
      if ($(this).hasClass('origin')) {
         classname = 'origin';
      } else if ($(this).hasClass('selected_area')) {
         classname = 'selected';
      }

      // Adjust scale
      var scale = get_bitmap_scale(classname);
      x = Math.floor(x / parseInt(scale.split(" ")[0]));
      y = Math.floor(y / parseInt(scale.split(" ")[1]));

      // Get IP at index
      var first_ip = '';
      var first_time = '';
      if (classname === 'origin') {
         first_ip = $('.bitmap_stats td.range').html().split(" ")[0];
         first_time = $('.bitmap_stats td.first_time').text();
      } else {
         first_ip= $('.selected_stats #selected_ip_range').html().split(" ")[0];
         first_time = $('.selected_stats #selected_int_range_first').text();
      }

      var arguments = 'calculate_index=true' +
                      '&bitmap_type=' + classname +
                      '&first_ip=' + first_ip +
                      '&ip_index=' + y +
                      '&first_time=' + first_time +
                      '&time_index=' + x;

      http_GET('', set_curr_position, arguments);

      // Update current position
      if (curr_IP === 'undefined') {
          document.getElementById(classname + '_curr_IP').innerHTML = curr_IP;
      } else {
         document.getElementById(classname + '_curr_IP').innerHTML = curr_IP +
                                     $('.bitmap_stats td.subnet_size').html();
      }
      document.getElementById(classname + '_curr_interval').innerHTML = curr_interval;

      $('th.' + classname + '_curr_colour').css({
         'background': ((curr_colour === 'gray') ? 'DimGray' : curr_colour),
         'color': ((curr_colour === 'black') || (curr_colour === 'gray') ? 'white' : 'black')
      });

      // Dragging
      if (mouse_down) {
         var width = Math.abs(mouse_X - event.pageX);
         var height = Math.abs(mouse_Y - event.pageY);
         $('#rectangle').css({
            'width': width - 1,
            'height': height - 1,
            'left': ((event.pageX < mouse_X) ? (mouse_X - width) : mouse_X),
            'top': ((event.pageY < mouse_Y) ? (mouse_Y - height) : mouse_Y)
         });
      }
   });

   
   // Drag image function - updates values in submit
   $( '<div id="rectangle" class="hover_coords"></div>' ).appendTo('#main')[0];

   $(document).on('mousedown', 'img.hover_coords.origin', function(event) {
      mouse_down = true;
      event.preventDefault();
      mouse_X = event.pageX;
      mouse_Y = event.pageY;
      $('#rectangle').css({
         'border': '2px solid DeepSkyBlue',
         'background': 'transparent',
         'position': 'absolute',
         'top': mouse_Y,
         'left': mouse_X,
         'width': 0,
         'height': 0
      }).show();

      // Save values
      down_ip = curr_IP;
      down_int = curr_interval;
   });

      // When mouse is up, detach rectangle
   $(document).on('mouseup', 'html', function() {

      if (mouse_down) {
         // Insert rectangle values to Options
         var ip1 = down_ip;
         var ip2 = curr_IP;         


         // Handle undefined
         // If both IPs are undefined, set them to the whole range
         if ((ip1 === 'undefined') && (ip2 === 'undefined')) {
            ip1 = $('.bitmap_stats td.range').text().split(" ")[0];
            ip2 = $('.bitmap_stats td.range').text().split(" ")[2];
         // If one of them, set it to the maximum IP
         } else if (ip1 === 'undefined') {
            ip1 = $('.bitmap_stats td.range').text().split(" ")[2];
         } else if (ip2 === 'undefined') {
            ip2 = $('.bitmap_stats td.range').text().split(" ")[2];
         }

         // Is ip1 < ip2 ?
         if (compare_ips(ip1, ip2)) {
            $('.bitmap_options input.first_ip').val(ip1);
            $('.bitmap_options input.last_ip').val(ip2);
         } else {
            $('.bitmap_options input.first_ip').val(ip2);
            $('.bitmap_options input.last_ip').val(ip1);
         }

   
         var int1 = down_int;
         var int2 = curr_interval;
         console.log("before:" + down_int + " and " + curr_interval);

         // Handle undefined
         // If both intervals are undefined, set them to the whole range
         if ((int1 === 'undefined') && (int2 === 'undefined')) {
            int1 = $('.bitmap_stats td.first_time').text();
            int2 = $('.bitmap_stats td.last_time').text();
         // If one of them, set it to the maximum interval
         } else if (int1 === 'undefined') {
            int1 = $('.bitmap_stats td.last_time').text();
         } else if (int2 === 'undefined') {
            int2 = $('.bitmap_stats td.last_time').text();
         }

         if (Date.parse(int1.replace(" ", "T")) <=
             Date.parse(int2.replace(" ", "T"))) {
            $('.bitmap_options input.first_int').val(int1);
            $('.bitmap_options input.last_int').val(int2);
         } else {
             $('.bitmap_options input.first_int').val(int2);
            $('.bitmap_options input.last_int').val(int1);
         }
         console.log("after:" + down_int + " and " + curr_interval);

         mouse_down = false;
         $('#rectangle').hide();
         mouse_X = -1;
         mouse_Y = -1;
      }
   });

   // Returns statement, if ip1 <= ip2
   function compare_ips(ip1, ip2) {

      // Compare IPs
      if (ip_version == 4) {
         var ip1_list = ip1.split('.');
         var ip2_list = ip2.split('.');
         var len = ip1_list.length;

         for (var i = 0; i < len; i++) {
            if (parseInt(ip1_list[i]) < parseInt(ip2_list[i])) {
               return true;
            } else if (parseInt(ip1_list[i]) > parseInt(ip2_list[i])) {
               return false;
            }
         }
      } else { // IPv6
         var ip1_list = ip1.split(':');
         var ip2_list = ip2.split(':');
         // Normalize
         var tmp = ip1_list;
         for (var i = 0; i < 2; i++, tmp = ip2_list) {
            var len = tmp.length;
            // Get rid of grouped ::, normalize to length of 4
            for (var j = 0; j < len; j++) {
               if (tmp[j] != '') {
                  tmp[j] = ('0000' + tmp[j]).substr(-4);
               } else {
                  tmp[j] = '0000';
               }
            }

            if (i == 0) {
               ip1_list = tmp;
            } else {
               ip2_list = tmp;
            }
         }

         // Compare normalized IPv6
         var len = ip1_list.length;

         for (var i = 0; i < len; i++) {
            if (parseInt(ip1_list[i], 16) < parseInt(ip2_list[i], 16)) {
               return true;
            } else if (parseInt(ip1_list[i], 16) > parseInt(ip2_list[i], 16)) {
               return false;
            }
         }
      }

      return true;
   }

});

