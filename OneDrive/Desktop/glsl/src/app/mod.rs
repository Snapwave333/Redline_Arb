mod audio;
mod config_watcher;
mod input;
mod rendering;
mod status_bar;
mod vj_integration;
mod autonomous_app;
mod chroma_app;
mod futuristic_status_bar;
mod startup;
mod styling_constants;

pub use autonomous_app::AutonomousApp;
pub use chroma_app::ChromaApp;

#[cfg(feature = "audio")]
use crate::constants::AUDIO_SAMPLE_THRESHOLD;
use crate::constants::FRAME_DURATION;
use anyhow::Result;
use chroma::ascii::{AsciiConverter, AsciiPalette};
#[cfg(feature = "audio")]
use chroma::audio::{AudioAnalyzer, AudioCapture};
use chroma::params::{PaletteType, ShaderParams};
use chroma::shader::{ShaderPipeline, ShaderUniforms};
use crossterm::terminal;
use std::fs::File;
use std::io::{BufWriter, Write};
use std::time::Instant;
use sysinfo::{System, SystemExt};

#[cfg(debug_assertions)]
pub(crate) type DebugLog = BufWriter<File>;

#[cfg(not(debug_assertions))]
pub(crate) type DebugLog = BufWriter<std::io::Sink>;

/// Main application state
pub struct App {
  params: ShaderParams,
  pipeline: ShaderPipeline,
  converter: AsciiConverter,
  running: bool,
  show_status_bar: bool,
  last_frame_time: Instant,
  debug_log: DebugLog,
  last_terminal_size: (u16, u16),
  config_watcher: Option<config_watcher::ConfigWatcher>,
  custom_shader: Option<String>,
  frame_limiter: Option<u32>, // FPS limit (None = unlimited)
  exit_confirmation: bool, // Whether to prompt before exiting
  #[cfg(feature = "audio")]
  audio_capture: Option<AudioCapture>,
  #[cfg(feature = "audio")]
  audio_analyzer: Option<AudioAnalyzer>,
  // Futuristic status bar and metrics helpers
  futuristic_status_bar: futuristic_status_bar::FuturisticStatusBar,
  fps_smooth: f32,
  system: System,
  #[cfg(feature = "audio")]
  last_beat_strength: f32,
}

impl App {
  /// Create a new application instance
  pub async fn new(
    loaded_config: Option<ShaderParams>,
    show_status_bar: bool,
    hud_style: String,
    config_path: Option<String>,
    #[cfg(feature = "audio")] audio_device: Option<String>,
    custom_shader: Option<String>,
    frame_limiter: Option<u32>,
    exit_confirmation: bool,
  ) -> Result<Self> {
    #[cfg(debug_assertions)]
    let mut debug_log = {
      let debug_file = File::create("debug.log")?;
      BufWriter::new(debug_file)
    };

    #[cfg(not(debug_assertions))]
    let mut debug_log = BufWriter::new(std::io::sink());

    let (terminal_width, terminal_height) = terminal::size()?;

    writeln!(
      debug_log,
      "DEBUG: Terminal size: {}x{}",
      terminal_width, terminal_height
    )?;

    let shader_width = terminal_width as u32;

    let shader_height = if show_status_bar {
      (terminal_height - 1) as u32
    } else {
      terminal_height as u32
    };

    writeln!(
      debug_log,
      "DEBUG: Shader size: {}x{}",
      shader_width, shader_height
    )?;

    let mut params = loaded_config.unwrap_or_else(|| {
      #[cfg(feature = "audio")]
      {
        ShaderParams::with_audio_reactive_defaults()
      }
      #[cfg(not(feature = "audio"))]
      {
        ShaderParams::default()
      }
    });

    params.set_resolution(shader_width, shader_height);

    if custom_shader.is_some() {
      writeln!(
        debug_log,
        "DEBUG: Using custom shader (overrides pattern selection)"
      )?;
    }

    let pipeline = ShaderPipeline::new(
      shader_width,
      shader_height,
      custom_shader.clone(),
      &mut debug_log,
    )
    .await?;

    let palette = Self::palette_from_type(params.palette);
    let converter = AsciiConverter::new(palette, true);

    #[cfg(feature = "audio")]
    let (audio_capture, audio_analyzer) =
      Self::init_audio(&mut debug_log, audio_device.as_deref())?;

    let config_watcher = Self::init_config_watcher(&config_path, &mut debug_log)?;

    // Initialize system info and futuristic status bar
    let mut system = System::new_all();
    system.refresh_memory();

    let hud_style_enum = match hud_style.to_lowercase().as_str() {
      "segmentedneon" | "segmented_neon" | "neon" => futuristic_status_bar::HudStyle::SegmentedNeon,
      "odometer" => futuristic_status_bar::HudStyle::Odometer,
      _ => futuristic_status_bar::HudStyle::SegmentedNeon,
    };
    let futuristic_status_bar = futuristic_status_bar::FuturisticStatusBar::new_with_style(hud_style_enum, show_status_bar);

    Ok(Self {
      params,
      pipeline,
      converter,
      running: true,
      show_status_bar,
      last_frame_time: Instant::now(),
      debug_log,
      last_terminal_size: (terminal_width, terminal_height),
      config_watcher,
      custom_shader,
      frame_limiter,
      exit_confirmation,
      #[cfg(feature = "audio")]
      audio_capture,
      #[cfg(feature = "audio")]
      audio_analyzer,
      futuristic_status_bar,
      fps_smooth: 0.0,
      system,
      #[cfg(feature = "audio")]
      last_beat_strength: 0.0,
    })
  }

