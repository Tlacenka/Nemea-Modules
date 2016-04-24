/*
 * Subject: IP Activity Analysis
 * Brief: JS for web client visualising data to user.
 * Author: Katerina Pilatova
 * Date: 2016
 */

// Main function
$(document).ready(function() {

   // When changing bitmap type, get new bitmap, update CSS
   $("#bitmap_type li").click(function() {

      if (!($(this).hasClass('chosen_type'))) {

         // Switch class to current type
         $('#bitmap_type li.chosen_type').removeClass();
         $(this).addClass('chosen_type');

         // Update bitmap
         var value = $(this).html();
         var suffix = "";
         if (value === "Source IPs") {
            suffix = "_s.png";
         } else if (value === "Destination IPs") {
            suffix = "_d.png";
         } else {
            suffix = "_sd.png";
         }

         // Filename to be added
         var image = "image" + suffix;
         http_GET(image, set_bitmap);

      }

   });


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
      //alert("setting bitmap");
      var response = http_request.responseText;
   }


   // Show parameters for each pair of coordinates - images with class 'hover_coords'
   // http://jsfiddle.net/pSVXz/12/
   var display_coords = $('<div id="display_coords"></div>').appendTo('body')[0];

   $('img.hover_coords').each(function()
   {

      // Get image stats 
      var position = $(this).position();
      var width = $(this).width();
      var height = $(this).height();
   
      var top = position.top;
      var left = position.left;
   /*
      // Calculate offset, display coordinates
      $(this).mousemove(function(event) {
         var x = event.clientX - left;
         var y = event.clientY - top;
   
         // AJAX GET request for offset values
   
         $('#display_coords').text(x + ', ' + y).css({
            left: event.clientX - 20;
            top: event.clientY - 20;
         }).show();
      });
   */
      // When mouse is out of image boundaries, hide text
      $(this).mouseleave(function() {
         $('#display_coords'.hide());
      });

   
   });

});

