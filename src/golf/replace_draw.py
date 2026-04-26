import os

with open("draw.c", 'r') as f:
    content = f.read()

# Replace the ball drawing section with a loop over players
original_block = """
        // Draw the ball
        {
            golf_shader_t *shader = golf_data_get_shader("data/shaders/ball.glsl");
            golf_shader_pipeline_t *pipeline = golf_shader_get_pipeline(shader, "ball");
            sg_apply_pipeline(pipeline->sg_pipeline);

            vec3 ball_pos = game->players[game->local_player_id].ball.draw_pos;
            vec3 ball_scale = V3(game->players[game->local_player_id].ball.radius, game->players[game->local_player_id].ball.radius, game->players[game->local_player_id].ball.radius);
            golf_model_t *model = golf_data_get_model("data/models/golf_ball.obj");
            mat4 model_mat = mat4_multiply_n(3,
                    mat4_translation(ball_pos),
                    mat4_scale(ball_scale),
                    mat4_from_quat(game->players[game->local_player_id].ball.orientation));
            golf_texture_t *texture = golf_data_get_texture("data/textures/golf_ball_normal_map.jpg");
            vec4 color = V4(1, 1, 1, 1);

            sg_bindings bindings = {
                .vertex_buffers[0] = model->sg_positions_buf,
                .vertex_buffers[1] = model->sg_normals_buf,
                .vertex_buffers[2] = model->sg_texcoords_buf,
                .fs_images[0] = texture->sg_image,
            };
            sg_apply_bindings(&bindings);

            golf_shader_uniform_t *vs_uniform = golf_shader_vs_uniform_setup(shader, "ball_vs_params", 2,
                    UNIFORM_MAT4("proj_view_mat", mat4_transpose(graphics->proj_view_mat)),
                    UNIFORM_MAT4("model_mat", mat4_transpose(model_mat)));
            sg_apply_uniforms(SG_SHADERSTAGE_VS, 0, &(sg_range) { vs_uniform->data, vs_uniform->size });

            golf_shader_uniform_t *fs_uniform = golf_shader_fs_uniform_setup(shader, "ball_fs_params", 1,
                    UNIFORM_VEC4("color", color));
            sg_apply_uniforms(SG_SHADERSTAGE_FS, 0, &(sg_range) { fs_uniform->data, fs_uniform->size });

            sg_draw(0, model->positions.length, 1);
        }

        // Draw the ball hidden behind objects
        {
            golf_shader_t *shader = golf_data_get_shader("data/shaders/ball_hidden.glsl");
            golf_shader_pipeline_t *pipeline = golf_shader_get_pipeline(shader, "ball_hidden");
            sg_apply_pipeline(pipeline->sg_pipeline);

            vec3 cam_pos = graphics->cam_pos;
            vec3 ball_pos = game->players[game->local_player_id].ball.draw_pos;
            float ball_radius = game->players[game->local_player_id].ball.radius;
            mat4 model_mat = mat4_multiply_n(2,
                    mat4_translation(ball_pos),
                    mat4_scale(V3(ball_radius + 0.001f, ball_radius + 0.001f, ball_radius + 0.001f)));
            golf_model_t *model = golf_data_get_model("data/models/golf_ball.obj");

            sg_bindings bindings = {
                .vertex_buffers[0] = model->sg_positions_buf,
                .vertex_buffers[1] = model->sg_normals_buf,
            };
            sg_apply_bindings(&bindings);

            golf_shader_uniform_t *vs_uniform = golf_shader_vs_uniform_setup(shader, "vs_params", 2,
                    UNIFORM_MAT4("model_mat", mat4_transpose(model_mat)),
                    UNIFORM_MAT4("proj_view_mat", mat4_transpose(graphics->proj_view_mat)));
            sg_apply_uniforms(SG_SHADERSTAGE_VS, 0, &(sg_range) { vs_uniform->data, vs_uniform->size });

            golf_shader_uniform_t *fs_uniform = golf_shader_fs_uniform_setup(shader, "fs_params", 2,
                    UNIFORM_VEC4("ball_position", V4(ball_pos.x, ball_pos.y, ball_pos.z, 0)),
                    UNIFORM_VEC4("cam_position", V4(cam_pos.x, cam_pos.y, cam_pos.z, 0)));
            sg_apply_uniforms(SG_SHADERSTAGE_FS, 0, &(sg_range) { fs_uniform->data, fs_uniform->size });

            sg_draw(0, model->positions.length, 1);
        }
"""

