use anyhow::Result;
use std::time::{Duration, Instant};
use crate::vj::{MacroStateEngine, BPMDetector, PatternMorpher};
use crate::params::{ShaderParams, PatternType, PaletteType, ColorMode};

/// Autonomous VJ Startup Sequence
/// 
/// Handles the intuitive startup process:
/// 1. Launch & Initialization
/// 2. Audio Setup (Auto-Select)
/// 3. BPM Detection
/// 4. First Cue (The Drop)
/// 5. Synchronization
pub struct AutonomousStartup {
    // Startup phases
    current_phase: StartupPhase,
    phase_start_time: Instant,
    phase_duration: Duration,
    
    // Core VJ components
    macro_state_engine: MacroStateEngine,
    bpm_detector: BPMDetector,
    pattern_morpher: PatternMorpher,
    
    // Audio analysis state
    audio_detected: bool,
    bpm_confident: bool,
    bpm_confidence_threshold: f32,
    analysis_samples: Vec<f32>,
    
    // Startup configuration
    attract_loop_pattern: PatternType,
    first_drop_pattern: PatternType,
    startup_complete: bool,
}

#[derive(Debug, Clone, Copy, PartialEq)]
pub enum StartupPhase {
    Initialization,    // Loading shaders and palettes
    AudioSetup,        // Auto-selecting audio input
    BPMDetection,      // Analyzing music tempo
    FirstCue,          // Selecting starting pattern
    Synchronization,   // Syncing with music
    Running,           // Autonomous VJ active
}

impl AutonomousStartup {
    /// Create a new autonomous startup sequence
    pub fn new(sample_rate: f32) -> Self {
        Self {
            current_phase: StartupPhase::Initialization,
            phase_start_time: Instant::now(),
            phase_duration: Duration::from_secs(2),
            
            macro_state_engine: MacroStateEngine::new(),
            bpm_detector: BPMDetector::new(sample_rate),
            pattern_morpher: PatternMorpher::new(),
            
            audio_detected: false,
            bpm_confident: false,
            bpm_confidence_threshold: 0.7,
            analysis_samples: Vec::new(),
            
            attract_loop_pattern: PatternType::Waves,
            first_drop_pattern: PatternType::Plasma,
            startup_complete: false,
        }
    }
    
    /// Update the startup sequence
    pub fn update(&mut self, audio_samples: &[f32]) -> Result<StartupUpdate> {
        match self.current_phase {
            StartupPhase::Initialization => self.update_initialization(),
            StartupPhase::AudioSetup => self.update_audio_setup(audio_samples),
            StartupPhase::BPMDetection => self.update_bpm_detection(audio_samples),
            StartupPhase::FirstCue => self.update_first_cue(),
            StartupPhase::Synchronization => self.update_synchronization(),
            StartupPhase::Running => self.update_running(),
        }
    }
    
    /// Update initialization phase
    fn update_initialization(&mut self) -> Result<StartupUpdate> {
        let elapsed = self.phase_start_time.elapsed();
        
        if elapsed >= self.phase_duration {
            println!("🎨 Initialization complete - Loading shaders and palettes");
            self.next_phase(StartupPhase::AudioSetup);
        }
        
        Ok(StartupUpdate {
            phase: self.current_phase,
            progress: elapsed.as_secs_f32() / self.phase_duration.as_secs_f32(),
            message: "Initializing VJ engine...".to_string(),
            should_render: true,
            pattern: self.attract_loop_pattern,
            palette: PaletteType::Smooth,
            color_mode: ColorMode::Cool,
            params: self.get_attract_loop_params(),
        })
    }
    
