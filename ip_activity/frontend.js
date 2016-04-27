/*
 * Subject: IP Activity Analysis
 * Brief: JS for web client visualising data to user.
 * Author: Katerina Pilatova
 * Date: 2016
 */

// Main function
$(document).ready(function() {

   // Start updating bitmap
   var timeout_handler = auto_update();

   // IP index and colour initialisation
   var curr_index = $('.bitmap_stats td.range').html().split(" ")[0];
   var curr_colour = "black";
   document.getElementById("curr_IP").innerHTML = curr_index;
   document.getElementById("curr_interval").innerHTML = 0;
   $('th.curr_colour').css({
      'background': 'black',
      'color': 'white'
   });

   // Initialise limits for input
   var ip_version = 4;
   if ($('.bitmap_stats td.range').html().split(" ")[0].indexOf(":") != -1) {
      ip_version = 6;
   }
   var ip_max = ((ip_version == 4) ? 32 : 128);
   var interval_max = 86400; // a day
   var window_max = 1000;

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
   $('.bitmap_options input.time_window').val(parseInt($('.bitmap_stats td.time_window').html().split(" ")[0]));
   $('.bitmap_options input.first_int').val(0);
   $('.bitmap_options input.last_int').val(parseInt($('.bitmap_stats td.time_window').html().split(" ")[0]));


   // When changing bitmap type, get new bitmap, update CSS
   $("#bitmap_type li").click(function() {

      if (!($(this).hasClass('chosen_type'))) {

         // Switch class to current type
         $('#bitmap_type li.chosen_type').removeClass();
         $(this).addClass('chosen_type');

         // Update bitmap immediately
         clearTimeout(timeout_handler);
         auto_update();
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
      if (typeof(arguments)==='undefined') {
         arguments = "";
      }

      var value = $('#bitmap_type li.chosen_type').html();

      var suffix = "";
      if (value === "Source IPs") {
         suffix = "_s.png";
      } else if (value === "Destination IPs") {
         suffix = "_d.png";
      } else if (value === "Both Directions") {
         suffix = "_sd.png";
      }

      // Filename to be added
      var image = "image" + suffix;
      http_GET(image, set_bitmap, 'update=true');

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
         content_type = "application/x-www-form-urlencoded";
      }

      // Create request
      var http_request = new XMLHttpRequest();
      http_request.open("GET", url, true);
      http_request.onreadystatechange = function() {
         if ((http_request.readyState == 4) && (http_request.status == 200)) {
            //alert("200")
            callback(http_request);
         } else if ((http_request.readyState == 4) && (http_request.status == 404)) {
            alert("404");
         }
      }

      // Send request
      http_request.send();

   }


   // Handle form submit TODO
   $('.submit').click(function(event) {
      event.preventDefault();
      alert($('#bitmap_form input.granularity').val());

   });

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
      } else if ((classname === 'time_window') || (classname ==='first_int') ||
                 (classname ==='last_int')) {
         limit = window_max;
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

      // Cover first and last interval + IP > first cannot be greater than last

   });

   // Set bitmap
   function set_bitmap(http_request)
   {
      // Change image
      $('#bitmap_inner img').remove();
      $('#bitmap_inner').html('<img class="hover_coords" src="data:image/png;base64,' + http_request.responseText + '" />');
      $('#bitmap_inner').css({
         "height":  $('#bitmap_inner img').height() + 1,
         "width":  $('#bitmap_inner img').width() + 1
      });
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
      var x = parseInt(event.pageX - $(this).position().left);
      var y = parseInt(event.pageY - $(this).position().top - 50);

      var arguments = 'calculate_index=true&first_ip=' +
                      $('td.range').html().split(" ")[0] + '&ip=' +
                      y + '&granularity=' + 
                      $('td.subnet_size').html().slice('1') + '&interval=' +
                      x;

      http_GET("", set_ip_index, arguments);

      document.getElementById("curr_IP").innerHTML = curr_index;
      document.getElementById("curr_interval").innerHTML = x;
      $('th.curr_colour').css({
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

   $(document).on('mousedown', 'img.hover_coords', function(event) {
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
   });

   // When mouse is up, detach rectangle
   $(document).on('mouseup', 'body', function() {
      mouse_down = false;
      $('#rectangle').hide();
      mouse_X = -1;
      mouse_Y = -1;
   });

});

