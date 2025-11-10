use anyhow::Result;
use chroma::vj::{AutonomousStartup, StartupPhase, OrchestratorIntegration, EffectTrigger, OrchestratorIntegrationResult, ActiveEffectState, PendingTransition, IntegrationMetrics};
use chroma::params::{ShaderParams, PatternType, PaletteType, ColorMode};
use chroma::shader::{ShaderPipeline, ShaderUniforms};
use chroma::ascii::{AsciiConverter, AsciiPalette};
use std::time::{Instant, Duration};
use std::io::{BufWriter, Write};
use crate::app::{DebugLog};
use crate::app::rendering;
use crate::app::futuristic_status_bar::FuturisticStatusBar;
use crossterm::terminal;
use crossterm::event::{self, Event, KeyCode};

/// Autonomous App - The main autonomous VJ application
/// 
/// This replaces the manual App when running in autonomous mode.
/// It handles the startup sequence and then runs the autonomous VJ.
pub struct AutonomousApp {
    // Core components
    startup: AutonomousStartup,
    orchestrator: OrchestratorIntegration,
    
    // Current state
    params: ShaderParams,
    pattern: PatternType,
    palette: PaletteType,
    color_mode: ColorMode,
    
    // Startup state
    in_startup: bool,
    startup_start_time: Instant,
    last_phase: Option<StartupPhase>,
    
    // Performance tracking
#[allow(dead_code)]
    frame_count: u64,
#[allow(dead_code)]
    last_fps_update: Instant,
    current_fps: f32,
    
    // REAL RENDERING COMPONENTS
    pipeline: ShaderPipeline,
    converter: AsciiConverter,
    debug_log: DebugLog,
    
    // Futuristic status bar
    futuristic_status_bar: FuturisticStatusBar,

    // Beat detection state for status bar pulse
    beat_detected: bool,

    // Terminal flash on extreme beats
    terminal_flash_until: Option<Instant>,

    // Stinger overlay timing
    stinger_until: Option<Instant>,

    // Auto-DJ timing (throttle auto effect triggers and major changes)
    last_effect_trigger: Instant,
    last_auto_change: Instant,
}

impl AutonomousApp {
    /// Create a new autonomous app
    pub async fn new(sample_rate: f32, start_pattern: Option<PatternType>) -> Result<Self> {
        // Initialize rendering components
        let (width, height) = terminal::size().unwrap_or((80, 24));

        #[cfg(debug_assertions)]
        let mut debug_log = BufWriter::new(
          std::fs::File::create("debug.log")
            .unwrap_or_else(|_| std::fs::File::create("/tmp/chroma_debug.log").unwrap()),
        );

        #[cfg(not(debug_assertions))]
        let mut debug_log = BufWriter::new(std::io::sink());

        let pipeline = ShaderPipeline::new(width as u32, height as u32, None, &mut debug_log).await?;
        let converter = AsciiConverter::new(AsciiPalette::standard(), true);

        let initial_pattern = start_pattern.unwrap_or(PatternType::Plasma);

        Ok(Self {
            startup: AutonomousStartup::new(sample_rate),
            orchestrator: OrchestratorIntegration::new(sample_rate),
            
            params: ShaderParams::default(),
            pattern: initial_pattern,
            palette: PaletteType::Standard,
            color_mode: ColorMode::Rainbow,
            
            in_startup: true,
            startup_start_time: Instant::now(),
            last_phase: None,
            
            frame_count: 0,
            last_fps_update: Instant::now(),
            current_fps: 60.0,
            
            // REAL RENDERING COMPONENTS
            pipeline,
            converter,
            debug_log,
            futuristic_status_bar: FuturisticStatusBar::new(),

            // Beat detection state
            beat_detected: false,

            // Terminal flash
            terminal_flash_until: None,

            // Stinger overlay
            stinger_until: None,

            // Auto-DJ timing
            last_effect_trigger: Instant::now(),
            last_auto_change: Instant::now(),
        })
    }
    
