#include <arpa/inet.h>
#include <SPI.h>
#include <Wire.h>
#include <Adafruit_SSD1306.h>
#include <WiFi.h>
#include <WiFiMulti.h>
#include "packet.h"
#include "network_settings.h"


// OLED dimensions (in pixels)
#define OLED_WIDTH 128
#define OLED_HEIGHT 64
#define OLED_RESET -1
#define SCREEN_ADDR 0x3c
Adafruit_SSD1306 monitor(OLED_WIDTH, OLED_HEIGHT, &Wire, OLED_RESET);

// Motion Detection
#define PIR_SENSOR_PIN 15	

WiFiMulti WiFiMulti;
WiFiClient sock;
void connect_to_local_wifi(const char *network, const char *pw);
void connect_to_server(uint16_t port, const char *host);

// This changes for each ESP32 in the field
#define SELF_METADATA (uint8_t*)"BACK DOOR"
const size_t PACKET_MAX = 2048;

// These values are updated by the server
uint8_t self_id = 0;
uint32_t local_time = 0;
volatile int pir_state = 0;
volatile bool send_heartbeat = false;
hw_timer_t *timer = NULL;

void IRAM_ATTR onTime()
{
	send_heartbeat = true;
}

void pir_ISR()
{
	pir_state = digitalRead(PIR_SENSOR_PIN);
}


#define  ONE_SECOND          1000
#define  ONE_MINUTE          (60   *  ONE_SECOND * 1000) // usecs for timer
#define  HEARTBEAT_INTERVAL  (5    *  ONE_MINUTE)

void setup() {
	Serial.begin(115200);
	delay(ONE_SECOND);

	// OLED setup
	if (!monitor.begin(SSD1306_SWITCHCAPVCC, SCREEN_ADDR)) {
		Serial.println(F("Monitor allocation failed"));
		while(true); // infinite fail
	}
	monitor.setTextSize(1);
	monitor.setTextColor(SSD1306_WHITE);
	monitor.setCursor(0,0); // top left
	monitor.cp437(true); // font selection
	monitor.clearDisplay();

	// Network setup
	WiFiMulti.addAP(WIFI_NETWORK, WIFI_PW);
	connect_to_local_wifi(WIFI_NETWORK, WIFI_PW);
	delay(ONE_SECOND);
	connect_to_server(NETWORK_PORT, HOST_ADDR);

	// PIR Sensor setup
	pinMode(PIR_SENSOR_PIN, INPUT);
	attachInterrupt(PIR_SENSOR_PIN, pir_ISR, HIGH);

	// Timer setup
	const bool COUNT_UP = true;
	const int PRESCALER = 80;
	const bool AUTO_RELOAD = true;
	timer = timerBegin(0, PRESCALER, COUNT_UP);
	timerAttachInterrupt(timer, &onTime, true);
	timerAlarmWrite(timer, HEARTBEAT_INTERVAL, AUTO_RELOAD);
	timerAlarmEnable(timer); 
}

const uint8_t *msg = (uint8_t*)"Motion detected.";
const uint8_t *heartbeat = (uint8_t*)"All clear.";

void loop() {
	monitor.clearDisplay();
	monitor.display();

	if (pir_state) {
		pir_state = 0;
		monitor.setCursor(0,0); // top left
		monitor.write((char*)msg);
		monitor.write("\n");
		monitor.display();
		packet_send(sock, self_id, status_update_pkt, msg);
		delay(5 * ONE_SECOND);
	}
	// timer has elapsed, send heartbeat
	if (send_heartbeat) {
		send_heartbeat = false;
		monitor.clearDisplay();
		monitor.display();
		monitor.setCursor(0,0); // top left
		monitor.write((char*)heartbeat);
		monitor.write("\n");
		monitor.display();
		packet_send(sock, self_id, heartbeat_pkt, heartbeat);
		delay(ONE_SECOND);
		timer = NULL;
	}
}

void connect_to_local_wifi(const char *network, const char *pw)
{
	WiFiMulti.addAP(network, pw);
	Serial.print("Waiting for WiFi...");
	monitor.write("Waiting for WiFi...");
	monitor.display();


	while(WiFiMulti.run() != WL_CONNECTED) {
		Serial.print(".");
		delay(ONE_SECOND / 2);
	}

	Serial.println("");
	Serial.println("WiFi connected!");
	Serial.println("IP address: ");
	Serial.println(WiFi.localIP());
	monitor.write("\nWiFi connected!\n");
	monitor.write(WiFi.localIP().toString().c_str());
	monitor.display();
}

void connect_to_server(uint16_t port, const char *host)
{
	Serial.print("Connecting to ");
	monitor.write("Connecting to ");
	Serial.println(host);
	monitor.write(host);
	monitor.display();

	if (!sock.connect(host, port)) {
		Serial.println("Connection failed.");
		Serial.println("Waiting 10 before retrying...");
		monitor.write("Connection failed.\n");
		monitor.write("Waiting 10 before retrying...\n");
		monitor.display();
		delay(10 * ONE_SECOND);
		monitor.clearDisplay();
		return;
	}

	packet_send(sock, self_id, client_register_pkt, SELF_METADATA);

	int maxloops = 0;

	// wait for server ACK pkt
	while (!sock.available() && maxloops < ONE_SECOND) {
		maxloops++;
		delay(1); // delay 1msec
	}	

	if (sock.available() > 0) {
		packet_receive_ack(&sock, &local_time, &self_id);
		Serial.println("Received server ACK");
		Serial.print("Assigned id is: ");
		Serial.println(self_id);
	} else {
		Serial.println("sock.available() timed out");
		Serial.println("Waiting 10s before retrying...");
		delay(10 * ONE_SECOND);
	}
}