    /// Update audio setup phase
    fn update_audio_setup(&mut self, audio_samples: &[f32]) -> Result<StartupUpdate> {
        // Analyze audio samples for detection
        if !audio_samples.is_empty() {
            let rms = (audio_samples.iter().map(|&x| x * x).sum::<f32>() / audio_samples.len() as f32).sqrt();
            self.audio_detected = rms > 0.01; // Threshold for audio detection
        }
        
        let elapsed = self.phase_start_time.elapsed();
        
        if self.audio_detected {
            println!("🎵 Audio detected - Starting BPM analysis");
            self.next_phase(StartupPhase::BPMDetection);
        } else if elapsed >= Duration::from_secs(5) {
            println!("🔇 No audio detected - Starting attract loop");
            self.next_phase(StartupPhase::Running);
        }
        
        Ok(StartupUpdate {
            phase: self.current_phase,
            progress: elapsed.as_secs_f32() / 5.0,
            message: if self.audio_detected { 
                "Audio detected!".to_string() 
            } else { 
                "Listening for audio...".to_string() 
            },
            should_render: true,
            pattern: self.attract_loop_pattern,
            palette: PaletteType::Smooth,
            color_mode: ColorMode::Cool,
            params: self.get_attract_loop_params(),
        })
    }
    
    /// Update BPM detection phase
    fn update_bpm_detection(&mut self, audio_samples: &[f32]) -> Result<StartupUpdate> {
        // Process audio for BPM detection
        let bpm_result = self.bpm_detector.process_audio(audio_samples)?;
        self.bpm_confident = bpm_result.confidence > self.bpm_confidence_threshold;
        
        let elapsed = self.phase_start_time.elapsed();
        
        if self.bpm_confident {
            println!("🎯 BPM detected: {:.1} (confidence: {:.2})", bpm_result.bpm, bpm_result.confidence);
            self.next_phase(StartupPhase::FirstCue);
        } else if elapsed >= Duration::from_secs(10) {
            println!("⏰ BPM detection timeout - Starting with default tempo");
            self.next_phase(StartupPhase::FirstCue);
        }
        
        Ok(StartupUpdate {
            phase: self.current_phase,
            progress: elapsed.as_secs_f32() / 10.0,
            message: format!("Analyzing tempo... BPM: {:.1}", bpm_result.bpm),
            should_render: true,
            pattern: self.attract_loop_pattern,
            palette: PaletteType::Smooth,
            color_mode: ColorMode::Cool,
            params: self.get_attract_loop_params(),
        })
    }
    
    /// Update first cue phase
    fn update_first_cue(&mut self) -> Result<StartupUpdate> {
        // Select high-energy starting pattern
        let bpm = self.bpm_detector.get_bpm();
        let energy = 0.8; // High energy for the drop
        
        // Update macro state engine with detected BPM
        self.macro_state_engine.update_audio_analysis(
            bpm,
            energy,
            true, // Beat detected
            (0.7, 0.6, 0.5), // High bass, moderate mid/treble
        )?;
        
        println!("🎭 First cue selected - Preparing the drop!");
        self.next_phase(StartupPhase::Synchronization);
        
        Ok(StartupUpdate {
            phase: self.current_phase,
            progress: 1.0,
            message: "Preparing the drop...".to_string(),
            should_render: true,
            pattern: self.first_drop_pattern,
            palette: PaletteType::Blocks,
            color_mode: ColorMode::Neon,
            params: self.get_first_drop_params(),
        })
    }
    
    /// Update synchronization phase
    fn update_synchronization(&mut self) -> Result<StartupUpdate> {
        let elapsed = self.phase_start_time.elapsed();
        
        // Wait for musical measure alignment (4 beats)
        let bpm = self.bpm_detector.get_bpm();
        let beat_duration = 60.0 / bpm;
        let measure_duration = beat_duration * 4.0; // 4 beats = 1 measure
        
        if elapsed.as_secs_f32() >= measure_duration {
            println!("🚀 SHOW TIME! Autonomous VJ is now running");
            self.startup_complete = true;
            self.next_phase(StartupPhase::Running);
        }
        
        Ok(StartupUpdate {
            phase: self.current_phase,
            progress: elapsed.as_secs_f32() / measure_duration,
            message: "Synchronizing with music...".to_string(),
            should_render: true,
            pattern: self.first_drop_pattern,
            palette: PaletteType::Blocks,
            color_mode: ColorMode::Neon,
            params: self.get_first_drop_params(),
        })
    }
    