    /// Run the autonomous VJ application
    pub fn run(&mut self) -> Result<()> {
        println!("🎵 Chroma Autonomous VJ v0.2.0");
        println!("🚀 Starting autonomous visual performance...");
        
        // Run the 16-second cinematic startup sequence
        if let Err(e) = crate::app::startup::run_cinematic_startup() { 
            eprintln!("Startup sequence error: {}", e); 
        }
        
        // OPTIMIZED Main loop - Target 240 FPS
        let mut running = true;
        let mut frame_count = 0u64;
        let mut last_fps_update = Instant::now();
        
        // Pre-allocate audio buffer for performance
        let mut audio_buffer = vec![0.0f32; 128]; // Minimal buffer for speed
        
        while running {
            let frame_start = Instant::now();
            
            // OPTIMIZED: Only update audio every 4 frames (60Hz audio for 240Hz video)
            if frame_count % 4 == 0 {
                if self.in_startup {
                    self.update_startup_optimized(&mut audio_buffer)?;
                    
                    if self.startup.is_startup_complete() {
                        self.in_startup = false;
                        println!("🎭 Autonomous VJ is now fully operational!");
                    }
                } else {
                    self.update_autonomous_vj_optimized(&mut audio_buffer)?;
                }
            }
            
            // OPTIMIZED: Update FPS counter every 240 frames (1 second at 240 FPS)
            if frame_count % 240 == 0 {
                let elapsed = last_fps_update.elapsed();
                let fps = 240.0 / elapsed.as_secs_f32();
                println!("🚀 FPS: {:.1}", fps);
                self.current_fps = fps;
                last_fps_update = Instant::now();
            }
            
            // OPTIMIZED: Render frame with minimal overhead
            self.render_frame_optimized()?;
            
            // OPTIMIZED: Handle input only every 16 frames (15Hz input for 240Hz video)
            if frame_count % 16 == 0 {
                self.handle_input(&mut running)?;
            }
            
            frame_count += 1;
            
            // OPTIMIZED: Target 240 FPS (4.17ms per frame)
            let frame_duration = frame_start.elapsed();
            if frame_duration < std::time::Duration::from_micros(4167) {
                std::thread::sleep(std::time::Duration::from_micros(4167) - frame_duration);
            }
        }
        
        Ok(())
    }

    /// OPTIMIZED: Minimal-overhead frame rendering path
    fn render_frame_optimized(&mut self) -> Result<()> {
        // Advance time at target frame rate
        self.params.update_time(1.0 / 240.0);
        self.params.set_resolution(self.pipeline.width(), self.pipeline.height());

        // Build uniforms from current params
        let uniforms = ShaderUniforms::from_params(&self.params);

        // Update/status bar metrics and render line (if visible)
        let (gpu_load, vram_used_mb, vram_total_mb, bpm_stub) = self.futuristic_status_bar.get_system_metrics();
        self.futuristic_status_bar.update_metrics(self.current_fps, gpu_load, vram_used_mb, vram_total_mb, bpm_stub);
        self.futuristic_status_bar.update_beat(self.beat_detected);
        let status_line = if self.futuristic_status_bar.is_visible() {
            Some(self.futuristic_status_bar.render()?)
        } else {
            None
        };

        // Terminal background color from params (0..1 -> 0..255)
        let bg = (
            (self.params.terminal_bg_r * 255.0) as u8,
            (self.params.terminal_bg_g * 255.0) as u8,
            (self.params.terminal_bg_b * 255.0) as u8,
        );
        let terminal_bg_color = Some(bg);

        // Render the frame using shared rendering pipeline
        rendering::render_frame(
            &self.pipeline,
            &self.converter,
            &uniforms,
            status_line,
            terminal_bg_color,
            &mut self.debug_log,
        )
    }

