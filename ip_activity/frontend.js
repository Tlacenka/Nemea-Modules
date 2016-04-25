/*
 * Subject: IP Activity Analysis
 * Brief: JS for web client visualising data to user.
 * Author: Katerina Pilatova
 * Date: 2016
 */

// Main function
$(document).ready(function() {

   // Start updating - immediately or after timeout?
   var timeout_handler = auto_update();

   // IP index for later use
   var index = "";

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
      var interval = parseInt($('td.time_interval').html().split(" ")[0])*1000;
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

   // Set IP index
   function set_ip_index(http_request) {
      index = http_request.getResponseHeader("IP_index");
   }


   // Show parameters for each pair of coordinates - images with class 'hover_coords'
   // http://jsfiddle.net/pSVXz/12/

   $(document).on('mousemove', 'img.hover_coords', function(event) {
      var x = parseInt(event.pageX - $(this).position().left);
      var y = parseInt(event.pageY - $(this).position().top - 50);

      var arguments = "calculate_index=true&first_ip=" +
                      $('td.range').html().split(" ")[0] + "&index=" +
                      y + "&granularity=" + 
                      $('td.subnet_size').html().slice("1");

      // AJAX GET request for IP index
      http_GET("", set_ip_index, arguments);

      $('#display_coords').html(x + ', ' + index).css({
         "position" : "absolute",
         "left": event.pageX + 20,
         "top": event.pageY - 90
      }).show();
   });

   // When mouse is out of image boundaries, hide text
   $(document).on('mouseleave', 'img.hover_coords', function() {
      $('#display_coords').hide();
   });

   

});

