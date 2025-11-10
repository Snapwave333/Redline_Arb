// Visual effects system

// Smoothing helpers
fn smootherstep(edge0: f32, edge1: f32, x: f32) -> f32 {
    let t = clamp((x - edge0) / (edge1 - edge0), 0.0, 1.0);
    return t * t * t * (t * (t * 6.0 - 15.0) + 10.0);
}

fn ease_out_cubic(t: f32) -> f32 {
    let u = clamp(t, 0.0, 1.0);
    return 1.0 - pow(1.0 - u, 3.0);
}

fn apply_effect(position: vec2<f32>, uv: vec2<f32>, color: vec3<f32>, time: f32) -> vec3<f32> {
    let elapsed = time - uniforms.effect_time;
    
    if elapsed < 0.0 || elapsed > 3.0 {
        return color;
    }
    
    let center = vec2<f32>(0.5, 0.5);
    let dist_from_center = distance(position, center);
    
    let expansion_speed = 0.5;
    let expansion_radius = elapsed * expansion_speed;
    
    // Pixel-size aware thickness to reduce aliasing/flicker on thin edges
    let px = 1.0 / max(uniforms.resolution.x, uniforms.resolution.y);
    
    var effect_strength = 0.0;
    
    if uniforms.effect_type == 0u {
        let ring_thickness = 0.10 + px * 2.0;
        let ring_dist = abs(dist_from_center - expansion_radius);
        effect_strength = 1.0 - smootherstep(0.0, ring_thickness, ring_dist);
    } else if uniforms.effect_type == 1u {
        let dx = abs(position.x - center.x);
        let dy = abs(position.y - center.y);
        let cross_dist = min(dx, dy);
        let cross_ring = abs(max(dx, dy) - expansion_radius);
        let cross_thickness = 0.08 + px * 2.0;
        
        if cross_dist < 0.03 {
            effect_strength = 1.0 - smootherstep(0.0, cross_thickness, cross_ring);
        }
    } else if uniforms.effect_type == 2u {
        let dx = position.x - center.x;
        let dy = position.y - center.y;
        let diamond_dist = abs(dx) + abs(dy);
        let diamond_ring = abs(diamond_dist - expansion_radius);
        let diamond_thickness = 0.10 + px * 2.0;
        effect_strength = 1.0 - smootherstep(0.0, diamond_thickness, diamond_ring);
    } else if uniforms.effect_type == 3u {
        let angle = atan2(position.y - center.y, position.x - center.x);
        let num_rays = 8.0;
        let ray_angle = fract(angle / (6.28318 / num_rays));
        let ray_proximity = abs(ray_angle - 0.5) * 2.0;
        let ray_width = 0.20 + px * 2.0;
        
        if ray_proximity < ray_width && dist_from_center < expansion_radius {
            let ray_fade = 1.0 - (dist_from_center / expansion_radius);
            effect_strength = (1.0 - ray_proximity / ray_width) * ray_fade * 0.7;
        }
    } else if uniforms.effect_type == 4u {
        let grid_size = 0.1;
        let grid_x = abs(fract(position.x / grid_size) - 0.5) * 2.0;
        let grid_y = abs(fract(position.y / grid_size) - 0.5) * 2.0;
        let grid_proximity = min(grid_x, grid_y);
        let grid_width = 0.40 + px * 2.0;
        
        if grid_proximity < grid_width && dist_from_center < expansion_radius {
            let grid_fade = 1.0 - (dist_from_center / expansion_radius);
            effect_strength = (1.0 - grid_proximity / grid_width) * grid_fade * 0.5;
        }
    } else if uniforms.effect_type == 5u {
        // Octgrams-style starburst with modded repetition and box sdf-like spokes
        let angle = atan2(position.y - center.y, position.x - center.x);
        let radius = dist_from_center + 1e-5;
        let num_arms = 8.0;
        let k = 3.14159265 / num_arms; // sector half-angle
        let m = abs(fract((angle + time * 0.2) / (2.0 * k)) - 0.5) * 2.0; // repeating wedge
        let spoke = 1.0 - smootherstep(0.0, 0.25 + px * 2.0, m);
        let ring = 1.0 - smootherstep(0.0, 0.06 + px * 2.0, abs(radius - expansion_radius));
        let core = 1.0 - smootherstep(0.0, 0.15 + px * 2.0, radius);
        effect_strength = (spoke * 0.8 + ring * 0.6 + core * 0.4) * 0.9;
    } else {
        let wave_y = center.y + sin(position.x * 9.0 - elapsed * 4.5) * 0.1;
        let wave_dist = abs(position.y - wave_y);
        let wave_thickness = 0.08 + px * 2.0;
        effect_strength = 1.0 - smootherstep(0.0, wave_thickness, wave_dist);
    }
    
    // Smoother fade-out over time
    let t = clamp(elapsed / 3.0, 0.0, 1.0);
    let fade = 1.0 - ease_out_cubic(t);
    effect_strength = effect_strength * fade;
    
    // Gentle nonlinearity to avoid harsh transitions
    effect_strength = pow(effect_strength, 0.85);
    
    var effect_color: vec3<f32>;
    
    let effect_index = uniforms.effect_type % 7u;
    if effect_index == 0u {
        effect_color = vec3<f32>(0.2, 0.5, 0.9);
    } else if effect_index == 1u {
        effect_color = vec3<f32>(0.9, 0.3, 0.5);
    } else if effect_index == 2u {
        effect_color = vec3<f32>(0.3, 0.9, 0.5);
    } else if effect_index == 3u {
        effect_color = vec3<f32>(0.9, 0.7, 0.2);
    } else if effect_index == 4u {
        effect_color = vec3<f32>(0.7, 0.2, 0.9);
    } else {
        effect_color = vec3<f32>(0.2, 0.9, 0.9);
    }
    
    return mix(color, effect_color, effect_strength * 0.7);
}
