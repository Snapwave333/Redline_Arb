use anyhow::Result;
use crossterm::terminal;
use std::time::{Duration, Instant};

use super::styling_constants::StylingConstants;

/// HUD style variants
#[derive(Clone, Copy)]
pub enum HudStyle {
    SegmentedNeon,
    Odometer,
}

/// Futuristic Cyberpunk-Tron Status Bar with segmented odometer displays
/// Implements a beautiful, high-contrast diagnostic dashboard
pub struct FuturisticStatusBar {
    // Display state
    visible: bool,
    style: HudStyle,
    last_update: Instant,
    update_interval: Duration,
    cached_line: String,

    // Metrics
    fps: f32,
    gpu_load: f32,
    vram_usage_mb: f32,
    vram_total_mb: f32,
    bpm: f32,

    // Smoothing state
    smoothed_gpu_load: f32,
    smoothed_vram_usage_mb: f32,
    smoothing_alpha_gpu: f32,
    smoothing_alpha_vram: f32,

    // Animation state
    scanline_phase: f32,
    pulse_intensity: f32,
    last_beat_time: Instant,
}

impl FuturisticStatusBar {
    /// Create a new futuristic status bar (default SegmentedNeon, visible)
    pub fn new() -> Self {
        Self::new_with_style(HudStyle::SegmentedNeon, true)
    }

    /// Create a futuristic status bar with a specific style and visibility
    pub fn new_with_style(style: HudStyle, visible: bool) -> Self {
        Self {
            visible,
            style,
            last_update: Instant::now(),
            update_interval: Duration::from_millis(150), // decoupled update
            cached_line: String::new(),

            fps: 0.0,
            gpu_load: 0.0,
            vram_usage_mb: 0.0,
            vram_total_mb: 0.0,
            bpm: 0.0,

            // Smoothing
            smoothed_gpu_load: 0.0,
            smoothed_vram_usage_mb: 0.0,
            smoothing_alpha_gpu: 0.25, // higher alpha -> more reactive
            smoothing_alpha_vram: 0.20,

            scanline_phase: 0.0,
            pulse_intensity: 0.0,
            last_beat_time: Instant::now(),
        }
    }

    /// Toggle visibility of the status bar
    pub fn toggle_visibility(&mut self) {
        self.visible = !self.visible;
    }

    /// Check if the status bar is visible
    pub fn is_visible(&self) -> bool {
        self.visible
    }

    /// Update metrics (called by App with latest values)
    pub fn update_metrics(&mut self, fps: f32, gpu_load: f32, vram_usage_mb: f32, vram_total_mb: f32, bpm: f32) {
        self.fps = fps;
        self.gpu_load = gpu_load;
        self.vram_usage_mb = vram_usage_mb;
        self.vram_total_mb = vram_total_mb.max(0.0);
        if bpm > 0.0 {
            self.bpm = bpm;
        }

        // Apply smoothing (EMA)
        let a_g = self.smoothing_alpha_gpu.clamp(0.0, 1.0);
        self.smoothed_gpu_load = (self.smoothed_gpu_load * (1.0 - a_g)) + (self.gpu_load * a_g);
        self.smoothed_gpu_load = self.smoothed_gpu_load.clamp(0.0, 100.0);

        let a_v = self.smoothing_alpha_vram.clamp(0.0, 1.0);
        self.smoothed_vram_usage_mb = (self.smoothed_vram_usage_mb * (1.0 - a_v)) + (self.vram_usage_mb * a_v);
        self.smoothed_vram_usage_mb = self.smoothed_vram_usage_mb.max(0.0);

        // Decay pulse intensity
        self.pulse_intensity *= 0.88;

        // Update scanline animation
        self.scanline_phase = (self.scanline_phase + 0.15) % std::f32::consts::TAU;
    }

    /// Explicitly update beat state from audio analyzer
    /// When a beat is detected, trigger an immediate pulse and reset beat timing.
    pub fn update_beat(&mut self, beat_detected: bool) {
        if beat_detected {
            let now = Instant::now();
            let dt = now.duration_since(self.last_beat_time).as_secs_f32();
            if dt > 0.2 && dt < 2.0 {
                let bpm_est = 60.0 / dt;
                // Smooth the displayed BPM toward the estimate
                self.bpm = if self.bpm == 0.0 { bpm_est } else { self.bpm * 0.9 + bpm_est * 0.1 };
            }
            self.last_beat_time = now;
            self.pulse_intensity = 1.0;
        }
    }

    /// Continuous beat strength update to modulate pulse intensity each frame
    /// This uses the analyzer's beat_strength in [0,1] to brighten the BPM segment subtly.
    pub fn update_beat_strength(&mut self, beat_strength: f32) {
        let s = beat_strength.clamp(0.0, 1.0);
        // Blend current pulse with incoming strength, then clamp.
        self.pulse_intensity = ((self.pulse_intensity * 0.85) + (s * 0.6)).clamp(0.0, 1.0);
    }