    /// Update running phase
    fn update_running(&mut self) -> Result<StartupUpdate> {
        // Get current VJ state
        let vj_state = self.macro_state_engine.get_current_state();
        
        Ok(StartupUpdate {
            phase: self.current_phase,
            progress: 1.0,
            message: "Autonomous VJ running".to_string(),
            should_render: true,
            pattern: vj_state.pattern,
            palette: vj_state.palette,
            color_mode: vj_state.color_mode,
            params: self.get_running_params(),
        })
    }
    
    /// Move to next startup phase
    fn next_phase(&mut self, new_phase: StartupPhase) {
        self.current_phase = new_phase;
        self.phase_start_time = Instant::now();
        
        // Set phase-specific duration
        self.phase_duration = match new_phase {
            StartupPhase::Initialization => Duration::from_secs(2),
            StartupPhase::AudioSetup => Duration::from_secs(5),
            StartupPhase::BPMDetection => Duration::from_secs(10),
            StartupPhase::FirstCue => Duration::from_secs(1),
            StartupPhase::Synchronization => Duration::from_secs(4),
            StartupPhase::Running => Duration::from_secs(0),
        };
    }
    
    /// Get attract loop parameters (ambient, non-reactive)
    fn get_attract_loop_params(&self) -> ShaderParams {
        ShaderParams {
            frequency: 8.0,
            amplitude: 0.5,
            speed: 0.3,
            scale: 1.0,
            brightness: 0.8,
            contrast: 1.0,
            saturation: 0.7,
            hue: 200.0, // Cool blue
            noise_strength: 0.1,
            distort_amplitude: 0.0,
            vignette: 0.3,
            ..ShaderParams::default()
        }
    }
    
    /// Get first drop parameters (high energy)
    fn get_first_drop_params(&self) -> ShaderParams {
        ShaderParams {
            frequency: 12.0,
            amplitude: 1.2,
            speed: 0.8,
            scale: 1.0,
            brightness: 1.2,
            contrast: 1.3,
            saturation: 1.5,
            hue: 0.0, // Neon colors
            noise_strength: 0.2,
            distort_amplitude: 0.3,
            vignette: 0.1,
            ..ShaderParams::default()
        }
    }
    
    /// Get running parameters (VJ-controlled)
    fn get_running_params(&self) -> ShaderParams {
        let base_params = ShaderParams::default();
        self.macro_state_engine.get_randomized_params(&base_params)
    }
    
    /// Check if startup is complete
    pub fn is_startup_complete(&self) -> bool {
        self.startup_complete
    }
    
    /// Get current startup phase
    pub fn get_current_phase(&self) -> StartupPhase {
        self.current_phase
    }
    
    /// Get macro state engine (for VJ integration)
    pub fn get_macro_state_engine(&mut self) -> &mut MacroStateEngine {
        &mut self.macro_state_engine
    }
    
    /// Get BPM detector (for VJ integration)
    pub fn get_bpm_detector(&mut self) -> &mut BPMDetector {
        &mut self.bpm_detector
    }
    
    /// Get pattern morpher (for VJ integration)
    pub fn get_pattern_morpher(&mut self) -> &mut PatternMorpher {
        &mut self.pattern_morpher
    }
    
    /// Check if audio is detected
    pub fn is_audio_detected(&self) -> bool {
        self.audio_detected
    }
    
    /// Check if BPM is confident
    pub fn is_bpm_confident(&self) -> bool {
        self.bpm_confident
    }
    
    /// Get current BPM
    pub fn get_current_bpm(&self) -> f32 {
        self.bpm_detector.get_bpm()
    }
}

/// Startup update information
#[derive(Debug, Clone)]
pub struct StartupUpdate {
    pub phase: StartupPhase,
    pub progress: f32,
    pub message: String,
    pub should_render: bool,
    pub pattern: PatternType,
    pub palette: PaletteType,
    pub color_mode: ColorMode,
    pub params: ShaderParams,
}

impl std::fmt::Display for StartupPhase {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            StartupPhase::Initialization => write!(f, "Initialization"),
            StartupPhase::AudioSetup => write!(f, "Audio Setup"),
            StartupPhase::BPMDetection => write!(f, "BPM Detection"),
            StartupPhase::FirstCue => write!(f, "First Cue"),
            StartupPhase::Synchronization => write!(f, "Synchronization"),
            StartupPhase::Running => write!(f, "Running"),
        }
    }
}




