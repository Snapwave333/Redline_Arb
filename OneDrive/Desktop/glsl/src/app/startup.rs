use anyhow::Result;
use crossterm::{
    cursor::{Hide, MoveTo, Show},
    style::{Color, ResetColor, SetForegroundColor, SetBackgroundColor},
    terminal::{Clear, ClearType},
    queue,
};
use std::io::{stdout, Write};
use std::time::{Duration, Instant};

// Simple xorshift RNG to avoid adding dependencies
fn rng_next(seed: &mut u32) -> u32 {
    *seed ^= *seed << 13;
    *seed ^= *seed >> 17;
    *seed ^= *seed << 5;
    *seed
}

fn noise_char(seed: &mut u32) -> char {
    let set = ["#", "$", "!", "@", "%", "&"]; // some high-impact glyphs
    let idx = (rng_next(seed) as usize) % set.len();
    set[idx].chars().next().unwrap()
}

fn cycle_color(seed: &mut u32) -> Color {
    // Neon Pink, Electric Blue, Bright Yellow cycling
    match (rng_next(seed) % 3) as u8 {
        0 => Color::Magenta,
        1 => Color::Blue,
        _ => Color::Yellow,
    }
}

fn clear_screen(buf: &mut Vec<u8>) {
    queue!(buf, Clear(ClearType::All), MoveTo(0, 0)).ok();
}

fn flush_buf(buf: &mut Vec<u8>) -> Result<()> {
    let mut out = stdout();
    out.write_all(buf)?;
    out.flush()?;
    buf.clear();
    Ok(())
}

fn draw_system_logs(buf: &mut Vec<u8>, width: u16, height: u16, frame: usize) {
    // Mock high-speed logs with per-message color for more impact
    let messages = [
        "[INIT] Core GPU Link... OK",
        "[LOAD] Palette Registry... OK",
        "[WARN] VRAM Hot Swap Enabled",
        "[ERROR] Data Integrity Check... FAIL",
        "[OVERRIDE] Generative Core... BYPASSED",
        "[SCAN] Shader Cache Indexing...",
        "[IO] Terminal DMA Boost... ACTIVE",
        "[AUTH] Operator Override... GRANTED",
        "[SYNC] Frameclock... LOCKED",
        "[BOOT] Pixel Matrix... CHARGING",
        "[CRITICAL] Visual Safety Limits... DISABLED",
        "[LINK] Audio Bus... MUTED",
    ];

    let lines_per_frame = ((height as usize) / 2).max(10); // denser
    let start_line = frame * lines_per_frame;
    let mut y = 0u16;
    for i in 0..lines_per_frame {
        let idx = (start_line + i) % messages.len();
        let msg = messages[idx];
        let truncated = if msg.len() as u16 > width { &msg[..width as usize] } else { msg };
        // Color selection
        let col = if msg.contains("ERROR") || msg.contains("CRITICAL") {
            Color::Red
        } else if msg.contains("WARN") {
            Color::Yellow
        } else if msg.contains("OVERRIDE") || msg.contains("AUTH") {
            Color::Magenta
        } else if msg.contains("INIT") || msg.contains("LOAD") || msg.contains("BOOT") {
            Color::Cyan
        } else {
            Color::Green
        };
        queue!(buf, MoveTo(0, y), SetForegroundColor(col)).ok();
        queue!(buf, crossterm::style::Print(truncated)).ok();
        y += 1;
        if y >= height { break; }
    }
    queue!(buf, ResetColor).ok();
}

fn glitch_sub_reveal(buf: &mut Vec<u8>, width: u16, height: u16, seed: &mut u32, elapsed: Duration) {
    // Fill with noise
    for y in 0..height {
        queue!(buf, MoveTo(0, y)).ok();
        for _x in 0..width {
            let ch = noise_char(seed);
            let col = cycle_color(seed);
            queue!(buf, SetForegroundColor(col), crossterm::style::Print(ch)).ok();
        }
    }
    // Briefly coalesce into "PIXEL PUSHER PLUS" near center for a subliminal flash
    let title = "PIXEL PUSHER PLUS";
    let tx = width.saturating_sub(title.len() as u16) / 2;
    let ty = height / 2;
    let flicker = if elapsed.as_millis() % 100 < 50 { Color::White } else { Color::Magenta };
    let mut glitched: String = title
        .chars()
        .map(|c| {
            // randomly corrupt some characters
            if (rng_next(seed) % 5) == 0 { noise_char(seed) } else { c }
        })
        .collect();
    // Ensure we keep length consistent
    glitched.truncate(title.len());
    queue!(buf, MoveTo(tx, ty), SetForegroundColor(flicker), crossterm::style::Print(glitched)).ok();
    queue!(buf, ResetColor).ok();
}