    /// OPTIMIZED: Handle input events at a reduced rate
    fn handle_input(&mut self, running: &mut bool) -> Result<()> {
        if event::poll(Duration::from_millis(0))? {
            if let Event::Key(key) = event::read()? {
                match key.code {
                    KeyCode::Char('q') | KeyCode::Esc => {
                        *running = false;
                    }
                    KeyCode::Char('s') => {
                        // Toggle futuristic status bar visibility
                        self.futuristic_status_bar.toggle_visibility();
                    }
                    _ => {}
                }
            }
        }
        Ok(())
    }

    /// OPTIMIZED: Fill a small audio buffer quickly without allocations
    fn fill_audio_buffer_optimized(&mut self, buffer: &mut [f32]) {
        let t = self.params.time;
        for (i, s) in buffer.iter_mut().enumerate() {
            let x = i as f32;
            // Simple synthetic waveform to drive visuals when real audio is absent
            *s = ((x * 0.12 + t * 3.0).sin() + (x * 0.05 + t * 1.7).cos()) * 0.5;
        }
    }

    /// OPTIMIZED: Lightweight energy calculation
    fn calculate_energy_fast(&self, samples: &[f32]) -> f32 {
        let sum: f32 = samples.iter().map(|v| v.abs()).sum();
        (sum / samples.len() as f32).min(1.0)
    }

    /// OPTIMIZED: Lightweight frequency band partition
    fn calculate_frequency_bands_fast(&self, samples: &[f32]) -> (f32, f32, f32) {
        let n = samples.len().max(3);
        let third = n / 3;
        let bass = samples.iter().take(third).map(|v| v.abs()).sum::<f32>() / third as f32;
        let mid = samples.iter().skip(third).take(third).map(|v| v.abs()).sum::<f32>() / third as f32;
        let treble = samples.iter().skip(third * 2).map(|v| v.abs()).sum::<f32>() / (n - third * 2).max(1) as f32;
        (bass.min(1.0), mid.min(1.0), treble.min(1.0))
    }

    /// OPTIMIZED: Randomize visual parameters based on audio cues with minimal overhead
    fn randomize_everything_from_audio_fast(&mut self, energy: f32, bands: (f32, f32, f32), bpm: f32) -> Result<()> {
        // Delegate to the legacy implementation for now to preserve behavior
        self.randomize_everything_from_audio(energy, bands, bpm)
    }
    
    /// OPTIMIZED Update startup sequence - minimal overhead
    fn update_startup_optimized(&mut self, audio_buffer: &mut [f32]) -> Result<()> {
        // OPTIMIZED: Use pre-allocated buffer
        self.fill_audio_buffer_optimized(audio_buffer);
        
        // Update startup sequence
        let startup_update = self.startup.update(audio_buffer)?;
        
        // Detect phase change to trigger stinger
        if self.last_phase.map(|p| p != startup_update.phase).unwrap_or(true) {
            self.last_phase = Some(startup_update.phase);
            // Show stinger for 2 seconds on phase transitions
            self.stinger_until = Some(Instant::now() + Duration::from_secs(2));
        }
        
        // Update app state with startup parameters
        self.params = startup_update.params;
        self.pattern = startup_update.pattern;
        self.palette = startup_update.palette;
        self.color_mode = startup_update.color_mode;
        
        // OPTIMIZED: Only print progress every 60 frames (1 second at 60Hz)
        if startup_update.progress >= 1.0 {
            println!("✅ {} complete", startup_update.phase);
        }
        
        Ok(())
    }
    
    /// Update startup sequence (legacy - kept for compatibility)
    #[allow(dead_code)]
    fn update_startup(&mut self) -> Result<()> {
        // Get audio samples (simplified - in real implementation, this would come from audio input)
        let audio_samples = self.get_audio_samples();
        
        // Update startup sequence
        let startup_update = self.startup.update(&audio_samples)?;
        
        // Update app state with startup parameters
        self.params = startup_update.params;
        self.pattern = startup_update.pattern;
        self.palette = startup_update.palette;
        self.color_mode = startup_update.color_mode;
        
        // Print startup progress
        if startup_update.progress >= 1.0 {
            println!("✅ {} complete", startup_update.phase);
        }
        
        Ok(())
    }
    
