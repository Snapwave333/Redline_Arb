use anyhow::Result;
use chroma::vj::{MacroStateEngine, BPMDetector, PatternMorpher, VJState};
use chroma::params::ShaderParams;
use std::time::Instant;

/// VJ Integration Module
/// 
/// Integrates the autonomous VJ system with the main application,
/// handling the transition from manual control to autonomous operation.
#[allow(dead_code)]
pub struct VJIntegration {
    // Core VJ components
    macro_state_engine: MacroStateEngine,
    bpm_detector: BPMDetector,
    pattern_morpher: PatternMorpher,
    
    // VJ state
    autonomous_mode: bool,
    vj_start_time: Instant,
    last_audio_update: Instant,
    
    // Audio analysis state
    current_bpm: f32,
    current_energy: f32,
    beat_detected: bool,
    frequency_bands: (f32, f32, f32), // bass, mid, treble
    
    // Performance tracking
    frame_count: u64,
    last_fps_update: Instant,
    current_fps: f32,
}

#[allow(dead_code)]
impl VJIntegration {
    /// Create a new VJ integration
    pub fn new(sample_rate: f32) -> Self {
        Self {
            macro_state_engine: MacroStateEngine::new(),
            bpm_detector: BPMDetector::new(sample_rate),
            pattern_morpher: PatternMorpher::new(),
            
            autonomous_mode: false,
            vj_start_time: Instant::now(),
            last_audio_update: Instant::now(),
            
            current_bpm: 120.0,
            current_energy: 0.5,
            beat_detected: false,
            frequency_bands: (0.5, 0.5, 0.5),
            
            frame_count: 0,
            last_fps_update: Instant::now(),
            current_fps: 60.0,
        }
    }
    
    /// Enable autonomous VJ mode
    pub fn enable_autonomous_mode(&mut self) {
        self.autonomous_mode = true;
        self.vj_start_time = Instant::now();
        println!("🎵 Autonomous VJ mode enabled! Let the music control the visuals...");
    }
    
    /// Disable autonomous VJ mode
    pub fn disable_autonomous_mode(&mut self) {
        self.autonomous_mode = false;
        println!("🎮 Manual control mode enabled.");
    }
    
    /// Check if in autonomous mode
    pub fn is_autonomous_mode(&self) -> bool {
        self.autonomous_mode
    }
    
    /// Update VJ system with audio data
    pub fn update_audio(&mut self, audio_samples: &[f32]) -> Result<()> {
        if !self.autonomous_mode {
            return Ok(());
        }
        
        // Process audio for BPM detection
        let bpm_result = self.bpm_detector.process_audio(audio_samples)?;
        self.current_bpm = bpm_result.bpm;
        self.beat_detected = bpm_result.beat_detected;
        
        // Calculate energy and frequency bands (simplified)
        self.calculate_audio_analysis(audio_samples)?;
        
        // Update macro state engine
        self.macro_state_engine.update_audio_analysis(
            self.current_bpm,
            self.current_energy,
            self.beat_detected,
            self.frequency_bands,
        )?;
        
        // Update pattern morpher
        self.pattern_morpher.update_morph(
            self.current_bpm,
            self.current_energy,
            self.beat_detected,
        )?;
        
        self.last_audio_update = Instant::now();
        Ok(())
    }
    
    /// Get current VJ state for rendering
    pub fn get_vj_state(&self) -> VJState {
        self.macro_state_engine.get_current_state()
    }
    
    /// Get morphed shader parameters
    pub fn get_morphed_params(&self, base_params: &ShaderParams) -> ShaderParams {
        if !self.autonomous_mode {
            return base_params.clone();
        }
        
        // Get intelligent parameter randomization
        let randomized_params = self.macro_state_engine.get_randomized_params(base_params);
        
        // Apply morphing if in progress
        if self.pattern_morpher.is_morphing() {
            self.pattern_morpher.get_morphed_params()
        } else {
            randomized_params
        }
    }
    
    /// Get current pattern (considering morphing)
    pub fn get_current_pattern(&self) -> chroma::params::PatternType {
        if !self.autonomous_mode {
            return chroma::params::PatternType::Plasma; // Default
        }
        
        if self.pattern_morpher.is_morphing() {
            self.pattern_morpher.get_current_pattern()
        } else {
            self.macro_state_engine.get_current_state().pattern
        }
    }
    
    /// Get current palette
    pub fn get_current_palette(&self) -> chroma::params::PaletteType {
        if !self.autonomous_mode {
            return chroma::params::PaletteType::Standard; // Default
        }
        
        self.macro_state_engine.get_current_state().palette
    }
    
