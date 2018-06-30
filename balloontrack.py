#!/usr/bin/python
from datetime import datetime, timezone, timedelta
import requests
import aprslib
import dbus
import time

control = [
  "KC3HOB-6",
]

msgNo = {
  "KC3HOB-6": 31,
}

stations = [
  "W3EAX-8",
  "W3EAX-10",
]

url = "http://predict.cusf.co.uk/api/v1/"
ascent_rate = 5
burst_altitude = 29000
descent_rate = 9

burst = False
current_rate = 0
last_altitude = 0
start_time = 0
session_bus = dbus.SessionBus()
navit = session_bus.get_object('org.navit_project.navit', '/org/navit_project/navit/default_navit')

def set_dest(lat, long):
  print("Navigating to {}, {}".format(lat, long))
  navit.set_destination("geo: {} {}".format(long, lat), "Balloon")

def run_predict(start_lat, start_lon, start_alt, current_rate, burst):
  try:
    date = "2018-06-30T{}Z".format(datetime.utcnow().strftime("%H:%M:%S.%f"))
    if burst:
      data = {
        "ascent_rate": ascent_rate,
        "burst_altitude": start_alt,
        "descent_rate": descent_rate,
        "launch_altitude": start_alt,
        "launch_datetime": date,
        "launch_latitude": float(start_lat),
        "launch_longitude": float(start_lon)+360,
        "profile": "standard_profile",
        "version": 1
      }
    else:
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
    print(data)
    print("Retrieving predict...")
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
    print(x)
    print("{}: {}, {} @ {}".format(x['from'], x['latitude'], x['longitude'], x['altitude']*3.2808399))
    new_ascent = (x['altitude'] - last_altitude) / (time.time() - start_time)
    start_time = time.time()
    last_altitude = x['altitude']
    current_rate = new_ascent
    print("Current rate: {}".format(current_rate))
    dest = run_predict(x['latitude'], x['longitude'], x['altitude'], current_rate, burst)
    if dest:
      set_dest(dest['latitude'], dest['longitude'])
  if 'addresse' in x.keys():
    if x['addresse'] in control:
      if x['msgNo'] <= msgNo[x['addresse']]:
        return
      else:
        msgNo[x['addresse']] = x['msgNo']
      print("control[{}]:".format(x['msgNo']), x['message_text'])
      if x['message_text'] == "burst":
        burst = True
        print("Now assuming the balloon has burst.")
      elif x['message_text'] == "!burst":
        burst = False
        print("Now assuming the balloon is intact.")
      elif x['message_text'].startswith("asc"):
        global ascent_rate
        ascent_rate = float(x['message_text'].split(":")[1])
        print("Setting ascent rate to {}".format(ascent_rate))
      elif x['message_text'].startswith("desc"):
        global descent_rate
        descent_rate = float(x['message_text'].split(":")[1])
        print("Setting descent rate to {}".format(ascent_rate))

AIS = aprslib.IS("KC3HOB")
AIS.connect()
AIS.consumer(packet)