    /// Render the futuristic status bar as a single row
    /// Uses ANSI color escapes and box-drawing characters to create a segmented odometer look
    pub fn render(&mut self) -> Result<String> {
        if !self.visible {
            return Ok(String::new());
        }

        // Only rebuild the line when the update interval elapses; otherwise return cached
        if self.last_update.elapsed() < self.update_interval {
            return Ok(self.cached_line.clone());
        }
        self.last_update = Instant::now();

        match self.style {
            HudStyle::SegmentedNeon => self.render_segmented_neon(),
            HudStyle::Odometer => self.render_segmented_neon(), // TODO: alternate style
        }
    }

    fn render_segmented_neon(&mut self) -> Result<String> {
        // Helper to apply ANSI foreground/background colors
        let set_fg = StylingConstants::fg;
        let set_bg = StylingConstants::bg;
        let reset = StylingConstants::reset();

        // Color palette for Segmented Neon style
        let neon_pink = StylingConstants::NEON_PINK; // Vibrant Neon Pink/Purple
        let electric_blue = StylingConstants::ELECTRIC_BLUE; // Electric Blue
        let bright_orange = StylingConstants::BRIGHT_ORANGE; // Bright Orange
        let alert_red = StylingConstants::ALERT_RED; // Bright Red for critical GPU
        let lime_green = StylingConstants::LIME_GREEN; // Lime Green
        let white = StylingConstants::WHITE;
        let near_black = StylingConstants::NEAR_BLACK;

        // Pulse intensity for BPM digits (0..1), brighten towards white on beat
        let pulse = self.pulse_intensity.clamp(0.0, 1.0);
        let bpm_fg = (
            (neon_pink.0 as f32 * (1.0 - 0.5 * pulse) + white.0 as f32 * (0.5 * pulse)) as u8,
            (neon_pink.1 as f32 * (1.0 - 0.5 * pulse) + white.1 as f32 * (0.5 * pulse)) as u8,
            (neon_pink.2 as f32 * (1.0 - 0.5 * pulse) + white.2 as f32 * (0.5 * pulse)) as u8,
        );

        // Values formatted
        let fps_val = format!("{:03}", self.fps.round() as u32);
        let gpu_val_num = self.smoothed_gpu_load.round() as u32;
        let gpu_val = format!("{:03}%", gpu_val_num);
        let used_str = if self.smoothed_vram_usage_mb >= 1024.0 { format!("{:.1}G", self.smoothed_vram_usage_mb / 1024.0) } else { format!("{:.1}M", self.smoothed_vram_usage_mb) };
        let nvml_tag = if self.vram_total_mb > 0.0 { "" } else { " (NVML N/A)" };
        let ram_val = if self.vram_total_mb > 0.0 {
            let total_str = if self.vram_total_mb >= 1024.0 { format!("{:.1}G", self.vram_total_mb / 1024.0) } else { format!("{:.0}M", self.vram_total_mb) };
            format!("{}/{}", used_str, total_str)
        } else {
            format!("{}{}", used_str, nvml_tag)
        };

        let bpm_val = format!("{:03}", self.bpm.round() as u32);

        // GPU critical flashing when >= 90%
        let gpu_critical = gpu_val_num >= 90;
        let flashing = self.scanline_phase.sin() > 0.0; // simple on/off
        let gpu_bg = if gpu_critical && flashing { alert_red } else { bright_orange };
        let gpu_fg = if gpu_critical { white } else { near_black };

        // Adaptive segment builder
        let mut blocks_left = [3usize, 2, 2, 2];
        let mut blocks_right = [3usize, 2, 2, 2];
        let mut pad_spaces = [2usize, 2, 2, 2];

        let segment_texts = [
            format!("{} BPM", bpm_val),
            format!("FPS {}", fps_val),
            format!("{} GPU", gpu_val),
            format!("{} VRAM", ram_val),
        ];
        let segment_fgs = [bpm_fg, white, gpu_fg, near_black];
        let segment_bgs = [neon_pink, electric_blue, gpu_bg, lime_green];

        // Strong vertical separators
        let sep = format!(" {}{}{} ", set_fg(white), StylingConstants::PIPE_SEP, reset);

        // Segment builder closure using current padding
        let build_segment = |bg: (u8,u8,u8), fg: (u8,u8,u8), inner: &str, left_blocks: usize, right_blocks: usize, space_pad: usize| -> String {
            let mut s = String::new();
            s.push_str(&set_bg(bg));
            s.push_str(&set_fg(fg));
            s.push('[');
            for _ in 0..left_blocks { s.push(StylingConstants::FULL_BLOCK); }
            for _ in 0..space_pad { s.push(' '); }
            s.push_str(inner);
            for _ in 0..space_pad { s.push(' '); }
            for _ in 0..right_blocks { s.push(StylingConstants::FULL_BLOCK); }
            s.push(']');
            s.push_str(reset);
            s
        };

        // Build initial line
        let mut segments: Vec<String> = (0..4)
            .map(|i| build_segment(segment_bgs[i], segment_fgs[i], &segment_texts[i], blocks_left[i], blocks_right[i], pad_spaces[i]))
            .collect();
        let mut line = format!("{}{}{}{}{}{}{}", segments[0], sep, segments[1], sep, segments[2], sep, segments[3]);

        // Helper: strip ANSI sequences to measure visible width
        fn strip_ansi(s: &str) -> String {
            let mut out = String::with_capacity(s.len());
            let mut chars = s.chars().peekable();
            while let Some(c) = chars.next() {
                if c == '\u{1b}' {
                    // Skip until 'm'
                    while let Some(nc) = chars.next() {
                        if nc == 'm' { break; }
                    }
                } else {
                    out.push(c);
                }
            }
            out
        }

        let (term_cols, _) = terminal::size().unwrap_or((80, 24));
        let mut visible_len = strip_ansi(&line).chars().count();
        let target = term_cols as usize;

        // Reduce blocks/padding until it fits; then if still too long, fall back to compact style
        let mut changed = true;
        while visible_len > target && changed {
            changed = false;
            // Reduce blocks uniformly
            for i in 0..4 {
                if blocks_left[i] > 0 { blocks_left[i] -= 1; changed = true; }
                if blocks_right[i] > 0 { blocks_right[i] -= 1; changed = true; }
            }
            // Rebuild
            segments = (0..4)
                .map(|i| build_segment(segment_bgs[i], segment_fgs[i], &segment_texts[i], blocks_left[i], blocks_right[i], pad_spaces[i]))
                .collect();
            line = format!("{}{}{}{}{}{}{}", segments[0], sep, segments[1], sep, segments[2], sep, segments[3]);
            visible_len = strip_ansi(&line).chars().count();

            // If still too long, reduce padding spaces
            if visible_len > target {
                for i in 0..4 { if pad_spaces[i] > 0 { pad_spaces[i] -= 1; changed = true; } }
                segments = (0..4)
                    .map(|i| build_segment(segment_bgs[i], segment_fgs[i], &segment_texts[i], blocks_left[i], blocks_right[i], pad_spaces[i]))
                    .collect();
                line = format!("{}{}{}{}{}{}{}", segments[0], sep, segments[1], sep, segments[2], sep, segments[3]);
                visible_len = strip_ansi(&line).chars().count();
            }
        }

        // Final fallback: compact text-only if still too wide
        if visible_len > target {
            let bpm = format!("{}{} BPM{}", set_fg(bpm_fg), bpm_val, reset);
            let fps = format!("{}FPS {}{}", set_fg(white), fps_val, reset);
            let gpu = format!("{}{} GPU{}", set_fg(gpu_fg), gpu_val, reset);
            let ram = format!("{}{} RAM{}", set_fg(near_black), ram_val, reset);
            // Add minimal separators
            let compact = format!("{} {} {} {} {}", bpm, sep, fps, sep, gpu)
                + &format!("{}{}{}", sep, ram, reset);
            line = compact;
        }

        self.cached_line = line.clone();
        Ok(line)
    }

