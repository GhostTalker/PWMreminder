# PWMreminder

PWMreminder is a Python script that regularly reads events from a MySQL database and sends messages to a Discord guild using a webhook to remind members of upcoming events.

## Installation

1. **Clone the repository:**

    ```bash
    git clone https://github.com/your-username/PWMreminder.git
    cd PWMreminder
    ```

2. **Create and activate a virtual environment:**

    ```bash
    python3 -m venv venv
    source venv/bin/activate 
    ```

3. **Install the dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

## Configuration

Create a `config.ini` file in the project directory with the following content:

```ini
[general]
remind_time_before_start = 30
timezone = Europe/Zurich

[mysql]
mysqlhost = localhost
mysqlport = 3306
mysqldb = statsdatabase
mysqluser = dbuser
mysqlpass = dbpassword
```
- remind_time_before_start: Time in minutes before the event to send the reminder.
- timezone: Timezone, e.g., Europe/Zurich.
- mysqlhost: Hostname of the MySQL server.
- mysqlport: Port of the MySQL server.
- mysqldb: Name of the MySQL database.
- mysqluser: MySQL username.
- mysqlpass: MySQL password.

## Database Structure

### Table `discord`

| Column               | Type          | Description                                  |
|----------------------|---------------|----------------------------------------------|
| `discord_guild_name` | varchar(255)  | Name of the Discord guild (Primary Key)      |
| `discord_guild_id`   | bigint(100)   | ID of the Discord guild                      |
| `discord_channel_id` | bigint(100)   | ID of the Discord channel                    |
| `discord_webhook_id` | varchar(255)  | URL of the Discord webhook                   |
| `discord_role_id`    | bigint(100)   | ID of the Discord role (optional)            |

### Table `events`

| Column              | Type          | Description                                  |
|---------------------|---------------|----------------------------------------------|
| `event_id`          | int(11)       | ID of the event (Primary Key)                |
| `event_name`        | varchar(45)   | Name of the event                            |
| `event_day`         | varchar(45)   | Day of the event (1=Monday, ..., 7=Sunday)   |
| `event_time`        | varchar(45)   | Time of the event (HH:MM)                    |
| `event_description` | varchar(255)  | Description of the event                     |

## Usage
Run the script:

```
python PWMreminder.py
```
The script will read the events from the database and send reminders to Discord based on the configured schedule.

## Schedule
The script is configured to run every 30 minutes between 16:00 and 22:00. The schedule can be adjusted in the script by modifying the schedule_tasks function.

## Sample Output
Upon successful execution, the script will output information about found events and their reminder status:

```bash
Create connection pool:
Connection Pool Name -  mysql_connection_pool
Connection Pool Size -  5
Connected to MySQL database using connection pool ... MySQL Server version on  5.5.5-10.6.16-MariaDB-0ubuntu0.22.04.1
Current time: 2024-05-17 22:52:33.585056
Reminder time threshold: 2024-05-17 23:22:33.585056
Found 1 upcoming event(s):
Event ID: 1, Name: Test Event, Day: Friday, Time: 19:30, Description: Test Description
Successfully sent reminder for event 'Test Event' to guild 'PWM Elysium'
```

## Stopping the Script
The script can be gracefully stopped by pressing Ctrl+C or sending a SIGTERM signal.

## License
This project is licensed under the MIT License. See the LICENSE file for details.

