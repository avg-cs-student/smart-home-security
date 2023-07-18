#ifndef PACKET_H
#define PACKET_H

#define PACKET_HEADER_SIZE	10

enum PacketType {
	client_register_pkt,
	server_ack_pkt, // unused
	status_update_pkt,
	heartbeat_pkt,
	img_pkt
};

extern const size_t PACKET_MAX;

// Errors
#define OK			0
#define UNKNOWN_PACKET_RECEIVED 1
uint32_t packet_err = OK;
	

void _packet_load(PacketType type, 
		uint32_t self_id,
		const uint8_t *msg,
		size_t *pkt_len,
		uint8_t *packet_buf)
{
	// get total packet length
	*pkt_len = strlen((char*)msg) + PACKET_HEADER_SIZE;
	uint8_t priority = 2;

	if (type == client_register_pkt) {
		packet_buf[0] = 0x00;
	} else if (type == status_update_pkt) {
		packet_buf[0] = 0x02;
	} else if (type == img_pkt) {
		packet_buf[0] = 0x03;
	} else if (type == heartbeat_pkt) {
		packet_buf[0] = 0x02;
		priority = 0x01;
	}

	packet_buf[4] = self_id;
	packet_buf[5] = priority;
	packet_buf[6] = strlen((char*)msg) >> 24;
	packet_buf[7] = strlen((char*)msg) >> 16;
	packet_buf[8] = strlen((char*)msg) >> 8;
	packet_buf[9] = strlen((char*)msg);
	memcpy(&packet_buf[PACKET_HEADER_SIZE], msg, *pkt_len);
}

void packet_send(WiFiClient sock,
		 uint32_t self_id,
		 PacketType type,
		 const uint8_t *msg)
{
	size_t pkt_len = 0;
	uint8_t packet_buf[PACKET_MAX] = {0};

	// placeholder 100 for seq num
	_packet_load(type, self_id, msg, &pkt_len, packet_buf);
	sock.write(packet_buf, pkt_len);
}

void packet_receive_ack(WiFiClient *sock,
			uint32_t *local_time,
			uint8_t *self_id)
{
	uint8_t packet_buf[1000];
	sock->read(packet_buf, 1000);

	if (packet_buf[0] != 0x02)
		packet_err = UNKNOWN_PACKET_RECEIVED;	

	*self_id = packet_buf[1];
	*local_time = 0;
	*local_time |= packet_buf[2] << 12;
	*local_time |= packet_buf[3] << 8;
	*local_time |= packet_buf[4] << 4;
	*local_time |= packet_buf[5];
}

#endif