  /// Initialize audio capture and analyzer
  #[cfg(feature = "audio")]
  fn init_audio(
    debug_log: &mut DebugLog,
    device_name: Option<&str>,
  ) -> Result<(Option<AudioCapture>, Option<AudioAnalyzer>)> {
    match AudioCapture::new(device_name) {
      Ok(capture) => {
        writeln!(
          debug_log,
          "Audio capture initialized successfully at {} Hz",
          capture.sample_rate
        )?;
        let analyzer = AudioAnalyzer::new(capture.sample_rate);
        Ok((Some(capture), Some(analyzer)))
      }
      Err(e) => {
        writeln!(debug_log, "Failed to initialize audio: {}", e)?;
        Ok((None, None))
      }
    }
  }

  /// Initialize config file watcher if config path is provided
  fn init_config_watcher(
    config_path: &Option<String>,
    debug_log: &mut DebugLog,
  ) -> Result<Option<config_watcher::ConfigWatcher>> {
    if let Some(path) = config_path {
      match config_watcher::ConfigWatcher::new(path) {
        Ok(watcher) => {
          writeln!(debug_log, "Config file watcher initialized for: {}", path)?;
          Ok(Some(watcher))
        }
        Err(e) => {
          writeln!(debug_log, "Failed to initialize config watcher: {}", e)?;
          Ok(None)
        }
      }
    } else {
      Ok(None)
    }
  }

  /// Convert palette type to ASCII palette
  fn palette_from_type(palette_type: PaletteType) -> AsciiPalette {
    match palette_type {
      PaletteType::Standard => AsciiPalette::standard(),
      PaletteType::Blocks => AsciiPalette::blocks(),
      PaletteType::Circles => AsciiPalette::circles(),
      PaletteType::Smooth => AsciiPalette::smooth(),
      PaletteType::Braille => AsciiPalette::braille(),
      PaletteType::Geometric => AsciiPalette::geometric(),
      PaletteType::Mixed => AsciiPalette::mixed(),
      PaletteType::Dots => AsciiPalette::dots(),
      PaletteType::Shades => AsciiPalette::shades(),
      PaletteType::Lines => AsciiPalette::lines(),
      PaletteType::Triangles => AsciiPalette::triangles(),
      PaletteType::Arrows => AsciiPalette::arrows(),
      PaletteType::Powerline => AsciiPalette::powerline(),
      PaletteType::BoxDraw => AsciiPalette::boxdraw(),
      PaletteType::Extended => AsciiPalette::extended(),
      PaletteType::Simple => AsciiPalette::simple(),
    }
  }