fn render_big_chroma(buf: &mut Vec<u8>, width: u16, height: u16) {
    // Simple block font just for CHROMA (7 rows)
    let c = [
        " ###### ",
        "##      ",
        "##      ",
        "##      ",
        "##      ",
        "##      ",
        " ###### ",
    ];
    let h = [
        "##   ## ",
        "##   ## ",
        "##   ## ",
        "####### ",
        "##   ## ",
        "##   ## ",
        "##   ## ",
    ];
    let r = [
        "####### ",
        "##   ## ",
        "##   ## ",
        "####### ",
        "##  ##  ",
        "##   ## ",
        "##    ##",
    ];
    let o = [
        " ###### ",
        "##    ##",
        "##    ##",
        "##    ##",
        "##    ##",
        "##    ##",
        " ###### ",
    ];
    let m = [
        "##    ##",
        "###  ###",
        "########",
        "## ## ##",
        "##    ##",
        "##    ##",
        "##    ##",
    ];
    let a = [
        "  ####  ",
        " ##  ## ",
        "##    ##",
        "########",
        "##    ##",
        "##    ##",
        "##    ##",
    ];
    let letters = [&c, &h, &r, &o, &m, &a];
    let spacing = 2;
    let letter_w = c[0].len() as u16;
    let total_w = letters.len() as u16 * (letter_w + spacing) - spacing;
    let start_x = width.saturating_sub(total_w) / 2;
    let start_y = height.saturating_sub(7) / 2;

    for (li, letter) in letters.iter().enumerate() {
        let x = start_x + (li as u16) * (letter_w + spacing);
        for (row_i, row) in letter.iter().enumerate() {
            let y = start_y + row_i as u16;
            if y >= height { continue; }
            queue!(buf, MoveTo(x, y), SetForegroundColor(Color::White), crossterm::style::Print(*row)).ok();
        }
    }
    queue!(buf, ResetColor).ok();
}

fn glitch_eruption_around_title(buf: &mut Vec<u8>, width: u16, height: u16, seed: &mut u32) {
    // Compute bounding box used in render_big_chroma
    let letter_w = 9u16; // width of rows above
    let spacing = 2u16;
    let total_w = 6 * (letter_w + spacing) - spacing; // CHROMA = 6 letters
    let start_x = width.saturating_sub(total_w) / 2;
    let start_y = height.saturating_sub(7) / 2;
    let bb_x0 = start_x;
    let bb_y0 = start_y;
    let bb_x1 = (start_x + total_w).min(width);
    let bb_y1 = (start_y + 7).min(height);

    // Draw random colored glyphs outside the title bounding box
    for y in 0..height {
        queue!(buf, MoveTo(0, y)).ok();
        for x in 0..width {
            let inside = x >= bb_x0 && x < bb_x1 && y >= bb_y0 && y < bb_y1;
            if inside { queue!(buf, crossterm::style::Print(" ")).ok(); continue; }
            let ch = noise_char(seed);
            let col = cycle_color(seed);
            queue!(buf, SetForegroundColor(col), crossterm::style::Print(ch)).ok();
        }
    }
    queue!(buf, ResetColor).ok();
}

fn fade_to_black(buf: &mut Vec<u8>) {
    queue!(buf, Clear(ClearType::All), MoveTo(0, 0)).ok();
}

// --- Spaceship Launch ASCII Helpers ---
fn draw_starfield(buf: &mut Vec<u8>, width: u16, height: u16, density: u16, seed: &mut u32) {
    for _ in 0..density {
        let x = (rng_next(seed) % width as u32) as u16;
        let y = (rng_next(seed) % height as u32) as u16;
        let glyph = if (rng_next(seed) % 5) == 0 { '*' } else { '.' };
        let col = if (rng_next(seed) % 4) == 0 { Color::White } else { Color::Grey };
        queue!(buf, MoveTo(x, y), SetForegroundColor(col), crossterm::style::Print(glyph)).ok();
    }
    queue!(buf, ResetColor).ok();
}

fn draw_rocket(buf: &mut Vec<u8>, width: u16, height: u16, base_x: i16, base_y: i16) {
    // Simple retro rocket (7 lines)
    let art = [
        "   /\\   ",
        "  /  \\  ",
        " /====\\ ",
        " | /\\ | ",
        " | | | | ",
        " | | | | ",
        "  |___|  ",
    ];
    let rocket_w = art[0].len() as i16;
    let x = base_x - rocket_w / 2;
    for (i, row) in art.iter().enumerate() {
        let y = base_y - i as i16;
        if x >= 0 && y >= 0 && (x as u16) < width && (y as u16) < height {
            queue!(buf, MoveTo(x as u16, y as u16), SetForegroundColor(Color::White), crossterm::style::Print(*row)).ok();
        }
    }
    queue!(buf, ResetColor).ok();
}

