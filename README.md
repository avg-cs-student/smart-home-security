Smart Home: Security
====================

Purpose:
--------
The goal of this project is to provide a DIY solution to home security through the use of inexpensive and accessible internet of things (IoT) devices.

Although the project is designed to be extensible, the current scope of the project is limited to home intrusion detection.

Features:
---------
- Motion detection at home entryways (or wherever you desire)
- Persistent history of events via local database
- Automated periodic database backups

Getting Started:
================

Necessary Equipment:
--------------------
- RaspberryPi 4 (any Linux computer should work, tested with UbuntuServer 22.04)
    - python3
    - sqlite3
- ESP32 (minimum 1)
    - PIR Sensor (1 per)
    - __OPTIONAL__ SSD1306 OLED Display (1 per)
    - Power supply (3.3V)
    - Some means of connecting components (breadboard/solder/etc)
- WiFi network
- Arduino IDE
    - esp32 espressif board manager
    - Adafruit_SSD1306 Library (FOSS available via Arduino IDE)

Project Layout:
---------------
```
.
├── homesecurityclient              Source code for ESP32
│  ├── homesecurityclient.ino       Install this to ESP32 via Arduino IDE
│  ├── network_settings.h.sample    Edit this to configure ESP32 to local WiFi
│  └── packet.h                     Code for reading and writing data packets
├── homesecurityserver              Source code for local server
│  ├── base.py                      TCP server (non-blocking) logic
│  ├── database.py                  Database logic
│  ├── generate-report.sh           Basic database query example script
│  ├── initdb.sql                   Code for database initialization
│  ├── main.py                      Executable script, creates and runs local python server
│  ├── packet.py                    Code for reading and writing data packets
│  ├── run.sh                       Run this to start the local server
│  └── smarthome-db-backup.sh       Script to be placed in /etc/cron.daily (automated by run.sh)
├── LICENSE
└── README.md                       YOU ARE HERE
```

Server Start:
-------------
- To get your local server's IP address, run:
```
ifconfig
```
- Navigate to the __homesecurityserver/__ directory
- To enable automatic backups (via anacron), run:
```
sudo ./run.sh
```
- To proceed WITHOUT automatic backups, run:
```
./run.sh 
```
__NOTE__: At this point, you should see your server running and waiting on devices to connect.

Client Installation and Start:
------------------------------
- Hardware Connection
| ESP32     | Device    |
|---------- | -------------- |
| GPIO15 (with 2.2k Resistor) | PIR Output |
| GPIO21    | OLED SDA   |
| GPIO22    | OLED SCL   |

- Connect ESP32 via USB and install `homesecurityclient.ino` via Arduino IDE 
- With server running, place sensors and connect power (3.3V)

__NOTE:__ In the `homesecurityclient.ino` file, `SELF_METADATA` must be modified prior to installation for each device to ensure unique, descriptive names.