  /// Check for config file changes and apply them if valid
  fn check_and_apply_config_reload(&mut self) {
    if let Some(ref watcher) = self.config_watcher {
      if let Some(mut new_params) = watcher.try_receive_config() {
        let current_time = self.params.time;
        let current_width = self.params.resolution_width;
        let current_height = self.params.resolution_height;

        new_params.time = current_time;
        new_params.set_resolution(current_width, current_height);

        if new_params.palette != self.params.palette {
          let new_palette = Self::palette_from_type(new_params.palette);
          self.converter = AsciiConverter::new(new_palette, true);
        }

        self.params = new_params;

        let _ = writeln!(self.debug_log, "Config reloaded successfully");
      }
    }
  }

  /// Update application state
  fn update(&mut self) {
    let current_time = Instant::now();
    let delta_time = current_time
      .duration_since(self.last_frame_time)
      .as_secs_f32();

    self.params.update_time(delta_time);

    #[cfg(feature = "audio")]
    {
      let beat_opt = audio::update_audio_reactive(
        &mut self.params,
        &self.audio_capture,
        &mut self.audio_analyzer,
        delta_time,
        &mut self.debug_log,
      );
      if let Some(bs) = beat_opt { self.last_beat_strength = bs; }
    }

    self.check_and_apply_config_reload();

    self.last_frame_time = current_time;
  }

  /// Render current frame
  fn render(&mut self) -> Result<()> {
    let uniforms = ShaderUniforms::from_params(&self.params);

    writeln!(
      self.debug_log,
      "DEBUG: Uniforms - time: {}, freq: {}, amp: {}, scale: {}",
      self.params.time, self.params.frequency, self.params.amplitude, self.params.scale
    )?;
    writeln!(
      self.debug_log,
      "DEBUG: Resolution in uniforms: {}x{}",
      self.params.resolution_width, self.params.resolution_height
    )?;

    let has_sound = self.check_audio_activity();

    let status_bar = if self.show_status_bar {
      Some(self.build_status_bar(has_sound))
    } else {
      None
    };

    // Convert terminal background color from normalized floats to u8
    let terminal_bg = if self.params.terminal_bg_r > 0.0
      || self.params.terminal_bg_g > 0.0
      || self.params.terminal_bg_b > 0.0
    {
      Some((
        (self.params.terminal_bg_r * 255.0) as u8,
        (self.params.terminal_bg_g * 255.0) as u8,
        (self.params.terminal_bg_b * 255.0) as u8,
      ))
    } else {
      None
    };

    rendering::render_frame(
      &self.pipeline,
      &self.converter,
      &uniforms,
      status_bar,
      terminal_bg,
      &mut self.debug_log,
    )?;

    self.debug_log.flush()?;
    Ok(())
  }

  /// Check if audio is currently active
  fn check_audio_activity(&self) -> bool {
    #[cfg(feature = "audio")]
    {
      if self.params.audio_enabled {
        if let (Some(capture), Some(_)) = (&self.audio_capture, &self.audio_analyzer) {
          let samples = capture.get_samples();
          return !samples.is_empty() && samples.iter().any(|s| s.abs() > AUDIO_SAMPLE_THRESHOLD);
        }
      }
    }
    false
  }

  /// Build status bar string
  fn build_status_bar(&mut self, _has_sound: bool) -> String {
    let (_current_width, _) = terminal::size().unwrap_or((80, 24));
    match self.futuristic_status_bar.render() {
      Ok(s) => s,
      Err(_) => String::new(),
    }
  }

  /// Handle window resize
  async fn handle_resize(&mut self, new_width: u16, new_height: u16) -> Result<()> {
    writeln!(
      self.debug_log,
      "RESIZE: Terminal resized to {}x{} (was {}x{})",
      new_width, new_height, self.last_terminal_size.0, self.last_terminal_size.1
    )?;

    let shader_width = new_width as u32;
    let shader_height = if self.show_status_bar {
      (new_height - 1) as u32
    } else {
      new_height as u32
    };

    self.params.set_resolution(shader_width, shader_height);

    self.pipeline = ShaderPipeline::new(
      shader_width,
      shader_height,
      self.custom_shader.clone(),
      &mut self.debug_log,
    )
    .await?;

    self.last_terminal_size = (new_width, new_height);

    writeln!(
      self.debug_log,
      "RESIZE: Pipeline recreated with dimensions {}x{}",
      shader_width, shader_height
    )?;

    Ok(())
  }

