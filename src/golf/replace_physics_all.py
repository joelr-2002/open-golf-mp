import re

with open("game.c", 'r') as f:
    content = f.read()

# Replace _physics_tick signature
content = content.replace("static void _physics_tick(float dt) {", "static void _physics_tick(int p_idx, float dt) {")

# Find the body of _physics_tick
start_idx = content.find("static void _physics_tick(int p_idx, float dt) {")
if start_idx != -1:
    end_idx = content.find("void golf_game_update(float dt) {")
    body = content[start_idx:end_idx]
    
    # Replace game.local_player_id with p_idx ONLY inside _physics_tick
    new_body = body.replace("game.players[game.local_player_id].ball", "game.players[p_idx].ball")
    
    content = content[:start_idx] + new_body + content[end_idx:]

# In golf_game_update, loop over players
old_loop = """
        vec3 bp_prev = game.players[game.local_player_id].ball.pos;
        int num_ticks = 0;
        while (game.physics.time_behind >= 0 && num_ticks < 5) {
            bp_prev = game.players[game.local_player_id].ball.pos;
            _physics_tick(physics_dt);
            game.physics.time_behind -= physics_dt;
            num_ticks++;
        }
        while (game.physics.time_behind >= 0) {
            game.physics.time_behind -= physics_dt;
        }

        float alpha = (float)(-game.physics.time_behind / physics_dt);
        game.players[game.local_player_id].ball.draw_pos = vec3_add(vec3_scale(game.players[game.local_player_id].ball.pos, 1.0f - alpha), vec3_scale(bp_prev, alpha));
"""

new_loop = """
        // Ticking physics for all active players
        vec3 bp_prev[MAX_PLAYERS];
        for (int p_idx = 0; p_idx < MAX_PLAYERS; p_idx++) {
            if (game.players[p_idx].active) {
                bp_prev[p_idx] = game.players[p_idx].ball.pos;
            }
        }
        
        int num_ticks = 0;
        float time_behind_save = game.physics.time_behind;
        while (game.physics.time_behind >= 0 && num_ticks < 5) {
            for (int p_idx = 0; p_idx < MAX_PLAYERS; p_idx++) {
                if (game.players[p_idx].active) {
                    bp_prev[p_idx] = game.players[p_idx].ball.pos;
                    _physics_tick(p_idx, physics_dt);
                }
            }
            game.physics.time_behind -= physics_dt;
            num_ticks++;
        }
        while (game.physics.time_behind >= 0) {
            game.physics.time_behind -= physics_dt;
        }

        float alpha = (float)(-game.physics.time_behind / physics_dt);
        for (int p_idx = 0; p_idx < MAX_PLAYERS; p_idx++) {
            if (game.players[p_idx].active) {
                game.players[p_idx].ball.draw_pos = vec3_add(
                    vec3_scale(game.players[p_idx].ball.pos, 1.0f - alpha), 
                    vec3_scale(bp_prev[p_idx], alpha)
                );
            }
        }
"""

if old_loop in content:
    content = content.replace(old_loop, new_loop)
else:
    print("Could not find old_loop")
    
# Replace other globals just like replace_game_ui
content = content.replace("game.ball", "game.players[game.local_player_id].ball")
content = content.replace("game.stroke_count", "game.players[game.local_player_id].stroke_count")

with open("game.c", 'w') as f:
    f.write(content)
