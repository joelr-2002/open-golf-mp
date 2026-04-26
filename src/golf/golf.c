#include "golf/golf.h"

#include "common/audio.h"
#include "common/data.h"
#include "common/debug_console.h"
#include "common/graphics.h"
#include "common/net.h"
#include "common/log.h"
#include "golf/game.h"
#include "golf/ui.h"

static golf_t golf;
static golf_config_t *game_cfg;
static golf_graphics_t *graphics;
static golf_game_t *game;
static golf_ui_t *ui;

static const char *initial_level_path = "data/levels/level-1.level";

void golf_init(void) {
    golf_data_load(initial_level_path, true);
    snprintf(golf.level_loading_path, GOLF_FILE_MAX_PATH, "%s", initial_level_path);
    golf.state = GOLF_STATE_TITLE_SCREEN;
    golf.title_screen.t = 0;
    graphics = golf_graphics_get();
    ui = golf_ui_get();
    game = golf_game_get();

    golf_net_init();
    golf_game_init();
    golf_ui_init();

    game_cfg = golf_data_get_config("data/config/game.cfg");
}

void golf_update(float dt) {
    golf_net_event_t event;
    while (golf_net_update(&event)) {
        if (event.type == GOLF_NET_EVENT_CONNECT) {
            golf_log_note("Client connected: %d", event.client_id);
            if (golf_net_is_server()) {
                // If it's the host, send level start if in game
                if (golf.state == GOLF_STATE_IN_GAME) {
                    golf_packet_t packet;
                    packet.type = GOLF_PACKET_LEVEL_START;
                    // Not sending full level right now, just generic start 
                    golf_net_server_send_packet_to(event.client_id, &packet, sizeof(packet), true);
                }
            }
        }
        else if (event.type == GOLF_NET_EVENT_DISCONNECT) {
            golf_log_note("Client disconnected: %d", event.client_id);
            if (event.client_id >= 0 && event.client_id < MAX_PLAYERS) {
                game->players[event.client_id].active = false;
            }
        }
        else if (event.type == GOLF_NET_EVENT_RECEIVE) {
            uint8_t packet_type = ((uint8_t*)event.data)[0];
            if (packet_type == GOLF_PACKET_SYNC_POS) {
                golf_packet_sync_pos_t *sync = (golf_packet_sync_pos_t*)event.data;
                if (sync->client_id >= 0 && sync->client_id < MAX_PLAYERS) {
                    game->players[sync->client_id].active = sync->active;
                    // We only overwrite position if we are not the one simulating it, or if it's authoritative
                    if (golf_net_is_client() && sync->client_id != game->local_player_id) {
                        game->players[sync->client_id].ball.pos = sync->pos;
                        game->players[sync->client_id].ball.vel = sync->vel;
                        game->players[sync->client_id].stroke_count = sync->strokes;
                    }
                }
            }
            else if (packet_type == GOLF_PACKET_HIT_BALL) {
                golf_packet_hit_ball_t *hit = (golf_packet_hit_ball_t*)event.data;
                if (hit->client_id >= 0 && hit->client_id < MAX_PLAYERS) {
                    game->players[hit->client_id].ball.vel = hit->velocity;
                    game->players[hit->client_id].ball.is_moving = true;
                    game->players[hit->client_id].stroke_count++;
                }
            }
            else if (packet_type == GOLF_PACKET_LEVEL_START) {
                if (golf_net_is_client() && golf.state != GOLF_STATE_IN_GAME) {
                    golf_start_level(golf.level_num); 
                }
            }
        }
        golf_net_free_event(&event);
    }

    if (golf_net_is_server()) {
        static float network_timer = 0;
        network_timer += dt;
        if (network_timer >= 1.0f / 20.0f) {
            network_timer = 0;
            for (int i = 0; i < MAX_PLAYERS; i++) {
                if (game->players[i].active) {
                    golf_packet_sync_pos_t sync;
                    sync.type = GOLF_PACKET_SYNC_POS;
                    sync.client_id = i;
                    sync.pos = game->players[i].ball.pos;
                    sync.vel = game->players[i].ball.vel;
                    sync.active = game->players[i].active;
                    sync.strokes = game->players[i].stroke_count;
                    golf_net_send_packet(&sync, sizeof(sync), false);
                }
            }
        }
    }

    switch (golf.state) {
        case GOLF_STATE_TITLE_SCREEN: {
            golf.title_screen.t += dt;
            if (golf_data_get_load_state(golf.level_loading_path) == GOLF_DATA_LOADED) {
                golf.level = golf_data_get_level(golf.level_loading_path);
                golf_goto_main_menu(); 
            }
            break;
        }
        case GOLF_STATE_MAIN_MENU: {
            golf.main_menu.t += dt;
            break;
        }
        case GOLF_STATE_LOADING_LEVEL: {
            golf.loading_level.t += dt;
            if (golf_data_get_load_state(golf.level_loading_path) == GOLF_DATA_LOADED) {
                golf.level = golf_data_get_level(golf.level_loading_path);
                golf.state = GOLF_STATE_IN_GAME;
                golf.in_game.t = 0;
                golf_game_start_level();
            }
            break;
        }
        case GOLF_STATE_IN_GAME: {
            golf.in_game.t += dt;
            break;
        }
    }

    if (golf.state == GOLF_STATE_MAIN_MENU || golf.state == GOLF_STATE_IN_GAME) {
        golf_game_update(dt);
    }
    golf_ui_update(dt);
    golf_debug_console_update(dt);
    golf_audio_update(dt);
}

golf_t *golf_get(void) {
    return &golf;
}

void golf_start_level(int level_num) {
    int num_levels = (int)CFG_NUM(game_cfg, "num_levels");
    if (level_num >= num_levels) {
        return;
    }

    if (golf_data_get_load_state(golf.level_loading_path) != GOLF_DATA_LOADED) {
        golf_log_warning("Trying to load level before previous one has finished loading...");
        return;
    }

    golf.level_num = level_num;
    golf.level = NULL;
    golf_data_unload(golf.level_loading_path);

    char level_key[256];
    snprintf(level_key, 256, "level%d", level_num + 1);
    const char *level_path = CFG_STRING(game_cfg, level_key);

    snprintf(golf.level_loading_path, GOLF_FILE_MAX_PATH, "%s", level_path);
    golf_data_load(golf.level_loading_path, true);
    golf.state = GOLF_STATE_LOADING_LEVEL;
}

void golf_goto_main_menu(void) {
    ui->main_menu.is_level_select_open = false;
    golf.state = GOLF_STATE_MAIN_MENU;
    golf.main_menu.t = 0;
    golf_game_start_main_menu();
}
