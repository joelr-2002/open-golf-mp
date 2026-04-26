import re

with open("golf.c", 'r') as f:
    content = f.read()

# Add include
content = content.replace('#include "common/graphics.h"', '#include "common/graphics.h"\n#include "common/net.h"')

# Add init and destroy
init_str = """
    golf_game_init();
    golf_ui_init();
"""
new_init = """
    golf_net_init();
    golf_game_init();
    golf_ui_init();
"""
content = content.replace(init_str, new_init)

# we don't have an explicit golf_destroy() ? Let's check.
