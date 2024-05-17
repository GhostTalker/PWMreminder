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
import requests
from mysql.connector import pooling, Error
import configparser

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

## create connection pool and connect to MySQL
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
        current_time = datetime.now()
        remind_time_threshold = current_time + timedelta(minutes=_remind_time_before_start)

        print("Current time:", current_time)
        print("Reminder time threshold:", remind_time_threshold)

        # Query to fetch events happening within the reminder time threshold
        cursor.execute("""
            SELECT * FROM events
        """)

        events = cursor.fetchall()
        events_dict = {event["event_id"]: event for event in events}

        # Filter events based on the reminder time threshold
        upcoming_events = []
        for event in events:
            event_datetime = datetime.strptime(f"{event['event_day']} {event['event_time']}", '%Y-%m-%d %H:%M:%S')
            if current_time <= event_datetime <= remind_time_threshold:
                upcoming_events.append(event)

        if upcoming_events:
            for event in upcoming_events:
                event_id = event["event_id"]
                event_name = event["event_name"]
                event_day = event["event_day"]
                event_time = event["event_time"]
                event_description = event["event_description"]

                for guild_name, webhook_info in discord_webhooks_dict.items():
                    webhook_id = webhook_info["discord_webhook_id"]
                    role_id = webhook_info.get("discord_role_id")

                    # Create the message
                    message = {
                        "content": f"@everyone Reminder for event: **{event_name}**\nDescription: {event_description}\nTime: {event_day} {event_time}",
                    }

                    if role_id:
                        message["content"] = f"<@&{role_id}> " + message["content"]

                    # Send the message to the Discord webhook
                    webhook_url = f"https://discord.com/api/webhooks/{webhook_id}"
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
