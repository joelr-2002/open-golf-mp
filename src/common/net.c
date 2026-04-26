#include "common/net.h"
#include "common/alloc.h"
#include "common/log.h"
#include <string.h>

#ifndef GOLF_PLATFORM_EMSCRIPTEN
#include <enet/enet.h>

static bool is_server = false;
static bool is_client = false;

static ENetHost *host = NULL;
static ENetPeer *client_peer = NULL;

void golf_net_init(void) {
    if (enet_initialize() != 0) {
        golf_log_error("An error occurred while initializing ENet.");
        return;
    }
}

void golf_net_destroy(void) {
    golf_net_disconnect();
    enet_deinitialize();
}

bool golf_net_server_create(int port) {
    if (host) golf_net_disconnect();
    ENetAddress address;
    address.host = ENET_HOST_ANY;
    address.port = port;
    host = enet_host_create(&address, 32, 2, 0, 0);
    if (host == NULL) {
        golf_log_error("An error occurred while trying to create an ENet server host.");
        return false;
    }
    is_server = true;
    is_client = false;
    return true;
}

bool golf_net_client_create(const char *ip, int port) {
    if (host) golf_net_disconnect();
    host = enet_host_create(NULL, 1, 2, 0, 0);
    if (host == NULL) {
        golf_log_error("An error occurred while trying to create an ENet client host.");
        return false;
    }
    ENetAddress address;
    enet_address_set_host(&address, ip);
    address.port = port;
    client_peer = enet_host_connect(host, &address, 2, 0);
    if (client_peer == NULL) {
        golf_log_error("No available peers for initiating an ENet connection.");
        return false;
    }
    is_client = true;
    is_server = false;
    return true;
}

void golf_net_disconnect(void) {
    if (client_peer) {
        enet_peer_disconnect(client_peer, 0);
        // Wait for disconnect
        ENetEvent event;
        while (enet_host_service(host, &event, 3000) > 0) {
            switch (event.type) {
                case ENET_EVENT_TYPE_RECEIVE:
                    enet_packet_destroy(event.packet);
                    break;
                case ENET_EVENT_TYPE_DISCONNECT:
                    goto end;
                default:
                    break;
            }
        }
        enet_peer_reset(client_peer);
    }
end:
    client_peer = NULL;
    if (host) {
        enet_host_destroy(host);
        host = NULL;
    }
    is_server = false;
    is_client = false;
}

bool golf_net_is_server(void) {
    return is_server;
}

bool golf_net_is_client(void) {
    return is_client;
}

bool golf_net_update(golf_net_event_t *out_event) {
    if (!host) return false;
    ENetEvent event;
    if (enet_host_service(host, &event, 0) > 0) {
        switch (event.type) {
            case ENET_EVENT_TYPE_CONNECT:
                out_event->type = GOLF_NET_EVENT_CONNECT;
                out_event->client_id = event.peer->connectID; // simplistic client ID
                event.peer->data = (void*)(intptr_t)out_event->client_id;
                out_event->data = NULL;
                out_event->data_len = 0;
                return true;
            case ENET_EVENT_TYPE_RECEIVE:
                out_event->type = GOLF_NET_EVENT_RECEIVE;
                out_event->client_id = (int)(intptr_t)event.peer->data;
                if (!is_server) {
                    out_event->client_id = 0; // server is 0
                }
                out_event->data_len = event.packet->dataLength;
                out_event->data = golf_alloc(out_event->data_len);
                memcpy(out_event->data, event.packet->data, out_event->data_len);
                enet_packet_destroy(event.packet);
                return true;
            case ENET_EVENT_TYPE_DISCONNECT:
                out_event->type = GOLF_NET_EVENT_DISCONNECT;
                out_event->client_id = (int)(intptr_t)event.peer->data;
                event.peer->data = NULL;
                out_event->data = NULL;
                out_event->data_len = 0;
                return true;
            case ENET_EVENT_TYPE_NONE:
                break;
        }
    }
    return false;
}

void golf_net_free_event(golf_net_event_t *event) {
    if (event->data) {
        golf_free(event->data);
        event->data = NULL;
    }
}

void golf_net_send_packet(void *data, int len, bool reliable) {
    if (!host) return;
    ENetPacket *packet = enet_packet_create(data, len, reliable ? ENET_PACKET_FLAG_RELIABLE : 0);
    if (is_server) {
        enet_host_broadcast(host, 0, packet);
    } else if (is_client && client_peer) {
        enet_peer_send(client_peer, 0, packet);
    }
}

void golf_net_server_send_packet_to(int client_id, void *data, int len, bool reliable) {
    if (!host || !is_server) return;
    for (size_t i = 0; i < host->peerCount; ++i) {
        ENetPeer *peer = &host->peers[i];
        if (peer->state != ENET_PEER_STATE_CONNECTED) continue;
        int id = (int)(intptr_t)peer->data;
        if (id == client_id) {
            ENetPacket *packet = enet_packet_create(data, len, reliable ? ENET_PACKET_FLAG_RELIABLE : 0);
            enet_peer_send(peer, 0, packet);
            break;
        }
    }
}

#else

void golf_net_init(void) {}
void golf_net_destroy(void) {}
bool golf_net_server_create(int port) { return false; }
bool golf_net_client_create(const char *ip, int port) { return false; }
void golf_net_disconnect(void) {}
bool golf_net_is_server(void) { return false; }
bool golf_net_is_client(void) { return false; }
bool golf_net_update(golf_net_event_t *out_event) { return false; }
void golf_net_free_event(golf_net_event_t *event) {}
void golf_net_send_packet(void *data, int len, bool reliable) {}
void golf_net_server_send_packet_to(int client_id, void *data, int len, bool reliable) {}

#endif