new_block = """
        for (int p_idx = 0; p_idx < MAX_PLAYERS; p_idx++) {
            if (!game->players[p_idx].active) continue;
            // Draw the ball
            {
                golf_shader_t *shader = golf_data_get_shader("data/shaders/ball.glsl");
                golf_shader_pipeline_t *pipeline = golf_shader_get_pipeline(shader, "ball");
                sg_apply_pipeline(pipeline->sg_pipeline);

                vec3 ball_pos = game->players[p_idx].ball.draw_pos;
                vec3 ball_scale = V3(game->players[p_idx].ball.radius, game->players[p_idx].ball.radius, game->players[p_idx].ball.radius);
                golf_model_t *model = golf_data_get_model("data/models/golf_ball.obj");
                mat4 model_mat = mat4_multiply_n(3,
                        mat4_translation(ball_pos),
                        mat4_scale(ball_scale),
                        mat4_from_quat(game->players[p_idx].ball.orientation));
                golf_texture_t *texture = golf_data_get_texture("data/textures/golf_ball_normal_map.jpg");
                
                vec4 color = V4(1, 1, 1, 1);
                // Maybe different color for other players?
                if (p_idx != game->local_player_id) {
                    color = V4(0.8, 0.2, 0.2, 1); // Redish
                }

                sg_bindings bindings = {
                    .vertex_buffers[0] = model->sg_positions_buf,
                    .vertex_buffers[1] = model->sg_normals_buf,
                    .vertex_buffers[2] = model->sg_texcoords_buf,
                    .fs_images[0] = texture->sg_image,
                };
                sg_apply_bindings(&bindings);

                golf_shader_uniform_t *vs_uniform = golf_shader_vs_uniform_setup(shader, "ball_vs_params", 2,
                        UNIFORM_MAT4("proj_view_mat", mat4_transpose(graphics->proj_view_mat)),
                        UNIFORM_MAT4("model_mat", mat4_transpose(model_mat)));
                sg_apply_uniforms(SG_SHADERSTAGE_VS, 0, &(sg_range) { vs_uniform->data, vs_uniform->size });

                golf_shader_uniform_t *fs_uniform = golf_shader_fs_uniform_setup(shader, "ball_fs_params", 1,
                        UNIFORM_VEC4("color", color));
                sg_apply_uniforms(SG_SHADERSTAGE_FS, 0, &(sg_range) { fs_uniform->data, fs_uniform->size });

                sg_draw(0, model->positions.length, 1);
            }

            // Draw the ball hidden behind objects
            {
                golf_shader_t *shader = golf_data_get_shader("data/shaders/ball_hidden.glsl");
                golf_shader_pipeline_t *pipeline = golf_shader_get_pipeline(shader, "ball_hidden");
                sg_apply_pipeline(pipeline->sg_pipeline);

                vec3 cam_pos = graphics->cam_pos;
                vec3 ball_pos = game->players[p_idx].ball.draw_pos;
                float ball_radius = game->players[p_idx].ball.radius;
                mat4 model_mat = mat4_multiply_n(2,
                        mat4_translation(ball_pos),
                        mat4_scale(V3(ball_radius + 0.001f, ball_radius + 0.001f, ball_radius + 0.001f)));
                golf_model_t *model = golf_data_get_model("data/models/golf_ball.obj");

                sg_bindings bindings = {
                    .vertex_buffers[0] = model->sg_positions_buf,
                    .vertex_buffers[1] = model->sg_normals_buf,
                };
                sg_apply_bindings(&bindings);

                golf_shader_uniform_t *vs_uniform = golf_shader_vs_uniform_setup(shader, "vs_params", 2,
                        UNIFORM_MAT4("model_mat", mat4_transpose(model_mat)),
                        UNIFORM_MAT4("proj_view_mat", mat4_transpose(graphics->proj_view_mat)));
                sg_apply_uniforms(SG_SHADERSTAGE_VS, 0, &(sg_range) { vs_uniform->data, vs_uniform->size });

                golf_shader_uniform_t *fs_uniform = golf_shader_fs_uniform_setup(shader, "fs_params", 2,
                        UNIFORM_VEC4("ball_position", V4(ball_pos.x, ball_pos.y, ball_pos.z, 0)),
                        UNIFORM_VEC4("cam_position", V4(cam_pos.x, cam_pos.y, cam_pos.z, 0)));
                sg_apply_uniforms(SG_SHADERSTAGE_FS, 0, &(sg_range) { fs_uniform->data, fs_uniform->size });

                sg_draw(0, model->positions.length, 1);
            }
        }
"""

content = content.replace(original_block.strip('\n'), new_block.strip('\n'))

with open("draw.c", 'w') as f:
    f.write(content)
