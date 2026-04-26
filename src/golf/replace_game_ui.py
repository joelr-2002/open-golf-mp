import os

def replace_in_file(path):
    with open(path, 'r') as f:
        content = f.read()

    # global singletons
    content = content.replace("game.ball", "game.players[game.local_player_id].ball")
    content = content.replace("game->ball", "game->players[game->local_player_id].ball")
    content = content.replace("game.stroke_count", "game.players[game.local_player_id].stroke_count")
    content = content.replace("game->stroke_count", "game->players[game->local_player_id].stroke_count")

    with open(path, 'w') as f:
        f.write(content)

replace_in_file("game.c")
replace_in_file("ui.c")
