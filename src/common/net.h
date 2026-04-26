#ifndef GOLF_NET_H
#define GOLF_NET_H

#include <stdbool.h>
#include <stdint.h>
#include "common/vec.h"
#include "common/maths.h"

typedef enum golf_packet_type {
    GOLF_PACKET_LOBBY_STATE,
    GOLF_PACKET_SYNC_POS,
    GOLF_PACKET_HIT_BALL,
    GOLF_PACKET_LEVEL_START
} golf_packet_type_t;

typedef struct golf_packet {
    uint8_t type;
} golf_packet_t;

typedef struct golf_packet_sync_pos {
    uint8_t type;
    int client_id;
    vec3 pos;
    vec3 vel;
    bool active;
    int strokes;
} golf_packet_sync_pos_t;

typedef struct golf_packet_hit_ball {
    uint8_t type;
    int client_id;
    vec3 velocity;
} golf_packet_hit_ball_t;

typedef enum golf_net_event_type {
    GOLF_NET_EVENT_NONE,
    GOLF_NET_EVENT_CONNECT,
    GOLF_NET_EVENT_DISCONNECT,
    GOLF_NET_EVENT_RECEIVE
} golf_net_event_type_t;

typedef struct golf_net_event {
    golf_net_event_type_t type;
    int client_id;
    void *data;
    int data_len;
} golf_net_event_t;

void golf_net_init(void);
void golf_net_destroy(void);

bool golf_net_server_create(int port);
bool golf_net_client_create(const char *ip, int port);
void golf_net_disconnect(void);

bool golf_net_is_server(void);
bool golf_net_is_client(void);

// Returns true if an event was dequeued
bool golf_net_update(golf_net_event_t *event);
// After processing a receive event, free the data
void golf_net_free_event(golf_net_event_t *event);

// Client sends to server, Server broadcasts to all clients
void golf_net_send_packet(void *data, int len, bool reliable);
// Server sends to specific client
void golf_net_server_send_packet_to(int client_id, void *data, int len, bool reliable);

#endif