    /// Render a single-line segmented pod: ╒─[::LABEL::]─│ VALUE │─╛
    #[allow(dead_code)]
    fn render_pod(
        &self,
        label: &str,
        value: &str,
        value_rgb: (u8, u8, u8),
        frame_color: &dyn Fn(&str) -> String,
        digit_color: &dyn Fn((u8, u8, u8), &str) -> String,
    ) -> String {
        let label_str = format!("[::{}::]", label);
        let left = frame_color("╒─");
        let mid = frame_color("─│ ");
        let right = frame_color(" │─╛");
        let value_colored = digit_color(value_rgb, value);
        let label_colored = frame_color(&label_str); // keep label as part of frame color
        format!("{}{}{}{}{}", left, label_colored, mid, value_colored, right)
    }

    /// Convenience: provide system-like metrics when caller doesn't track them
    /// Returns (gpu_load_percent, vram_used_mb, vram_total_mb, bpm)
    pub fn get_system_metrics(&self) -> (f32, f32, f32, f32) {
        // Simulate GPU load from scanline_phase animation if not provided externally
        let gpu_load = ((self.scanline_phase.sin() * 0.5) + 0.5) * 100.0;
        let vram_used_mb = self.vram_usage_mb; // Caller may have updated this; defaults to 0
        let vram_total_mb = self.vram_total_mb;
        let bpm = self.bpm; // If driven externally it will be non-zero
        (gpu_load, vram_used_mb, vram_total_mb, bpm)
    }
}