fn draw_exhaust(buf: &mut Vec<u8>, width: u16, height: u16, base_x: i16, base_y: i16, intensity: u16, seed: &mut u32) {
    // Flickering flame plume below rocket base
    let plume_h = (intensity.min(12)) as i16;
    for dy in 1..=plume_h {
        let spread = dy + (rng_next(seed) % 3) as i16;
        for dx in -spread..=spread {
            let x = base_x + dx;
            let y = base_y + dy;
            if x < 0 || y < 0 || (x as u16) >= width || (y as u16) >= height { continue; }
            let col = match rng_next(seed) % 4 { 0 => Color::Yellow, 1 => Color::Red, 2 => Color::Magenta, _ => Color::White };
            let glyph = match rng_next(seed) % 5 { 0 => 'V', 1 => '^', 2 => '~', 3 => '#', _ => '|' };
            queue!(buf, MoveTo(x as u16, y as u16), SetForegroundColor(col), crossterm::style::Print(glyph)).ok();
        }
    }
    queue!(buf, ResetColor).ok();
}

fn draw_star_streaks(buf: &mut Vec<u8>, width: u16, height: u16, count: u16, seed: &mut u32, progress: f32) {
    // Warp streaks to imply velocity (lines angled slightly)
    for _ in 0..count {
        let x = (rng_next(seed) % width as u32) as i16;
        let y = (rng_next(seed) % height as u32) as i16;
        let len = ((progress * 6.0) as i16).max(2);
        let angle = (rng_next(seed) % 3) as i16 - 1; // -1, 0, 1
        let col = match rng_next(seed) % 3 { 0 => Color::Cyan, 1 => Color::Blue, _ => Color::White };
        for i in 0..len {
            let sx = x + i * angle;
            let sy = y - i; // streak upward
            if sx >= 0 && sy >= 0 && (sx as u16) < width && (sy as u16) < height {
                queue!(buf, MoveTo(sx as u16, sy as u16), SetForegroundColor(col), crossterm::style::Print('-')).ok();
            }
        }
    }
    queue!(buf, ResetColor).ok();
}

// --- New 16-Second Cinematic Launch Sequence Helpers ---

fn draw_preflight_diagnostics(buf: &mut Vec<u8>, width: u16, height: u16, elapsed: Duration, seed: &mut u32) {
    // Flickering green diagnostic text in corners
    let diagnostics = [
        "SYS_CHECK",
        "PWR_OK",
        "LINK_UP",
        "READY",
        "INIT_OK",
        "BOOT_OK",
        "CORE_OK",
        "GPU_OK",
    ];
    
    // Flicker every 200ms
    let flicker = (elapsed.as_millis() / 200) % 2 == 0;
    if !flicker { return; }
    
    // Corner positions
    let corners = [
        (2, 2),                           // Top-left
        (width.saturating_sub(10), 2),    // Top-right
        (2, height.saturating_sub(2)),     // Bottom-left
        (width.saturating_sub(10), height.saturating_sub(2)), // Bottom-right
    ];
    
    for (i, (x, y)) in corners.iter().enumerate() {
        if i < diagnostics.len() {
            let msg = diagnostics[i];
            queue!(buf, MoveTo(*x, *y), SetForegroundColor(Color::Green), crossterm::style::Print(msg)).ok();
        }
    }
    queue!(buf, ResetColor).ok();
}

fn draw_ignition_sequence(buf: &mut Vec<u8>, width: u16, height: u16, elapsed: Duration, seed: &mut u32) {
    // Large block text: [IGNITION SEQUENCE ACTIVE]
    let ignition_text = "[IGNITION SEQUENCE ACTIVE]";
    let ignition_x = width.saturating_sub(ignition_text.len() as u16) / 2;
    let ignition_y = height.saturating_sub(3);
    
    // Flash between bright yellow and red
    let flash_color = if (elapsed.as_millis() / 100) % 2 == 0 { Color::Yellow } else { Color::Red };
    queue!(buf, MoveTo(ignition_x, ignition_y), SetForegroundColor(flash_color), crossterm::style::Print(ignition_text)).ok();
    
    // PIXEL PUSHER PLUS with aggressive glitch corruption
    let title = "PIXEL PUSHER PLUS";
    let title_x = width.saturating_sub(title.len() as u16) / 2;
    let title_y = height / 2;
    
    // Create glitched version
    let mut glitched = String::new();
    for (i, c) in title.chars().enumerate() {
        if (rng_next(seed) % 3) == 0 {
            // Corrupt character with random glyph
            let corrupt_chars = ['#', '@', '%', '&', '*', '+', '~'];
            let corrupt_char = corrupt_chars[(rng_next(seed) % corrupt_chars.len() as u32) as usize];
            glitched.push(corrupt_char);
        } else {
            glitched.push(c);
        }
    }
    
    // Color alternates between red and orange
    let title_color = if (elapsed.as_millis() / 50) % 2 == 0 { Color::Red } else { Color::Magenta };
    queue!(buf, MoveTo(title_x, title_y), SetForegroundColor(title_color), crossterm::style::Print(glitched)).ok();
    queue!(buf, ResetColor).ok();
}