  /// Set the frame rate limit
  #[allow(dead_code)]
   pub fn set_frame_limiter(&mut self, fps_limit: Option<u32>) {
     self.frame_limiter = fps_limit;
   }

   /// Get the current frame rate limit
  #[allow(dead_code)]
   pub fn get_frame_limiter(&self) -> Option<u32> {
     self.frame_limiter
   }

  /// Main application loop
  pub fn run(&mut self) -> Result<()> {
    // Run the cinematic startup sequence before entering the main loop
    // This ignores audio input and focuses purely on timed visual effects
    if let Err(e) = startup::run_cinematic_startup() { eprintln!("Startup sequence error: {}", e); }
    while self.running {
      let frame_start = Instant::now();

      // Apply frame limiting if enabled
      if let Some(fps_limit) = self.frame_limiter {
        let target_frame_duration = std::time::Duration::from_secs_f32(1.0 / fps_limit as f32);
        let elapsed = frame_start.duration_since(self.last_frame_time);
        if elapsed < target_frame_duration {
          std::thread::sleep(target_frame_duration - elapsed);
        }
      }

      // Check for window resize
      let (current_width, current_height) = terminal::size()?;
      if (current_width, current_height) != self.last_terminal_size {
        pollster::block_on(async { self.handle_resize(current_width, current_height).await })?;
      }

      // Handle input, update state, and render
      input::handle_input(
        &mut self.params,
        &mut self.converter,
        &mut self.running,
        &mut self.debug_log,
        self.exit_confirmation,
        &mut self.show_status_bar,
      )?;

      // Keep futuristic bar visibility in sync with global toggle
      // (Rendering path already checks self.show_status_bar)
      // Update app state and render
      self.update();

      // BPM synchronization from audio analyzer via beat_distortion_time
      let beat_detected = (self.params.time - self.params.beat_distortion_time).abs() < 0.05;
      if beat_detected {
        self.futuristic_status_bar.update_beat(true);
      }
      #[cfg(feature = "audio")]
      {
        self.futuristic_status_bar.update_beat_strength(self.last_beat_strength);
      }

      self.render()?;

      // Frame rate limiting
      let frame_time = frame_start.elapsed();

      // Update metrics for futuristic status bar (decoupled rendering uses cached string)
      let fps_current = if frame_time.as_secs_f32() > 0.0 { 1.0 / frame_time.as_secs_f32() } else { 0.0 };
      self.fps_smooth = if self.fps_smooth == 0.0 {
        fps_current
      } else {
        self.fps_smooth * 0.85 + fps_current * 0.15
      };

      // Prefer real GPU metrics if available; otherwise, simulate based on frame time relative to the configured FPS limit
      let target_frame_duration = if let Some(limit) = self.frame_limiter { 1.0 / (limit as f32) } else { 1.0 / 60.0 };
      let gpu_load = if let Some(real_gpu) = crate::system::gpu::try_get_gpu_load() {
        real_gpu.clamp(0.0, 100.0)
      } else {
        let ratio = (frame_time.as_secs_f32() / target_frame_duration).max(0.0);
        // Map ratio=1.0 (meeting target FPS) -> ~50% load, slower -> approach 100%
        (50.0 + 50.0 * (ratio - 1.0).clamp(0.0, 1.0)).clamp(0.0, 100.0)
      };

      // VRAM usage (MiB) via system::gpu integrations if available
      let (vram_used_mb, vram_total_mb) = if let Some((used_mb, total_mb)) = crate::system::gpu::try_get_vram_usage_mb() {
        (used_mb, total_mb)
      } else {
        (0.0, 0.0)
      };
     
       // BPM value is driven by beat sync inside the status bar; keep placeholder
       let bpm = 0.0;

      self.futuristic_status_bar.update_metrics(self.fps_smooth, gpu_load, vram_used_mb, vram_total_mb, bpm);

      if frame_time < FRAME_DURATION {
        std::thread::sleep(FRAME_DURATION - frame_time);
      }
    }

    Ok(())
  }
}