    /// OPTIMIZED Update autonomous VJ - minimal overhead for 240 FPS
    fn update_autonomous_vj_optimized(&mut self, audio_buffer: &mut [f32]) -> Result<()> {
        // OPTIMIZED: Use pre-allocated buffer
        self.fill_audio_buffer_optimized(audio_buffer);
        
        // Update the visual orchestrator with audio data
        let orchestrator_result = self.orchestrator.update(audio_buffer)?;
        
        // Apply orchestrator recommendations
        self.apply_orchestrator_recommendations(&orchestrator_result)?;
        
        // OPTIMIZED: Simplified energy calculation (fallback)
        let energy = self.calculate_energy_fast(audio_buffer);
        let frequency_bands = self.calculate_frequency_bands_fast(audio_buffer);
        
        // OPTIMIZED: Minimal BPM processing
        let bpm_result = self.startup.get_bpm_detector().process_audio(audio_buffer)?;
        let bpm = bpm_result.bpm;
        
        // Capture beat for status bar pulse
        self.beat_detected = bpm_result.beat_detected;

        // Trigger terminal flash on extreme beats
        if self.beat_detected && energy > 0.4 {
            self.terminal_flash_until = Some(Instant::now() + Duration::from_millis(150));
        }
        
        // OPTIMIZED: Apply orchestrator-driven changes with minimal overhead
        self.apply_orchestrator_changes_fast(&orchestrator_result, energy, [frequency_bands.0, frequency_bands.1, frequency_bands.2], bpm)?;
        
        Ok(())
    }
    
    /// Apply orchestrator recommendations to current state
    fn apply_orchestrator_recommendations(&mut self, result: &OrchestratorIntegrationResult) -> Result<()> {
        // Apply recommended shader parameters
        self.params = result.recommended_params.clone();
        
        // Update pattern based on orchestrator state
        self.pattern = result.orchestrator_state.performance.primary_pattern;
        
        // Update color mode based on orchestrator recommendations
        self.color_mode = result.orchestrator_state.performance.color_scheme.primary;
        
        Ok(())
    }
    
    /// Apply orchestrator-driven changes with minimal overhead
    fn apply_orchestrator_changes_fast(&mut self, result: &OrchestratorIntegrationResult, energy: f32, frequency_bands: [f32; 3], bpm: f32) -> Result<()> {
        // Apply active effects
        for effect_state in &result.active_effects {
            self.apply_effect_fast(effect_state, energy, frequency_bands, bpm)?;
        }
        
        // Apply pending transitions
        for pending_transition in &result.pending_transitions {
            self.prepare_transition_fast(pending_transition)?;
        }
        
        // Update performance metrics
        self.update_performance_metrics(&result.integration_metrics);
        
        Ok(())
    }
    
    /// Apply effect with minimal overhead
    fn apply_effect_fast(&mut self, effect_state: &ActiveEffectState, energy: f32, frequency_bands: [f32; 3], bpm: f32) -> Result<()> {
        let intensity = effect_state.intensity;
        
        // Apply effect parameters based on type
        match effect_state.effect.trigger {
            EffectTrigger::Beat => {
                if self.beat_detected {
                    self.params.distort_amplitude += effect_state.effect.parameters.distortion * intensity;
                    self.params.scale += effect_state.effect.parameters.zoom * intensity;
                }
            },
            EffectTrigger::Frequency => {
                // Apply frequency-based effects
                self.params.frequency += frequency_bands[1] * effect_state.effect.parameters.speed_modifier * intensity;
            },
            EffectTrigger::Intensity => {
                // Apply intensity-based effects
                self.params.amplitude += energy * effect_state.effect.parameters.distortion * intensity;
            },
            _ => {
                // Apply general effects
                self.params.noise_strength += effect_state.effect.parameters.noise * intensity;
                self.params.vignette += effect_state.effect.parameters.vignette * intensity;
            }
        }
        
        Ok(())
    }
    
