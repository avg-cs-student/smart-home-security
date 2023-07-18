#ifndef CONNECT_H
#define CONNECT_H

void connect_to_local_wifi(const char *network, const char *pw)
{
	WiFiMulti.addAP(WIFI_NETWORK, WIFI_PW);
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
#endif
