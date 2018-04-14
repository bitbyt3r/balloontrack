#!/usr/bin/python
from datetime import datetime, timezone, timedelta
import requests
import aprslib
import dbus
import time

stations = [
  "W3EAX-12",
  "W3EAX-13",
]

url = "http://predict.cusf.co.uk/api/v1/"
ascent_rate = 5
burst_altitude = 25500
descent_rate = 6

burst = False
current_rate = 0
last_altitude = 0
start_time = time.time()
session_bus = dbus.SessionBus()
navit = session_bus.get_object('org.navit_project.navit', '/org/navit_project/navit/default_navit')

def set_dest(lat, long):
  print("Navigating to {}, {}".format(lat, long))
  navit.set_destination("geo: {} {}".format(long, lat), "Balloon")

def run_predict(start_lat, start_lon, start_alt, current_rate, burst):
  try:
    date = datetime.now(timezone.utc)
    date = date + timedelta(hours=12)
    date = str(date.astimezone().isoformat())
    data = {
      "ascent_rate": ascent_rate,
      "burst_altitude": burst_altitude,
      "descent_rate": descent_rate,
      "launch_altitude": start_alt,
      "launch_datetime": date,
      "launch_latitude": float(start_lat),
      "launch_longitude": float(start_lon)+360,
      "profile": "standard_profile",
      "version": 1
    }
    r = requests.get(url, data)
    dest = r.json()['prediction'][-1]['trajectory'][-1]
    print(dest)
    return {"latitude": dest['latitude'], "longitude": dest['longitude']-360}
  except:
    return None

def packet(x):
  global last_altitude
  global start_time
  global current_rate
  global burst
  if x['from'] in stations:
    print("{}: {}, {} @ {}".format(x['from'], x['latitude'], x['longitude'], x['altitude']))
    if x['altitude'] > burst_altitude:
      burst = True
    new_ascent = (x['altitude'] - last_altitude) / (time.time() - start_time)
    start_time = time.time()
    last_altitude = x['altitude']
    #current_rate = current_rate * 0.8 + new_ascent * 0.2
    current_rate = new_ascent
    print("Current rate: {}".format(current_rate))
    dest = run_predict(x['latitude'], x['longitude'], x['altitude'], current_rate, burst)
    if dest:
      set_dest(dest['latitude'], dest['longitude'])

AIS = aprslib.IS("KC3HOB")
AIS.connect()
AIS.consumer(packet)