    /// Prepare transition with minimal overhead
    fn prepare_transition_fast(&mut self, _pending_transition: &PendingTransition) -> Result<()> {
        // Prepare transition logic here
        Ok(())
    }
    
    /// Update performance metrics
    fn update_performance_metrics(&mut self, _metrics: &IntegrationMetrics) {
        // Update performance metrics
    }
    
    /// Update autonomous VJ (MAXIMUM AUDIO REACTIVITY) - legacy
    #[allow(dead_code)]
    fn update_autonomous_vj(&mut self) -> Result<()> {
        // Get EXPLOSIVE audio samples
        let audio_samples = self.get_audio_samples();
        
        // Calculate EXPLOSIVE energy and frequency bands
        let energy = self.calculate_energy(&audio_samples);
        let frequency_bands = self.calculate_frequency_bands(&audio_samples);
        
        // Process audio for BPM detection
        let bpm_result = self.startup.get_bpm_detector().process_audio(&audio_samples)?;
        
        // Keep beat state for UI
        self.beat_detected = bpm_result.beat_detected;

        // Trigger terminal flash on extreme beats (legacy path)
        if self.beat_detected && energy > 0.4 {
            self.terminal_flash_until = Some(Instant::now() + Duration::from_millis(150));
        }
        
        // MAXIMUM AUDIO REACTIVITY - Randomize everything based on audio!
        self.randomize_everything_from_audio(energy, frequency_bands, bpm_result.bpm)?;
        
        // Update macro state engine with EXPLOSIVE values
        self.startup.get_macro_state_engine().update_audio_analysis(
            bpm_result.bpm,
            energy,
            bpm_result.beat_detected,
            frequency_bands,
        )?;
        
        // Get current VJ state
        let vj_state = self.startup.get_macro_state_engine().get_current_state();
        
        // Update app state with MAXIMUM reactivity
        self.params = self.startup.get_macro_state_engine().get_randomized_params(&self.params);
        self.pattern = vj_state.pattern;
        self.palette = vj_state.palette;
        self.color_mode = vj_state.color_mode;

        // Auto-trigger shader effects on musical beats, with mood-aware selection
        self.trigger_auto_effects(vj_state.mood, bpm_result.beat_detected, energy);
        
        Ok(())
    }
    
    /// MAXIMUM AUDIO REACTIVITY - Randomize everything based on audio! (OPTIMIZED)
    fn randomize_everything_from_audio(&mut self, energy: f32, bands: (f32, f32, f32), bpm: f32) -> Result<()> {
        let time = self.startup_start_time.elapsed().as_secs_f32();
        let (bass, mid, treble) = bands;

        // Remove ultra-frequent hard switches; rely on MacroStateEngine for pattern/palette/color transitions.
        // Occasionally allow a major state change if enough time has passed and the music is hot.
        if self.last_auto_change.elapsed() > Duration::from_secs(10) && (energy > 0.7 || bpm > 130.0) {
            self.pattern = self.get_random_pattern_from_audio(bass, mid, treble);
            self.palette = self.get_random_palette_from_audio(bass, mid, treble);
            self.color_mode = self.get_random_color_mode_from_audio(bpm, energy);
            self.last_auto_change = Instant::now();
            println!("🎛️ AUTO-DJ: Switched core vibe → pattern={:?}, palette={:?}, color={:?}", self.pattern, self.palette, self.color_mode);
        }

        // Compute a target parameter set based on audio
        let target = self.get_explosive_params_from_audio(energy, bands, bpm);
        
        // Smoothly move towards target for less flicker
        self.smooth_apply_params(&target, 0.15);

        Ok(())
    }
    
