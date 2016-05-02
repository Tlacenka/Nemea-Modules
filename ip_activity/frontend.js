/*
 * Subject: IP Activity Analysis
 * Brief: JS for web client visualising data to user.
 * Author: Katerina Pilatova
 * Date: 2016
 */

// Main function
$(document).ready(function() {

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

   // TODO with each update, decrease chosen interval range? or...?

   // IP index and colour initialisation
   // Original bitmap
   var curr_index = $('.bitmap_stats td.range').html().split(" ")[0];
   var curr_colour = 'black';
   document.getElementById('origin_curr_IP').innerHTML = curr_index +
                                                  $('.bitmap_stats td.subnet_size').html();
   document.getElementById('origin_curr_interval').innerHTML = 0;
   $('th.origin_curr_colour').css({
      'background': 'black',
      'color': 'white'
   });

   var down_ip = curr_index;
   var down_int = 0;

   // Initialise limits for input
   var ip_version = 4;
   if ($('.bitmap_stats td.range').html().split(" ")[0].indexOf(":") != -1) {
      ip_version = 6;
   }
   var ip_max = ((ip_version == 4) ? 32 : 128);
   var interval_max = 86400; // a day
   var int_range_max = $('.bitmap_stats td.int_range').html().split(" ")[0];

   // Mouse position for drag event
   var mouse_X = -1;
   var mouse_Y = -1;
   var mouse_down = false;

   // Initialize form values
   $('.bitmap_options input.granularity').val(parseInt(
                                       $('.bitmap_stats td.subnet_size').html().slice("1")));
   $('.bitmap_options input.first_ip').val($('.bitmap_stats td.range').html().split(" ")[0]);
   $('.bitmap_options input.last_ip').val($('.bitmap_stats td.range').html().split(" ")[2]);
   $('.bitmap_options input.time_interval').val(parseInt($('.bitmap_stats td.time_interval').html().split(" ")[0]));
   $('.bitmap_options input.first_int').val(0);
   $('.bitmap_options input.last_int').val(parseInt($('.bitmap_stats td.int_range').html().split(" ")[0]));

   $('#selected').hide();

   // When changing bitmap type, get new bitmap, update CSS
   $('#bitmap_type li').click(function() {

      if (!($(this).hasClass('chosen_type'))) {

         // Switch class to current type
         $('#bitmap_type li.chosen_type').removeClass();
         $(this).addClass('chosen_type');

         // Update bitmap immediately
         if (mode == 'online') {
            // Restart automatic update
            clearTimeout(timeout_handler);
            auto_update();
         } else {
            // Send one request
            update_bitmap();
         }
      }
   });

   // Call update every interval
   function auto_update() {
      update_bitmap();
      var interval = parseInt($('.bitmap_stats td.time_interval').html().split(" ")[0])*1000;
      timeout_handler = setTimeout(auto_update, interval);
   }

   // Update bitmap by sending GET request
   function update_bitmap() {

      // Filename to be added
      var image = 'images/image_' + get_bitmap_type() + '.png';
      http_GET(image, set_bitmap, 'update=true');
   }

   // Returns bitmap type
   function get_bitmap_type () {

      var value = $('#bitmap_type li.chosen_type').html();
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
            //alert("200")
            callback(http_request);
         } else if ((http_request.readyState == 4) && (http_request.status == 404)) {
            alert('404');
         }
      }

      // Send request
      http_request.send();
   }


   // Handle form submit TODO
   $('.submit').click(function(event) {
      event.preventDefault();

      // Create http GET request

      // Get area parameters
      var type = get_bitmap_type(),
          subnet_size = $('#bitmap_form input.granularity').val(),
          first_ip = $('#bitmap_form input.first_ip').val(),
          last_ip = $('#bitmap_form input.last_ip').val(),
          first_int = $('#bitmap_form input.first_int').val(), 
          last_int = $('#bitmap_form input.last_int').val(),
          time_interval = $('#bitmap_form input.time_interval').val();

      // Validate parameters
      if (parseInt(subnet_size) > ip_max) {
         alert('Subnet size must be between 0 and ' + ip_max);
         return;
      }
      if (parseInt(time_interval) > interval_max) {
         alert('Time interval is too big (maximum is one day - ' + interval_max + ' seconds)');
         return;
      }
      if ((parseInt(first_int) < 0) || (parseInt(last_int) > int_range_max) ||
          (parseInt(first_int) > parseInt(last_int))) {
         alert('Intervals must be between 0 and ' + int_range_max + '.');
         return;
      }
      if (parseInt(first_int) == parseInt(last_int)) {
         alert('Size of interval range must be greater than 0.');
         return;
      }
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
                      '&subnet_size=' +  subnet_size +
                      '&first_ip=' +  first_ip +
                      '&last_ip=' +  last_ip +
                      '&first_int=' +  first_int +
                      '&last_int=' + last_int +
                      '&time_interval=' + time_interval;

      http_GET("", set_selected_area, arguments);

      // Update characteristics of selected area
      $('#selected').show();
      document.getElementById('selected_type').innerHTML = $('#bitmap_type li.chosen_type').html();
      document.getElementById('selected_subnet_size').innerHTML = '/' + subnet_size;
      document.getElementById('selected_ip_range').innerHTML = first_ip + ' - ' + last_ip;
      document.getElementById('selected_int_range').innerHTML = first_int + ' - ' + last_int;
      document.getElementById('selected_time_interval').innerHTML = time_interval + ' seconds';

      // Set current position
      var curr_index = $('.selected_stats #selected_ip_range').html().split(" ")[0];
      var curr_colour = 'black';
      document.getElementById('selected_curr_IP').innerHTML = curr_index +
                                                     $('.selected_stats #selected_subnet_size').html();
      document.getElementById('selected_curr_interval').innerHTML = $('.selected_stats #selected_int_range').html().split(" ")[0];
      $('th.selected_curr_colour').css({
         'background': 'black',
         'color': 'white'
      });

   
   });

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
         $('#selected_area').html('<img class="hover_coords selected_area" src="data:image/png;base64,' + http_request.responseText + '" />');
         $('#selected_area img').css({
            'border': '1px solid SlateGray',
            'display': 'block',
            'margin': 'auto'
         });
         $('#selected_area').css({
            'margin-top': '50px'
         });
      }
   }

   // Change text in input
   $('img.btn').click(function(){
      var value = parseInt($(this).siblings('input').val());
      var classname = $(this).siblings('input').attr('class');
      if ($(this).closest('tr').hasClass('int_range')) {
         if ($(this).hasClass('first_int')) {
            value = parseInt($(this).siblings('input.first_int').val());
            classname = 'first_int';
         } else if ($(this).hasClass('last_int')) {
            value = parseInt($(this).siblings('input.last_int').val());
            classname = 'last_int'
         }
      }

      // Get limit based on type of input
      var limit = 0;
      
      if (classname === 'granularity') {
         limit = ip_max;
      } else if (classname === 'time_interval') {
         limit = interval_max;
      } else if ((classname ==='first_int') || (classname ==='last_int')) {
         limit = int_range_max;
      }
     

      // Increment/decrement
      if (value > limit) {
         $(this).siblings('input.' + classname).val(limit);
      } else if (value < 0) {
         $(this).siblings('input.' + classname).val(0);
      } else {
         if ($(this).hasClass('form_incr') && (value < limit)) {
            $(this).siblings('input.' + classname).val(value + 1);
         } else if ($(this).hasClass('form_decr') && (value > 0)) {
            $(this).siblings('input.' + classname).val(value - 1);
         }
      }

      // TODO Cover first and last interval + IP > first cannot be greater than last
   });

   // Set bitmap if sent
   function set_bitmap(http_request)
   {
      // Change image
      if (http_request.getResponseHeader('Bitmap') === 'ok') {
         $('#bitmap_inner').show();
         $('#bitmap_inner img').remove();
         $('#bitmap_inner').html('<img class="hover_coords origin" src="data:image/png;base64,' + http_request.responseText + '" />');
         $('#bitmap_inner img').css({
            'border': '1px solid SlateGray',
            'display': 'block',
            'margin': 'auto'
         });
         $('#bitmap_inner').css({
            'margin-top': '50px'
         });

         // Change interval characteristics if range < time window
         if (parseInt($('#int_range').html().split(" ")[0]) <
            parseInt($('.bitmap_stats td.time_window').html().split(" ")[0])) {
            int_range_max = http_request.getResponseHeader('Interval_range');
            document.getElementById("int_range").innerHTML = int_range_max + " intervals";
         }
         // Change online -> offline only
         if (($('.bitmap_stats td.mode').html() == 'online') &&
             (http_request.getResponseHeader('Mode') == 'offline')) {
            document.getElementById("mode").innerHTML = http_request.getResponseHeader('Mode');
            // Cancel periodic update
            clearTimeout(timeout_handler);
            
         }
      }
   }

   // Set IP index and cell colour
   function set_ip_index(http_request) {
      curr_index = http_request.getResponseHeader('IP_index');
      curr_colour = http_request.getResponseHeader('Cell_colour');
   }


   // Show parameters for each pair of coordinates - images with class 'hover_coords'
   // Also when dragging, extend rectangle
   // http://jsfiddle.net/pSVXz/12/
   $(document).on('mousemove', 'img.hover_coords', function(event) {

      // Displaying coordinates
      var x = parseInt(event.pageX - $(this).position().left - 1);
      var y = parseInt(event.pageY - $(this).position().top - 51);

      if ((x < 0) || (y < 0)) {
         return;
      }

      // Origin x selected
      var classname = '';
      if ($(this).hasClass('origin')) {
         classname = 'origin';
      } else if ($(this).hasClass('selected_area')) {
         classname = 'selected';
      }

      // Get IP at index
      var first_ip = '';
      var granularity = 0;
      if (classname === 'origin') {
         first_ip = $('.bitmap_stats td.range').html().split(" ")[0];
         granularity = $('.bitmap_stats td.subnet_size').html().slice('1');
      } else {
         first_ip= $('.selected_stats #selected_ip_range').html().split(" ")[0];
         granularity = $('.selected_stats #selected_subnet_size').html().slice('1');
         
      }
      


      var arguments = 'calculate_index=true' +
                      '&bitmap_type=' + classname +
                      '&first_ip=' + first_ip +
                      '&ip_index=' + y +
                      '&granularity=' + granularity +
                      '&interval=' + x;

      http_GET('', set_ip_index, arguments);

      // Update current position
      if (classname === 'origin') {
         document.getElementById(classname + '_curr_IP').innerHTML = curr_index +
                                        $('.bitmap_stats td.subnet_size').html();
         if (x == parseInt($('.bitmap_stats td.int_range').html())) {
            x--;
         }
         document.getElementById(classname + '_curr_interval').innerHTML = x;
      } else {
         // Move coordinates based on selected area
         document.getElementById(classname + '_curr_IP').innerHTML = curr_index +
                                        $('.selected_stats #selected_subnet_size').html();
         if (x == parseInt($('.selected_stats #selected_int_range').html().split(' ')[2])) {
            x--;
         }
         document.getElementById(classname + '_curr_interval').innerHTML = x +
                                       parseInt($('.selected_stats #selected_int_range').html().split(" ")[0]);
      }
      $('th.' + classname + '_curr_colour').css({
         'background': curr_colour,
         'color': ((curr_colour === 'black') ? 'white' : 'black')
      });

      // Dragging
      if (mouse_down) {
         var width = Math.abs(mouse_X - event.pageX);
         var height = Math.abs(mouse_Y - event.pageY + 50);
         $('#rectangle').css({
            'width': width - 1,
            'height': height - 1,
            'left': ((event.pageX < mouse_X) ? (mouse_X - width) : mouse_X),
            'top': ((event.pageY - 50 < mouse_Y) ? (mouse_Y - height) : mouse_Y)
         });
      }
   });

   
   // Drag image function - updates values in submit
   $( '<div id="rectangle" class="hover_coords"></div>' ).appendTo('#main')[0];

   $(document).on('mousedown', 'img.hover_coords.origin', function(event) {
      mouse_down = true;
      event.preventDefault();
      mouse_X = event.pageX;
      mouse_Y = event.pageY - 50;
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
      down_ip = curr_index;
      down_int = parseInt($('#origin_curr_interval').html());
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
            for (var i = 0; i < len; i++) {
               if (tmp[i] != '') {
                  tmp[i] = ('0000' + tmp[i]).substr(-4);
               } else {
                  tmp[i] = '0000';
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

   // When mouse is up, detach rectangle
   $(document).on('mouseup', 'html', function() {

      if (mouse_down) {
         // Insert rectangle values to Options
         var ip1 = down_ip;
         var ip2 = curr_index;         

         // Is ip1 < ip2 ?
         if (compare_ips(ip1, ip2)) {
            $('.bitmap_options input.first_ip').val(ip1);
            $('.bitmap_options input.last_ip').val(ip2);
         } else {
            $('.bitmap_options input.first_ip').val(ip2);
            $('.bitmap_options input.last_ip').val(ip1);
         }
   
         var int1 = down_int;
         var int2 = parseInt($('#origin_curr_interval').html());
         if (int1 <= int2) {
            $('.bitmap_options input.first_int').val(int1);
            $('.bitmap_options input.last_int').val(int2);
         } else {
             $('.bitmap_options input.first_int').val(int2);
            $('.bitmap_options input.last_int').val(int1);
         }

         mouse_down = false;
         $('#rectangle').hide();
         mouse_X = -1;
         mouse_Y = -1;
      }
   });

});