fn draw_earth_ascent(buf: &mut Vec<u8>, width: u16, height: u16, elapsed: Duration, seed: &mut u32) {
    // Fast scrolling patterns simulating upward acceleration through atmosphere
    let ascent_chars = ['_', '~', '#', '^', 'v', '|'];
    
    // Calculate scroll speed (increases over time)
    let progress = elapsed.as_secs_f32() / 5.0; // 5 second duration
    let scroll_speed = (progress * 3.0 + 1.0) as u16; // Speed increases from 1 to 4
    
    for y in 0..height {
        for x in 0..width {
            // Create scrolling pattern
            let pattern_y = (y + scroll_speed * 2) % (height * 2);
            let char_idx = ((x + pattern_y * 3) % ascent_chars.len() as u16) as usize;
            let ch = ascent_chars[char_idx];
            
            // Color alternates between blue and white
            let color = if (x + y + elapsed.as_millis() as u16 / 50) % 2 == 0 { 
                Color::Blue 
            } else { 
                Color::White 
            };
            
            queue!(buf, MoveTo(x, y), SetForegroundColor(color), crossterm::style::Print(ch)).ok();
        }
    }
    queue!(buf, ResetColor).ok();
}

fn draw_stratosphere_horizon(buf: &mut Vec<u8>, width: u16, height: u16, elapsed: Duration, seed: &mut u32) {
    // Single curved horizon line at center with cyan glow
    let center_y = height / 2;
    let center_x = width / 2;
    
    // Draw curved horizon line
    for x in 0..width {
        let y_offset = ((x as f32 - center_x as f32) / (width as f32 / 4.0)).sin() * 2.0;
        let y = (center_y as f32 + y_offset) as u16;
        
        if y < height {
            // Main horizon line
            queue!(buf, MoveTo(x, y), SetForegroundColor(Color::Cyan), crossterm::style::Print("-")).ok();
            
            // Glow effect (slightly above and below)
            if y > 0 {
                queue!(buf, MoveTo(x, y - 1), SetForegroundColor(Color::Cyan), crossterm::style::Print(".")).ok();
            }
            if y < height - 1 {
                queue!(buf, MoveTo(x, y + 1), SetForegroundColor(Color::Cyan), crossterm::style::Print(".")).ok();
            }
        }
    }
    queue!(buf, ResetColor).ok();
}

fn draw_hyperspace_streaks(buf: &mut Vec<u8>, width: u16, height: u16, elapsed: Duration, seed: &mut u32) {
    // Radial white/yellow streaks from center outward
    let center_x = width as f32 / 2.0;
    let center_y = height as f32 / 2.0;
    
    // Calculate streak intensity based on elapsed time
    let progress = elapsed.as_secs_f32() / 4.0; // 4 second duration
    let streak_count = (progress * 50.0 + 20.0) as u32; // 20 to 70 streaks
    
    for _ in 0..streak_count {
        // Random angle from center
        let angle = (rng_next(seed) % 360) as f32 * std::f32::consts::PI / 180.0;
        let length = (rng_next(seed) % 20 + 5) as f32; // 5 to 25 characters
        
        // Streak characters
        let streak_chars = ['-', '|', '*', '/', '\\'];
        let ch = streak_chars[(rng_next(seed) % streak_chars.len() as u32) as usize];
        
        // Color alternates between white and yellow
        let color = if (rng_next(seed) % 2) == 0 { Color::White } else { Color::Yellow };
        
        // Draw streak
        for i in 0..length as u32 {
            let x = (center_x + angle.cos() * i as f32) as u16;
            let y = (center_y + angle.sin() * i as f32) as u16;
            
            if x < width && y < height {
                queue!(buf, MoveTo(x, y), SetForegroundColor(color), crossterm::style::Print(ch)).ok();
            }
        }
    }
    queue!(buf, ResetColor).ok();
}

