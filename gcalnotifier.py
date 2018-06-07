from __future__ import print_function

import colorsys
import datetime
import math
import os
import sys
import time

import numpy as np
import pytz
from dateutil import parser
from apiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools

SCOPES = 'https://www.googleapis.com/auth/calendar.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Pi Reminder'
CALENDAR_ID = 'primary'
HASH = '#'
HASHES = '########################################'

# ten.wav - 10 minutes until appointment
# five.wav - 5 minutes until appointment
# two.wav - 2 minutes until appointment

# Reminder thresholds
FIRST_THRESHOLD = 5  # minutes,

SECOND_THRESHOLD = 2  # minutes,

def get_credentials():
    global service
    # taken from https://developers.google.com/google-apps/calendar/quickstart/python
    SCOPES = 'https://www.googleapis.com/auth/calendar.readonly'
    store = file.Storage('credentials.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('client_secret.json', SCOPES)
        creds = tools.run_flow(flow, store)
    service = build('calendar', 'v3', http=creds.authorize(Http()))

def has_reminder(event):
    # Return true if there's a reminder set for the event
    # First, check to see if there is a default reminder set
    has_default_reminder = event['reminders'].get('useDefault')
    if has_default_reminder:
        # if yes, then we're good
        return True
    else:
        # are there overrides set for reminders?
        overrides = event['reminders'].get('overrides')
        if overrides:
            # OK, then we have a reminder to use
            return True
    # if we got this far, then there must not be a reminder set
    return False

def get_next_event(search_limit):
    global service
    # modified from https://developers.google.com/google-apps/calendar/quickstart/python
    # get all of the events on the calendar from now through 10 minutes from now
    print(datetime.datetime.now(), 'Getting next event')

    now = datetime.datetime.utcnow()
    then = now + datetime.timedelta(minutes=search_limit)
    # ask Google for the calendar entries
    events_result = service.events().list(
        # get all of them between now and 10 minutes from now
        calendarId=CALENDAR_ID,
        timeMin=now.isoformat() + 'Z',
        timeMax=then.isoformat() + 'Z',
        singleEvents=True,
        orderBy='startTime').execute()
    print('Data succesfully returned from Google calendar API\n')
    event_list = events_result.get('items', [])

    if not event_list:
        # no? Then no upcoming events at all, so nothing to do right now
        print(datetime.datetime.now(), 'No entries returned')
        return None
    else:
        # what time is it now?
        current_time = pytz.utc.localize(datetime.datetime.utcnow())
    	# loop through the events in the list
        for event in event_list:
            # we only care about events that have a start time
            start = event['start'].get('dateTime')
            # return the first event that has a start time
            # so, first, do we have a start time for this event?
            if start:
                # When does the appointment start?
                # Convert the string it into a Python dateTime object so we can do math on it
                event_start = parser.parse(start)
                # does the event start in the future?
                if current_time < event_start:
                    # only use events that have a reminder set
                    if has_reminder(event):
                        # no? So we can use it
                        event_summary = event['summary'] if 'summary' in event else 'No Title'
                        print('Found event:', event_summary)
                        print('Event starts:', start)
                        # figure out how soon it starts
                        time_delta = event_start - current_time
                        # Round to the nearest minute and return with the object
                        event['num_minutes'] = time_delta.total_seconds() // 60
                        return event
    # if we got this far and haven't returned anything, then there's no appointments in the specified time
    # range, or we had an error, so...
    return None

def main():
    # initialize the lastMinute variable to the current time to start
    last_minute = datetime.datetime.now().minute
    # on startup, just use the previous minute as lastMinute
    if last_minute == 0:
        last_minute = 59
    else:
        last_minute -= 1

    # infinite loop to continuously check Google Calendar for future entries
    while 1:
        # get the current minute
        current_minute = datetime.datetime.now().minute
        # is it the same minute as the last time we checked?
        if current_minute != last_minute:
            # reset last_minute to the current_minute, of course
            last_minute = current_minute
            # we've moved a minute, so we have work to do
            # get the next calendar event (within the specified time limit [in minutes])
            next_event = get_next_event(10)
            # do we get an event?
            if next_event is not None:
                num_minutes = next_event['num_minutes']
                if num_minutes != 1:
                    print('Starts in', int(num_minutes), 'minutes\n')
                else:
                    print('Starts in 1.0 minute\n')
                # is the appointment between 10 and 5 minutes from now?
                if num_minutes >= FIRST_THRESHOLD:
                    # play ten.wav sound 3 times within 30 seconds to remind that there are less than 10 minutes left
                    os.system('aplay ten.wav')
                    time.sleep(10)
                    os.system('aplay ten.wav')
                    time.sleep(10)
                    os.system('aplay ten.wav')
                # is the appointment less than 5 minutes but more than 2 minutes from now?
                elif num_minutes > SECOND_THRESHOLD:
               	    # play five.wav sound 3 times within 30 seconds to remind that there are less than 5 minutes left
                    os.system('aplay five.wav')
                    time.sleep(10)
                    os.system('aplay five.wav')
                    time.sleep(10)
                    os.system('aplay five.wav')
                # hmmm, less than 2 minutes, almost time to start!
                else:
                    # play two.wav sound 2 times within 30 seconds to remind that there are less than 2 minutes left
                    os.system('aplay two.wav')
                    time.sleep(10)
                    os.system('aplay two.wav')
        # wait a second then check again
        time.sleep(1)


# now tell the user what we're doing...
print('\n')
print(HASHES)
print(HASH, 'Pi Remind                           ', HASH)
print(HASHES)

get_credentials()

print('\nApplication initialized\n')

# Now see what we're supposed to do next
if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nExiting application\n')
        sys.exit(0)