    /// EXPLOSIVE parameter calculation (for dramatic visual changes)
    fn get_explosive_params_from_audio(&self, energy: f32, bands: (f32, f32, f32), bpm: f32) -> ShaderParams {
        let (bass, mid, treble) = bands;
        let time = self.startup_start_time.elapsed().as_secs_f32();
        let mut params = ShaderParams::default();
        params.frequency = 1.0 + treble * 10.0;
        params.amplitude = 0.1 + bass * 2.0;
        params.speed = 0.01 + (bpm / 60.0) * 1.0;
        params.brightness = 0.2 + energy * 1.5;
        params.contrast = 0.5 + mid * 1.5;
        params.saturation = 0.1 + (bass + mid + treble) * 1.0;
        params.hue = (time * 50.0 + energy * 100.0) % 360.0;
        params.noise_strength = treble * 0.5;
        params.distort_amplitude = bass * 0.8;
        params.vignette = energy * 0.3;
        params.scale = 0.1 + (bpm / 200.0) * 0.5;
        params.time = time;
        params.effect_time = time;
        params.beat_distortion_time = time;
        params
    }
    
    fn get_audio_samples(&self) -> Vec<f32> {
        let time = self.startup_start_time.elapsed().as_secs_f32();
        let mut samples = Vec::with_capacity(256);
        let bass_freq = 60.0;
        let drop_period = 2.0;
        for i in 0..256 {
            let t = time + (i as f32 / 44100.0);
            let bass = (2.0 * std::f32::consts::PI * bass_freq * t).sin() * 1.5;
            let kick = if (t * 2.0).fract() < 0.1 { 2.0 } else { 0.0 };
            let snare = if (t * 4.0).fract() > 0.9 { 1.0 } else { 0.0 };
            let hihat = (2.0 * std::f32::consts::PI * 8000.0 * t).sin() * 0.3;
            let drop_factor = if (time % drop_period) > (drop_period - 0.2) { 3.0 } else { 1.0 };
            let sample = (bass + kick + snare + hihat) * drop_factor;
            samples.push(sample.clamp(-2.0, 2.0));
        }
        samples
    }

    fn calculate_energy(&self, samples: &[f32]) -> f32 {
        if samples.is_empty() { return 0.0; }
        let rms = (samples.iter().map(|&x| x * x).sum::<f32>() / samples.len() as f32).sqrt();
        let time = self.startup_start_time.elapsed().as_secs_f32();
        let dynamic_factor = 0.5 + 0.5 * (2.0 * std::f32::consts::PI * 1.0 * time).sin().abs();
        let drop_factor = if (time % 2.0) > 1.8 { 2.0 } else { 1.0 };
        (rms * dynamic_factor * drop_factor).clamp(0.0, 3.0)
    }

    fn calculate_frequency_bands(&self, samples: &[f32]) -> (f32, f32, f32) {
        if samples.is_empty() { return (0.0, 0.0, 0.0); }
        let len = samples.len();
        let quarter = len / 4;
        let half = len / 2;
        let bass_energy = samples[..quarter].iter().map(|&x| x.abs()).sum::<f32>() / quarter as f32;
        let mid_energy = samples[quarter..quarter + half].iter().map(|&x| x.abs()).sum::<f32>() / half as f32;
        let treble_energy = samples[quarter + half..].iter().map(|&x| x.abs()).sum::<f32>() / (len - quarter - half) as f32;
        let time = self.startup_start_time.elapsed().as_secs_f32();
        let modulation = 1.0 + 0.3 * (2.0 * std::f32::consts::PI * 2.0 * time).sin().abs();
        (
            (bass_energy * modulation).clamp(0.0, 2.0),
            (mid_energy * modulation).clamp(0.0, 2.0),
            (treble_energy * modulation).clamp(0.0, 2.0),
        )
    }

    fn get_random_pattern_from_audio(&self, bass: f32, mid: f32, treble: f32) -> PatternType {
        if bass >= mid && bass >= treble { PatternType::Vortex }
        else if mid >= treble { PatternType::Waves }
        else { PatternType::Interference }
    }