    /// Get current color mode
    pub fn get_current_color_mode(&self) -> chroma::params::ColorMode {
        if !self.autonomous_mode {
            return chroma::params::ColorMode::Rainbow; // Default
        }
        
        self.macro_state_engine.get_current_state().color_mode
    }
    
    /// Update frame count for FPS tracking
    pub fn update_frame(&mut self) {
        self.frame_count += 1;
        
        let now = Instant::now();
        let elapsed = now.duration_since(self.last_fps_update);
        
        if elapsed >= std::time::Duration::from_secs(1) {
            self.current_fps = self.frame_count as f32 / elapsed.as_secs_f32();
            self.frame_count = 0;
            self.last_fps_update = now;
        }
    }
    
    /// Get current FPS
    pub fn get_fps(&self) -> f32 {
        self.current_fps
    }
    
    /// Get VJ statistics
    pub fn get_vj_stats(&self) -> VJStats {
        VJStats {
            autonomous_mode: self.autonomous_mode,
            uptime: self.vj_start_time.elapsed(),
            current_bpm: self.current_bpm,
            current_energy: self.current_energy,
            beat_detected: self.beat_detected,
            morphing: self.pattern_morpher.is_morphing(),
            morph_progress: self.pattern_morpher.get_morph_progress(),
            current_fps: self.current_fps,
            frequency_bands: self.frequency_bands,
        }
    }
    
    /// Calculate audio analysis (simplified implementation)
    fn calculate_audio_analysis(&mut self, samples: &[f32]) -> Result<()> {
        if samples.is_empty() {
            return Ok(());
        }
        
        // Calculate RMS energy
        let rms = (samples.iter().map(|&x| x * x).sum::<f32>() / samples.len() as f32).sqrt();
        self.current_energy = rms.clamp(0.0, 1.0);
        
        // Simplified frequency band analysis
        // In a real implementation, this would use FFT
        let bass_energy = samples.iter().take(samples.len() / 4).map(|&x| x.abs()).sum::<f32>() / (samples.len() / 4) as f32;
        let mid_energy = samples.iter().skip(samples.len() / 4).take(samples.len() / 2).map(|&x| x.abs()).sum::<f32>() / (samples.len() / 2) as f32;
        let treble_energy = samples.iter().skip(3 * samples.len() / 4).map(|&x| x.abs()).sum::<f32>() / (samples.len() / 4) as f32;
        
        self.frequency_bands = (
            bass_energy.clamp(0.0, 1.0),
            mid_energy.clamp(0.0, 1.0),
            treble_energy.clamp(0.0, 1.0),
        );
        
        Ok(())
    }
    
    /// Force a pattern transition (for testing)
    pub fn force_transition(&mut self) -> Result<()> {
        if !self.autonomous_mode {
            return Ok(());
        }
        
        // This would trigger a manual transition in the MSE
        // For now, we'll just log it
        println!("🎭 Forcing pattern transition...");
        Ok(())
    }
    
    /// Reset VJ system
    pub fn reset(&mut self) {
        self.bpm_detector.reset();
        self.macro_state_engine = MacroStateEngine::new();
        self.pattern_morpher = PatternMorpher::new();
        self.vj_start_time = Instant::now();
        self.frame_count = 0;
        self.current_fps = 60.0;
    }
}

/// VJ Statistics
#[allow(dead_code)]
#[derive(Debug, Clone)]
pub struct VJStats {
    pub autonomous_mode: bool,
    pub uptime: std::time::Duration,
    pub current_bpm: f32,
    pub current_energy: f32,
    pub beat_detected: bool,
    pub morphing: bool,
    pub morph_progress: f32,
    pub current_fps: f32,
    pub frequency_bands: (f32, f32, f32),
}

impl std::fmt::Display for VJStats {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(
            f,
            "VJ Stats:\n  Mode: {}\n  Uptime: {:.1}s\n  BPM: {:.1}\n  Energy: {:.2}\n  Beat: {}\n  Morphing: {} ({:.1}%)\n  FPS: {:.1}\n  Bands: B:{:.2} M:{:.2} T:{:.2}",
            if self.autonomous_mode { "Autonomous" } else { "Manual" },
            self.uptime.as_secs_f32(),
            self.current_bpm,
            self.current_energy,
            if self.beat_detected { "YES" } else { "NO" },
            if self.morphing { "YES" } else { "NO" },
            self.morph_progress * 100.0,
            self.current_fps,
            self.frequency_bands.0,
            self.frequency_bands.1,
            self.frequency_bands.2,
        )
    }
}
