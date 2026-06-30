/**
 * Google Apps Script Web App Bridge to create events in Google Calendar.
 * 
 * Deployment Instructions:
 * 1. Open https://script.new
 * 2. Delete any default code and paste this code.
 * 3. Click "Deploy" (Развернуть) -> "New deployment" (Новое развертывание).
 * 4. Choose "Web app" (Веб-приложение) as the type.
 * 5. Set:
 *    - Description: Hermes Calendar Bridge
 *    - Execute as: Me (your-email@gmail.com)
 *    - Who has access: Anyone (Все)
 * 6. Click "Deploy". Authorize permissions when prompted (you might need to click "Advanced" -> "Go to Untitled project (unsafe)").
 * 7. Copy the Web app URL (e.g., https://script.google.com/macros/s/..../exec).
 * 8. Add it to your .env file as: GOOGLE_CALENDAR_WEBHOOK_URL=https://script.google.com/macros/s/..../exec
 */

function doPost(e) {
  var responseHeaders = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type'
  };
  
  try {
    if (!e || !e.postData || !e.postData.contents) {
      return createJsonResponse({
        status: 'error',
        message: 'No POST data received'
      }, 400, responseHeaders);
    }
    
    var data = JSON.parse(e.postData.contents);
    var title = data.title;
    var startStr = data.start; // ISO-8601 string
    var endStr = data.end;     // ISO-8601 string or undefined
    var description = data.description || '';
    
    if (!title || !startStr) {
      return createJsonResponse({
        status: 'error',
        message: 'Missing title or start parameters'
      }, 400, responseHeaders);
    }
    
    var startTime = new Date(startStr);
    var endTime = endStr ? new Date(endStr) : new Date(startTime.getTime() + 60 * 60 * 1000); // 1 hour default
    
    var calendar = CalendarApp.getDefaultCalendar();
    var event;
    
    if (data.all_day) {
      event = calendar.createAllDayEvent(title, startTime, {
        description: description
      });
    } else {
      event = calendar.createEvent(title, startTime, endTime, {
        description: description
      });
    }
    
    return createJsonResponse({
      status: 'success',
      event_id: event.getId(),
      title: title,
      start: startTime.toISOString(),
      end: endTime.toISOString(),
      calendar_name: calendar.getName()
    }, 200, responseHeaders);
    
  } catch (error) {
    return createJsonResponse({
      status: 'error',
      message: error.toString()
    }, 500, responseHeaders);
  }
}

// Handle OPTIONS requests (CORS preflight)
function doOptions(e) {
  var responseHeaders = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Max-Age': '86400'
  };
  return ContentService.createTextOutput('')
    .setMimeType(ContentService.MimeType.TEXT)
    .setHeaders(responseHeaders);
}

function createJsonResponse(data, statusCode, headers) {
  var response = ContentService.createTextOutput(JSON.stringify(data))
    .setMimeType(ContentService.MimeType.JSON);
  if (headers) {
    response.setHeaders(headers);
  }
  return response;
}
