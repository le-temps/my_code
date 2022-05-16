import datetime

FORMART = {
    "time": "%Y-%m-%d %H:%M:%S",
    "date": "%Y-%m-%d"
}

def get_current_time_string(type):
    timestamp = datetime.datetime.now().timestamp()
    return datetime.datetime.fromtimestamp(timestamp).strftime(FORMART[type])

def timestamp_to_time_string(timestamp, type):
    return datetime.datetime.fromtimestamp(timestamp).strftime(FORMART[type])

def time_string_to_timestamp(time_string, type):
    return datetime.datetime.strptime(time_string, FORMART[type]).timestamp()

def compare_time_string(time_string1, time_string2, type):
    if time_string_to_timestamp(time_string1, type) > time_string_to_timestamp(time_string2, type):
        return True
    else:
        return False