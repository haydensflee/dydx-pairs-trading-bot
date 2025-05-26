'''
func_utils.py
This file contains all the utility functions that are used in the program.
'''
from datetime import datetime, timedelta
import time
from datetime import datetime, timedelta

# Format number
def format_number(curr_num, match_num):

  """
    Give current number an example of number with decimals desired
    Function will return the correctly formatted string
  """

  curr_num_string = f"{curr_num}"
  match_num_string = f"{match_num}"

  if "." in match_num_string:
    match_decimals = len(match_num_string.split(".")[1])
    curr_num_string = f"{curr_num:.{match_decimals}f}"
    curr_num_string = curr_num_string[:]
    return curr_num_string
  else:
    return f"{int(curr_num)}"
  

# ----- GET ISO TIME FUNCTIONS ----- #

# Format time
def format_time(timestamp):
  return timestamp.replace(microsecond=0).isoformat()

# Get ISO time
def get_ISO_times():

  """
    Get the ISO times for the start and end of the window
  """
  date_start_0 = datetime.now()
  date_start_1 = date_start_0 - timedelta(hours=100)
  date_start_2 = date_start_1 - timedelta(hours=100)
  date_start_3 = date_start_2 - timedelta(hours=100)
  date_start_4 = date_start_3 - timedelta(hours=100)

  # Format datetimes (Approximately 16 days of hourly data)
  times_dict = {
    "range_1": {
      "from_iso": format_time(date_start_1),
      "to_iso": format_time(date_start_0),
    },
    "range_2": {
      "from_iso": format_time(date_start_2),
      "to_iso": format_time(date_start_1),
    },
    "range_3": {
      "from_iso": format_time(date_start_3),
      "to_iso": format_time(date_start_2),
    },
    "range_4": {
      "from_iso": format_time(date_start_4),
      "to_iso": format_time(date_start_3),
    },
  }

  # Return result
  return times_dict


def wait_until_half_hour():
  now = datetime.now()
  # Round up to the next 00 or 30 minute mark
  if now.minute < 30:
      next_run = now.replace(minute=30, second=0, microsecond=0)
  else:
      next_run = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)

  seconds_to_sleep = (next_run - now).total_seconds()
  # seconds_to_sleep = 30
  print(f"Sleeping for {int(seconds_to_sleep)} seconds until {next_run.strftime('%H:%M:%S')}")
  time.sleep(seconds_to_sleep)