    fn get_random_palette_from_audio(&self, bass: f32, mid: f32, treble: f32) -> PaletteType {
        if bass >= mid && bass >= treble { PaletteType::Blocks }
        else if mid >= treble { PaletteType::Smooth }
        else { PaletteType::Shades }
    }

    fn get_random_color_mode_from_audio(&self, bpm: f32, energy: f32) -> ColorMode {
        if bpm >= 140.0 && energy >= 0.5 { ColorMode::Neon }
        else if energy < 0.2 { ColorMode::Pastel }
        else { ColorMode::Rainbow }
    }

    // Smoothly interpolate current params towards target values
    fn smooth_apply_params(&mut self, target: &ShaderParams, alpha: f32) {
        fn lerp(a: f32, b: f32, t: f32) -> f32 { a + (b - a) * t }
        self.params.frequency = lerp(self.params.frequency, target.frequency, alpha);
        self.params.amplitude = lerp(self.params.amplitude, target.amplitude, alpha);
        self.params.speed = lerp(self.params.speed, target.speed, alpha);
        self.params.brightness = lerp(self.params.brightness, target.brightness, alpha);
        self.params.contrast = lerp(self.params.contrast, target.contrast, alpha);
        self.params.saturation = lerp(self.params.saturation, target.saturation, alpha);
        // Hue wraps around 360; take the shortest path
        let mut dh = target.hue - self.params.hue;
        if dh > 180.0 { dh -= 360.0; } else if dh < -180.0 { dh += 360.0; }
        self.params.hue = self.params.hue + dh * alpha;
        self.params.noise_strength = lerp(self.params.noise_strength, target.noise_strength, alpha);
        self.params.distort_amplitude = lerp(self.params.distort_amplitude, target.distort_amplitude, alpha);
        self.params.vignette = lerp(self.params.vignette, target.vignette, alpha);
        self.params.scale = lerp(self.params.scale, target.scale, alpha);
        // Camera smoothing (if used)
        self.params.camera_zoom = lerp(self.params.camera_zoom, target.camera_zoom, alpha);
        self.params.camera_pan_x = lerp(self.params.camera_pan_x, target.camera_pan_x, alpha);
        self.params.camera_pan_y = lerp(self.params.camera_pan_y, target.camera_pan_y, alpha);
        self.params.camera_rotation = lerp(self.params.camera_rotation, target.camera_rotation, alpha);
        // Beat strengths
        self.params.beat_distortion_strength = lerp(self.params.beat_distortion_strength, target.beat_distortion_strength, alpha);
        self.params.beat_zoom_strength = lerp(self.params.beat_zoom_strength, target.beat_zoom_strength, alpha);
        // Clamp after blending
        self.params.clamp_all();
    }

    // Mood-aware automatic effect triggering on beats
    fn trigger_auto_effects(&mut self, mood: chroma::vj::MusicMood, beat_detected: bool, energy: f32) {
        if !beat_detected { return; }
        // Throttle effect triggers to avoid flicker
        if self.last_effect_trigger.elapsed() < Duration::from_millis(800) { return; }
        let now_t = self.startup_start_time.elapsed().as_secs_f32();
        let chosen_effect = match mood {
            chroma::vj::MusicMood::Ambient => 6,   // smooth wave sweep
            chroma::vj::MusicMood::Energetic => 5, // starburst
            chroma::vj::MusicMood::Melodic => 2,   // diamond ring
            chroma::vj::MusicMood::Rhythmic => 0,  // circular ring
            chroma::vj::MusicMood::Chaotic => 4,   // grid blast
        } as u32;

        self.params.effect_type = chosen_effect;
        self.params.effect_time = now_t; // start the effect window
        // Reinforce beat-driven distort/zoom with gentle strengths
        self.params.beat_distortion_time = now_t;
        self.params.beat_distortion_strength = (0.4 + energy * 0.6).clamp(0.3, 0.9);
        self.params.beat_zoom_strength = (0.25 + energy * 0.5).clamp(0.2, 0.8);
        self.last_effect_trigger = Instant::now();
    }
}