fn draw_chroma_title_large(buf: &mut Vec<u8>, width: u16, height: u16, elapsed: Duration) {
    // Reuse existing render_big_chroma but make it stable during hyperspace
    render_big_chroma(buf, width, height);
}

fn dissolve_to_main(buf: &mut Vec<u8>, width: u16, height: u16, elapsed: Duration) {
    // Smooth dissolve effect - gradually fade to black
    let progress = elapsed.as_secs_f32() / 1.0; // 1 second duration
    let fade_intensity = (1.0 - progress).clamp(0.0, 1.0);
    
    // Create a fade pattern
    for y in 0..height {
        for x in 0..width {
            // Random fade based on progress
            if rng_next(&mut 0x1234_5678) as f32 / u32::MAX as f32 > fade_intensity {
                queue!(buf, MoveTo(x, y), SetForegroundColor(Color::Black), crossterm::style::Print(" ")).ok();
            }
        }
    }
    queue!(buf, ResetColor).ok();
}

pub fn run_cinematic_startup() -> Result<()> {
    let mut buf: Vec<u8> = Vec::with_capacity(1024 * 64);
    let (width, height) = crossterm::terminal::size()?;
    let mut seed: u32 = 0x1234_5678;

    // Hide cursor during sequence
    queue!(buf, Hide).ok();
    clear_screen(&mut buf);
    flush_buf(&mut buf)?;

    // Stage 1: Pre-Flight Check (2.0s)
    let stage1_start = Instant::now();
    while stage1_start.elapsed() < Duration::from_millis(2000) {
        clear_screen(&mut buf);
        draw_preflight_diagnostics(&mut buf, width, height, stage1_start.elapsed(), &mut seed);
        flush_buf(&mut buf)?;
        std::thread::sleep(Duration::from_millis(33)); // ~30 FPS
    }

    // Stage 2: System Ignition (2.0s)
    let stage2_start = Instant::now();
    while stage2_start.elapsed() < Duration::from_millis(2000) {
        clear_screen(&mut buf);
        draw_ignition_sequence(&mut buf, width, height, stage2_start.elapsed(), &mut seed);
        flush_buf(&mut buf)?;
        std::thread::sleep(Duration::from_millis(33)); // ~30 FPS
    }

    // Stage 3: Earth Ascent (5.0s)
    let stage3_start = Instant::now();
    while stage3_start.elapsed() < Duration::from_millis(5000) {
        clear_screen(&mut buf);
        draw_earth_ascent(&mut buf, width, height, stage3_start.elapsed(), &mut seed);
        flush_buf(&mut buf)?;
        std::thread::sleep(Duration::from_millis(33)); // ~30 FPS
    }

    // Stage 4: Stratosphere Break (2.0s)
    let stage4_start = Instant::now();
    while stage4_start.elapsed() < Duration::from_millis(2000) {
        clear_screen(&mut buf);
        draw_stratosphere_horizon(&mut buf, width, height, stage4_start.elapsed(), &mut seed);
        flush_buf(&mut buf)?;
        std::thread::sleep(Duration::from_millis(33)); // ~30 FPS
    }

    // Stage 5: Hyperspace Jump / CHROMA Reveal (4.0s)
    let stage5_start = Instant::now();
    while stage5_start.elapsed() < Duration::from_millis(4000) {
        clear_screen(&mut buf);
        draw_hyperspace_streaks(&mut buf, width, height, stage5_start.elapsed(), &mut seed);
        draw_chroma_title_large(&mut buf, width, height, stage5_start.elapsed());
        flush_buf(&mut buf)?;
        std::thread::sleep(Duration::from_millis(33)); // ~30 FPS
    }

    // Stage 6: Transition to MPS (1.0s)
    let stage6_start = Instant::now();
    while stage6_start.elapsed() < Duration::from_millis(1000) {
        clear_screen(&mut buf);
        draw_hyperspace_streaks(&mut buf, width, height, stage5_start.elapsed(), &mut seed);
        draw_chroma_title_large(&mut buf, width, height, stage5_start.elapsed());
        dissolve_to_main(&mut buf, width, height, stage6_start.elapsed());
        flush_buf(&mut buf)?;
        std::thread::sleep(Duration::from_millis(33)); // ~30 FPS
    }

    // Final cleanup - ensure black screen
    clear_screen(&mut buf);
    flush_buf(&mut buf)?;

    // Restore cursor
    queue!(buf, Show, ResetColor, Clear(ClearType::All), MoveTo(0, 0)).ok();
    flush_buf(&mut buf)?;

    Ok(())
}