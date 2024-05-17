#!/usr/bin/env /bin/python3
#
# PWMreminder
# Script to send discord messages to remind guild events in PWM
#
__author__ = "GhostTalker"
__copyright__ = "Copyright 2023, The GhostTalker project"
__version__ = "0.0.1"
__status__ = "TEST"

import os
import sys
import json
from datetime import datetime, timedelta
import pytz
import requests
from mysql.connector import pooling, Error
import configparser
import schedule
import time
import signal

## read config
_config = configparser.ConfigParser()
_rootdir = os.path.dirname(os.path.abspath('config.ini'))
_config.read(_rootdir + "/config.ini")
_mysqlhost = _config.get("mysql", "mysqlhost", fallback='127.0.0.1')
_mysqlport = _config.get("mysql", "mysqlport", fallback='3306')
_mysqldb = _config.get("mysql", "mysqldb")
_mysqluser = _config.get("mysql", "mysqluser")
_mysqlpass = _config.get("mysql", "mysqlpass")
_remind_time_before_start = int(_config.get("general", "remind_time_before_start"))
_timezone = _config.get("general", "timezone", fallback='UTC')


# Helper function to get the next occurrence of a weekday
def get_next_weekday(start_date, weekday):
    days_ahead = weekday - start_date.weekday()
    if days_ahead < 0:
        days_ahead += 7
    return start_date + timedelta(days=days_ahead)


# Helper function to convert event_day to the correct weekday name
def get_weekday_name(event_day):
    weekday_map = {
        1: "Monday",
        2: "Tuesday",
        3: "Wednesday",
        4: "Thursday",
        5: "Friday",
        6: "Saturday",
        7: "Sunday"
    }
    return weekday_map.get(event_day, "Invalid day")


# Function to perform the reminder task
def send_reminders():
    try:
        connection_pool = pooling.MySQLConnectionPool(pool_name="mysql_connection_pool",
                                                      pool_size=5,
                                                      pool_reset_session=True,
                                                      host=_mysqlhost,
                                                      port=_mysqlport,
                                                      database=_mysqldb,
                                                      user=_mysqluser,
                                                      password=_mysqlpass)

        print("Create connection pool: ")
        print("Connection Pool Name - ", connection_pool.pool_name)
        print("Connection Pool Size - ", connection_pool.pool_size)

        # Get connection object from a pool
        connection_object = connection_pool.get_connection()

        if connection_object.is_connected():
            db_Info = connection_object.get_server_info()
            print("Connected to MySQL database using connection pool ... MySQL Server version on ", db_Info)

            cursor = connection_object.cursor(dictionary=True)

            # Fetch Discord webhook information
            cursor.execute("SELECT * FROM discord")
            discord_webhooks = cursor.fetchall()
            discord_webhooks_dict = {webhook["discord_guild_name"]: webhook for webhook in discord_webhooks}

            # Calculate the reminder time threshold
            tz = pytz.timezone(_timezone)
            current_time = datetime.now(tz)
            remind_time_threshold = current_time + timedelta(minutes=_remind_time_before_start)

            #print("Current time:", current_time)
            #print("Reminder time threshold:", remind_time_threshold)

            # Query to fetch events happening within the reminder time threshold
            cursor.execute("""
                SELECT * FROM events
            """)

            events = cursor.fetchall()
            events_dict = {event["event_id"]: event for event in events}

            # Filter events based on the reminder time threshold
            upcoming_events = []
            for event in events:
                # Assume event_day is the day of the week (1=Monday, ..., 7=Sunday)
                event_day = int(event['event_day']) - 1  # Adjust for Python's weekday (0 = Monday, ..., 6 = Sunday)
                event_time = event['event_time']
                next_event_date = get_next_weekday(current_time, event_day)
                event_datetime_str = f"{next_event_date.strftime('%Y-%m-%d')} {event_time}:00"
                event_datetime = tz.localize(datetime.strptime(event_datetime_str, '%Y-%m-%d %H:%M:%S'))
                if current_time <= event_datetime <= remind_time_threshold:
                    upcoming_events.append(event)

            if upcoming_events:
                print(f"Found {len(upcoming_events)} upcoming event(s):")
                for event in upcoming_events:
                    print(
                        f"Event ID: {event['event_id']}, Name: {event['event_name']}, Day: {get_weekday_name(int(event['event_day']))}, Time: {event['event_time']}, Description: {event['event_description']}")
                    event_id = event["event_id"]
                    event_name = event["event_name"]
                    event_day_num = int(event["event_day"])
                    event_time = event["event_time"]
                    event_description = event["event_description"]

                    for guild_name, webhook_info in discord_webhooks_dict.items():
                        webhook_url = webhook_info["discord_webhook_id"]
                        role_id = webhook_info.get("discord_role_id")

                        # Create the embed message
                        embed = {
                            "title": f"Reminder for Event: {event_name}",
                            "description": event_description,
                            "color": 5814783,  # Blue color
                            "fields": [
                                {
                                    "name": "Day",
                                    "value": get_weekday_name(event_day_num),
                                    "inline": True
                                },
                                {
                                    "name": "Time",
                                    "value": f"{event_time}",
                                    "inline": True
                                }
                            ],
                            "footer": {
                                "text": "Don't miss it!"
                            },
                            "timestamp": event_datetime.isoformat()
                        }

                        message = {
                            "content": f"@everyone",
                            "embeds": [embed]
                        }

                        if role_id:
                            message["content"] = f"<@&{role_id}> " + message["content"]

                        # Send the message to the Discord webhook
                        response = requests.post(webhook_url, json=message)

                        if response.status_code == 204:
                            print(f"Successfully sent reminder for event '{event_name}' to guild '{guild_name}'")
                        else:
                            print(
                                f"Failed to send reminder for event '{event_name}' to guild '{guild_name}': {response.text}")
            else:
                print("No upcoming events to remind.")

    except Error as e:
        print("Error while connecting to MySQL using Connection pool ", e)

    finally:
        # closing database connection.
        if connection_object.is_connected():
            cursor.close()
            connection_object.close()
            print("MySQL connection is closed")


# Schedule the task to run every 30 minutes between 16:00 and 22:00
def schedule_tasks():
    schedule.every().day.at("16:00").do(send_reminders)
    schedule.every().day.at("16:30").do(send_reminders)
    schedule.every().day.at("17:00").do(send_reminders)
    schedule.every().day.at("17:30").do(send_reminders)
    schedule.every().day.at("18:00").do(send_reminders)
    schedule.every().day.at("18:30").do(send_reminders)
    schedule.every().day.at("19:00").do(send_reminders)
    schedule.every().day.at("19:30").do(send_reminders)
    schedule.every().day.at("20:00").do(send_reminders)
    schedule.every().day.at("20:30").do(send_reminders)
    schedule.every().day.at("21:00").do(send_reminders)
    schedule.every().day.at("21:30").do(send_reminders)
    schedule.every().day.at("22:00").do(send_reminders)


def exit_gracefully(signum, frame):
    print("Exiting gracefully...")
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, exit_gracefully)
    signal.signal(signal.SIGTERM, exit_gracefully)
    # execute for testing
    send_reminders
    schedule_tasks()
    while True:
        schedule.run_pending()
        time.sleep(1)
