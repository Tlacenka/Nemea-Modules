/*
 * Subject: IP Activity Analysis
 * Brief: JS for web client visualising data to user.
 * Author: Katerina Pilatova
 * Date: 2016
 */

// Universal function for all asynchronous GET requests
function http_GET(url, arguments, content_type, callback)
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
         callback(http_request);
      }
   }
   xhttp.setRequestHeader("Content-type", content_type);

   // Send request
   http.send();
}

// Show parameters for each pair of coordinates - images with class 'hover_coords'
// http://jsfiddle.net/pSVXz/12/
var display_coords = $('<div id="display_coords"></div>').appendTo('body')[0];
$('.hover_coords').each(coords_handler());

function coords_handler()
{
   // Get image stats 
   var position = $(this).position();
   var width = $(this).width();
   var height = $(this).height();

   var top = position.top;
   var left = position.left;

   // Calculate offset, display coordinates
   $(this).mousemove(function(event) {
      var x = event.clientX - left;
      var y = event.clientY - top;

      // AJAX GET request for offset values

      $('#display_coords').text(x + ', ' + y).css({
         left: event.clientX - 20;
         top: event.clientY - 20;
      }).show();
   })

   // When mouse is out of image boundaries, hide text
   $(this)mouseleave(function() {
      $('#display_coords'.hide());
   })
}

// Get bitmap based on entered arguments
function get_bitmap()
{
   http_GET(url, arguments, set_bitmap);
}

// Set bitmap
function set_bitmap(http_request)
{
   http_request.responseText;
}
