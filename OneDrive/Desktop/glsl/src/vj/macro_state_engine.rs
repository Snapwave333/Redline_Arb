use anyhow::Result;
use std::collections::{HashMap, VecDeque};
use std::time::{Duration, Instant};
use crate::params::{PatternType, PaletteType, ColorMode, ShaderParams};

/// Macro-State Engine - The brain of the autonomous VJ
/// 
/// This engine analyzes audio input and makes intelligent decisions about:
/// - When to transition between patterns
/// - Which patterns/palettes to select
/// - How to morph between states
/// - Parameter randomization based on music mood
pub struct MacroStateEngine {
    // Current state
    current_pattern: PatternType,
    current_palette: PaletteType,
    current_color_mode: ColorMode,
    
    // Audio analysis state
    bpm: f32,
    energy_level: f32,
    mood: MusicMood,
    last_beat_time: Instant,
    beat_history: VecDeque<Instant>,
    
    // Transition control
    transition_in_progress: bool,
    transition_start_time: Instant,
    transition_duration: Duration,
    morph_factor: f32,
    
    // Pattern/palette management
    pattern_blacklist: HashMap<String, Instant>,
    palette_blacklist: HashMap<String, Instant>,
    blacklist_duration: Duration,
    
    // State history for intelligent decisions
    pattern_history: VecDeque<PatternType>,
    palette_history: VecDeque<PaletteType>,
    transition_history: VecDeque<TransitionEvent>,
    
    // Configuration
    min_pattern_duration: Duration,
    max_pattern_duration: Duration,
    transition_probability: f32,
}

#[derive(Debug, Clone, Copy, PartialEq)]
pub enum MusicMood {
    Ambient,      // Slow, atmospheric
    Energetic,    // Fast, high-energy
    Melodic,      // Moderate tempo, melodic
    Rhythmic,     // Strong beat, danceable
    Chaotic,      // Complex, unpredictable
}

#[derive(Debug, Clone)]
pub struct TransitionEvent {
    pub from_pattern: PatternType,
    pub to_pattern: PatternType,
    pub from_palette: PaletteType,
    pub to_palette: PaletteType,
    pub trigger: TransitionTrigger,
    pub timestamp: Instant,
}

#[derive(Debug, Clone)]
pub enum TransitionTrigger {
    BeatDetected,
    EnergyChange,
    TimeBased,
    MoodChange,
    Random,
}

impl MacroStateEngine {
    /// Create a new Macro-State Engine
    pub fn new() -> Self {
        Self {
            current_pattern: PatternType::Plasma,
            current_palette: PaletteType::Standard,
            current_color_mode: ColorMode::Rainbow,
            
            bpm: 120.0,
            energy_level: 0.5,
            mood: MusicMood::Melodic,
            last_beat_time: Instant::now(),
            beat_history: VecDeque::with_capacity(32),
            
            transition_in_progress: false,
            transition_start_time: Instant::now(),
            transition_duration: Duration::from_millis(2000),
            morph_factor: 0.0,
            
            pattern_blacklist: HashMap::new(),
            palette_blacklist: HashMap::new(),
            blacklist_duration: Duration::from_secs(30),
            
            pattern_history: VecDeque::with_capacity(10),
            palette_history: VecDeque::with_capacity(10),
            transition_history: VecDeque::with_capacity(20),
            
            min_pattern_duration: Duration::from_secs(8),
            max_pattern_duration: Duration::from_secs(45),
            transition_probability: 0.3,
        }
    }
    
    /// Update the engine with new audio analysis data
    pub fn update_audio_analysis(
        &mut self,
        bpm: f32,
        energy_level: f32,
        beat_detected: bool,
        frequency_bands: (f32, f32, f32), // bass, mid, treble
    ) -> Result<()> {
        // Update BPM
        self.bpm = bpm;
        self.energy_level = energy_level;
        
        // Detect mood based on audio characteristics
        self.mood = self.detect_mood(bpm, energy_level, frequency_bands);
        
        // Track beats
        if beat_detected {
            self.last_beat_time = Instant::now();
            self.beat_history.push_back(self.last_beat_time);
            
            // Keep only recent beats
            while self.beat_history.len() > 32 {
                self.beat_history.pop_front();
            }
        }
        
        // Update transition state
        self.update_transition_state()?;
        
        // Check for transition triggers
        if self.should_transition() {
            self.initiate_transition()?;
        }
        
        Ok(())
    }
    
    /// Get the current visual state for rendering
    pub fn get_current_state(&self) -> VJState {
        VJState {
            pattern: self.current_pattern,
            palette: self.current_palette,
            color_mode: self.current_color_mode,
            morph_factor: self.morph_factor,
            energy_level: self.energy_level,
            mood: self.mood,
            bpm: self.bpm,
        }
    }
    
    /// Detect music mood based on audio characteristics
    fn detect_mood(&self, bpm: f32, energy: f32, bands: (f32, f32, f32)) -> MusicMood {
        let (bass, _mid, treble) = bands;
        
        // High BPM + High Energy = Energetic
        if bpm > 140.0 && energy > 0.7 {
            return MusicMood::Energetic;
        }
        
        // Low BPM + Low Energy = Ambient
        if bpm < 80.0 && energy < 0.3 {
            return MusicMood::Ambient;
        }
        
        // Strong bass + moderate tempo = Rhythmic
        if bass > 0.6 && bpm > 100.0 && bpm < 140.0 {
            return MusicMood::Rhythmic;
        }
        
        // High treble + complex patterns = Chaotic
        if treble > 0.7 && energy > 0.5 {
            return MusicMood::Chaotic;
        }
        
        // Default to Melodic
        MusicMood::Melodic
    }
    
    /// Check if a transition should occur
    fn should_transition(&self) -> bool {
        if self.transition_in_progress {
            return false;
        }
        
        let current_duration = self.transition_start_time.elapsed();
        
        // Force transition after max duration
        if current_duration > self.max_pattern_duration {
            return true;
        }
        
        // Don't transition too quickly
        if current_duration < self.min_pattern_duration {
            return false;
        }
        
        // Check various transition triggers
        self.check_beat_transition() ||
        self.check_energy_transition() ||
        self.check_mood_transition() ||
        self.check_random_transition()
    }
    
    /// Check for beat-based transition triggers
    fn check_beat_transition(&self) -> bool {
        if self.beat_history.len() < 4 {
            return false;
        }
        
        // Transition on strong beat patterns (every 8 beats)
        let recent_beats: Vec<_> = self.beat_history.iter()
            .filter(|&&time| time.elapsed() < Duration::from_secs(4))
            .collect();
        
        if recent_beats.len() >= 8 {
            // Check if we're at a musical phrase boundary
            let beat_interval = self.bpm / 60.0;
            let phrase_length = beat_interval * 8.0; // 8 beats = 1 phrase
            
            if let Some(&last_beat) = recent_beats.last() {
                let time_since_last = last_beat.elapsed();
                return time_since_last.as_secs_f32() > phrase_length * 0.8;
            }
        }
        
        false
    }
    
    /// Check for energy-based transition triggers
    fn check_energy_transition(&self) -> bool {
        // Transition on significant energy changes
        let _energy_threshold = 0.3;
        
        // High energy spike
        if self.energy_level > 0.8 {
            return true;
        }
        
        // Energy drop (breakdown)
        if self.energy_level < 0.2 && self.mood != MusicMood::Ambient {
            return true;
        }
        
        false
    }
    
    /// Check for mood-based transition triggers
    fn check_mood_transition(&self) -> bool {
        // Get previous mood from history
        if let Some(last_transition) = self.transition_history.back() {
            let time_since_transition = last_transition.timestamp.elapsed();
            
            // Don't transition too quickly after mood change
            if time_since_transition < Duration::from_secs(10) {
                return false;
            }
        }
        
        // Transition when mood changes significantly
        match self.mood {
            MusicMood::Chaotic => true, // Always transition on chaotic mood
            MusicMood::Energetic => self.energy_level > 0.7,
            MusicMood::Ambient => self.energy_level < 0.3,
            _ => false,
        }
    }
    
    /// Check for random transition triggers
    fn check_random_transition(&self) -> bool {
        use std::collections::hash_map::DefaultHasher;
        use std::hash::{Hash, Hasher};
        
        let mut hasher = DefaultHasher::new();
        Instant::now().elapsed().as_nanos().hash(&mut hasher);
        
        let random_value = (hasher.finish() % 1000) as f32 / 1000.0;
        random_value < self.transition_probability
    }
    
    /// Initiate a new transition
    fn initiate_transition(&mut self) -> Result<()> {
        self.transition_in_progress = true;
        self.transition_start_time = Instant::now();
        
        // Select new pattern and palette
        let new_pattern = self.select_next_pattern()?;
        let new_palette = self.select_next_palette()?;
        let new_color_mode = self.select_next_color_mode()?;
        
        // Record transition
        let transition = TransitionEvent {
            from_pattern: self.current_pattern,
            to_pattern: new_pattern,
            from_palette: self.current_palette,
            to_palette: new_palette,
            trigger: self.determine_transition_trigger(),
            timestamp: Instant::now(),
        };
        
        self.transition_history.push_back(transition);
        if self.transition_history.len() > 20 {
            self.transition_history.pop_front();
        }
        
        // Update current state
        self.current_pattern = new_pattern;
        self.current_palette = new_palette;
        self.current_color_mode = new_color_mode;
        
        // Add to blacklist
        self.add_to_blacklist();
        
        Ok(())
    }
    
    /// Select the next pattern based on current context
    fn select_next_pattern(&self) -> Result<PatternType> {
        let available_patterns = self.get_available_patterns();
        
        // Select based on mood and energy
        let selected = match self.mood {
            MusicMood::Ambient => self.select_ambient_pattern(&available_patterns),
            MusicMood::Energetic => self.select_energetic_pattern(&available_patterns),
            MusicMood::Melodic => self.select_melodic_pattern(&available_patterns),
            MusicMood::Rhythmic => self.select_rhythmic_pattern(&available_patterns),
            MusicMood::Chaotic => self.select_chaotic_pattern(&available_patterns),
        };
        
        Ok(selected)
    }
    
    /// Select ambient patterns (slow, flowing)
    fn select_ambient_pattern(&self, available: &[PatternType]) -> PatternType {
        let ambient_patterns = [
            PatternType::Waves,
            PatternType::Ripples,
            PatternType::Vortex,
            PatternType::Noise,
        ];
        
        self.select_from_preferred(available, &ambient_patterns)
    }
    
    /// Select energetic patterns (fast, dynamic)
    fn select_energetic_pattern(&self, available: &[PatternType]) -> PatternType {
        let energetic_patterns = [
            PatternType::Plasma,
            PatternType::Glitch,
            PatternType::Spiral,
            PatternType::Rings,
        ];
        
        self.select_from_preferred(available, &energetic_patterns)
    }
    
    /// Select melodic patterns (balanced)
    fn select_melodic_pattern(&self, available: &[PatternType]) -> PatternType {
        let melodic_patterns = [
            PatternType::Plasma,
            PatternType::Waves,
            PatternType::Geometric,
            PatternType::Hexagonal,
        ];
        
        self.select_from_preferred(available, &melodic_patterns)
    }
    
    /// Select rhythmic patterns (beat-synchronized)
    fn select_rhythmic_pattern(&self, available: &[PatternType]) -> PatternType {
        let rhythmic_patterns = [
            PatternType::Rings,
            PatternType::Grid,
            PatternType::Diamonds,
            PatternType::Octgrams,
        ];
        
        self.select_from_preferred(available, &rhythmic_patterns)
    }
    
    /// Select chaotic patterns (complex, unpredictable)
    fn select_chaotic_pattern(&self, available: &[PatternType]) -> PatternType {
        let chaotic_patterns = [
            PatternType::Fractal,
            PatternType::Voronoi,
            PatternType::Truchet,
            PatternType::WarpedFbm,
        ];
        
        self.select_from_preferred(available, &chaotic_patterns)
    }
    
    /// Select from preferred patterns, fallback to random
    fn select_from_preferred(&self, available: &[PatternType], preferred: &[PatternType]) -> PatternType {
        // Find intersection of available and preferred
        let mut candidates: Vec<PatternType> = available.iter()
            .filter(|&&pattern| preferred.contains(&pattern))
            .copied()
            .collect();
        
        if candidates.is_empty() {
            // Fallback to any available pattern
            candidates = available.to_vec();
        }
        
        // Select randomly from candidates
        use std::collections::hash_map::DefaultHasher;
        use std::hash::{Hash, Hasher};
        
        let mut hasher = DefaultHasher::new();
        Instant::now().elapsed().as_nanos().hash(&mut hasher);
        
        let index = (hasher.finish() as usize) % candidates.len();
        candidates[index]
    }
    
    /// Get patterns not currently blacklisted
    fn get_available_patterns(&self) -> Vec<PatternType> {
        let all_patterns = [
            PatternType::Plasma,
            PatternType::Waves,
            PatternType::Ripples,
            PatternType::Vortex,
            PatternType::Noise,
            PatternType::Geometric,
            PatternType::Voronoi,
            PatternType::Truchet,
            PatternType::Hexagonal,
            PatternType::Interference,
            PatternType::Fractal,
            PatternType::Glitch,
            PatternType::Spiral,
            PatternType::Rings,
            PatternType::Grid,
            PatternType::Diamonds,
            PatternType::Sphere,
            PatternType::Octgrams,
            PatternType::WarpedFbm,
        ];
        
        all_patterns.iter()
            .filter(|&&pattern| !self.is_blacklisted(&format!("{:?}", pattern)))
            .copied()
            .collect()
    }
    
    /// Select next palette based on mood and pattern
    fn select_next_palette(&self) -> Result<PaletteType> {
        let available_palettes = self.get_available_palettes();
        
        // Select based on mood
        let selected = match self.mood {
            MusicMood::Ambient => PaletteType::Smooth,
            MusicMood::Energetic => PaletteType::Blocks,
            MusicMood::Melodic => PaletteType::Standard,
            MusicMood::Rhythmic => PaletteType::Geometric,
            MusicMood::Chaotic => PaletteType::Braille,
        };
        
        // If selected is not available, pick any available
        if available_palettes.contains(&selected) {
            Ok(selected)
        } else {
            Ok(available_palettes[0])
        }
    }
    
    /// Get palettes not currently blacklisted
    fn get_available_palettes(&self) -> Vec<PaletteType> {
        let all_palettes = [
            PaletteType::Standard,
            PaletteType::Blocks,
            PaletteType::Circles,
            PaletteType::Smooth,
            PaletteType::Braille,
            PaletteType::Geometric,
            PaletteType::Mixed,
            PaletteType::Dots,
            PaletteType::Shades,
            PaletteType::Lines,
            PaletteType::Triangles,
            PaletteType::Arrows,
            PaletteType::Powerline,
            PaletteType::BoxDraw,
            PaletteType::Extended,
            PaletteType::Simple,
        ];
        
        all_palettes.iter()
            .filter(|&&palette| !self.is_blacklisted(&format!("{:?}", palette)))
            .copied()
            .collect()
    }
    
    /// Select next color mode based on mood
    fn select_next_color_mode(&self) -> Result<ColorMode> {
        match self.mood {
            MusicMood::Ambient => Ok(ColorMode::Cool),
            MusicMood::Energetic => Ok(ColorMode::Neon),
            MusicMood::Melodic => Ok(ColorMode::Rainbow),
            MusicMood::Rhythmic => Ok(ColorMode::Cyberpunk),
            MusicMood::Chaotic => Ok(ColorMode::Warped),
        }
    }
    
    /// Update transition morphing state
    fn update_transition_state(&mut self) -> Result<()> {
        if !self.transition_in_progress {
            self.morph_factor = 0.0;
            return Ok(());
        }
        
        let elapsed = self.transition_start_time.elapsed();
        
        if elapsed >= self.transition_duration {
            // Transition complete
            self.transition_in_progress = false;
            self.morph_factor = 1.0;
        } else {
            // Calculate morph factor (smooth easing)
            let progress = elapsed.as_secs_f32() / self.transition_duration.as_secs_f32();
            self.morph_factor = self.ease_in_out_cubic(progress);
        }
        
        Ok(())
    }
    
    /// Smooth easing function for transitions
    fn ease_in_out_cubic(&self, t: f32) -> f32 {
        if t < 0.5 {
            4.0 * t * t * t
        } else {
            let f = 2.0 * t - 2.0;
            1.0 + f * f * f / 2.0
        }
    }
    
    /// Check if a pattern/palette is blacklisted
    fn is_blacklisted(&self, name: &str) -> bool {
        if let Some(&blacklist_time) = self.pattern_blacklist.get(name) {
            blacklist_time.elapsed() < self.blacklist_duration
        } else {
            false
        }
    }
    
    /// Add current pattern/palette to blacklist
    fn add_to_blacklist(&mut self) {
        let now = Instant::now();
        self.pattern_blacklist.insert(format!("{:?}", self.current_pattern), now);
        self.palette_blacklist.insert(format!("{:?}", self.current_palette), now);
        
        // Clean old entries
        self.pattern_blacklist.retain(|_, &mut time| now.elapsed() < self.blacklist_duration);
        self.palette_blacklist.retain(|_, &mut time| now.elapsed() < self.blacklist_duration);
    }
    
    /// Determine what triggered the current transition
    fn determine_transition_trigger(&self) -> TransitionTrigger {
        if self.check_beat_transition() {
            TransitionTrigger::BeatDetected
        } else if self.check_energy_transition() {
            TransitionTrigger::EnergyChange
        } else if self.check_mood_transition() {
            TransitionTrigger::MoodChange
        } else {
            TransitionTrigger::Random
        }
    }
    
    /// Get intelligent parameter randomization based on mood (EXPLOSIVE reactivity)
    pub fn get_randomized_params(&self, base_params: &ShaderParams) -> ShaderParams {
        let mut params = base_params.clone();
        
        // EXPLOSIVE time-based variation
        let time = std::time::Instant::now().elapsed().as_secs_f32();
        
        match self.mood {
            MusicMood::Ambient => {
                // EXPLOSIVE gentle variations with dramatic pulsing
                let pulse = 0.5 + 0.8 * (2.0 * std::f32::consts::PI * 0.3 * time).sin().abs();
                let wave = 1.0 + 0.5 * (2.0 * std::f32::consts::PI * 0.1 * time).sin();
                params.frequency *= pulse * wave;
                params.speed *= 0.2 + (self.energy_level * 0.6) * pulse;
                params.amplitude *= 0.4 + (self.energy_level * 1.2) * pulse;
                params.brightness *= pulse;
                params.contrast *= wave;
            },
            MusicMood::Energetic => {
                // EXPLOSIVE fast variations with beat synchronization
                let beat_pulse = 1.0 + 1.0 * (2.0 * std::f32::consts::PI * 3.0 * time).sin().abs();
                let explosion = 1.0 + 0.8 * (2.0 * std::f32::consts::PI * 0.2 * time).sin();
                params.frequency *= 1.5 + (self.energy_level * 1.0) * beat_pulse;
                params.speed *= 1.0 + (self.energy_level * 0.8) * beat_pulse;
                params.amplitude *= 1.2 + (self.energy_level * 1.0) * beat_pulse;
                params.contrast *= beat_pulse * explosion;
                params.saturation *= explosion;
            },
            MusicMood::Melodic => {
                // EXPLOSIVE balanced variations with harmonic modulation
                let harmonic = 0.8 + 0.6 * (2.0 * std::f32::consts::PI * 0.8 * time).sin().abs();
                let melody_wave = 1.0 + 0.4 * (2.0 * std::f32::consts::PI * 0.3 * time).sin();
                params.frequency *= harmonic;
                params.speed *= 0.4 + (self.energy_level * 0.5) * melody_wave;
                params.amplitude *= 0.6 + (self.energy_level * 0.8) * harmonic;
                params.saturation *= harmonic * melody_wave;
                params.brightness *= melody_wave;
            },
            MusicMood::Rhythmic => {
                // EXPLOSIVE beat-synchronized variations
                let rhythm = 1.0 + 0.8 * (2.0 * std::f32::consts::PI * 2.0 * time).sin().abs();
                let beat_wave = 1.0 + 0.6 * (2.0 * std::f32::consts::PI * 0.5 * time).sin();
                params.frequency *= 1.2 + (self.energy_level * 0.6) * rhythm;
                params.speed *= 0.8 + (self.energy_level * 0.4) * rhythm;
                params.amplitude *= 1.0 + (self.energy_level * 0.6) * rhythm;
                params.scale *= rhythm * beat_wave;
                params.contrast *= beat_wave;
            },
            MusicMood::Chaotic => {
                // EXPLOSIVE extreme, unpredictable variations
                let chaos = 0.3 + 1.4 * (2.0 * std::f32::consts::PI * 5.0 * time).sin().abs();
                let madness = 1.0 + 0.8 * (2.0 * std::f32::consts::PI * 0.1 * time).sin();
                params.frequency *= chaos;
                params.speed *= 0.1 + (self.energy_level * 1.2) * chaos;
                params.amplitude *= 0.2 + (self.energy_level * 2.0) * chaos;
                params.distort_amplitude *= chaos * madness;
                params.noise_strength *= madness;
            },
        }
        
        // EXPLOSIVE global dynamic effects
        let global_pulse = 1.0 + 0.6 * (2.0 * std::f32::consts::PI * 1.5 * time).sin().abs();
        let global_wave = 1.0 + 0.3 * (2.0 * std::f32::consts::PI * 0.2 * time).sin();
        params.brightness *= global_pulse;
        params.contrast *= global_wave;
        
        // EXPLOSIVE energy-driven effects
        if self.energy_level > 0.6 {
            params.contrast *= 2.0;
            params.saturation *= 1.8;
            params.amplitude *= 1.5;
        }
        
        // EXPLOSIVE burst effects
        let burst = if (time % 1.0) > 0.95 { 2.0 } else { 1.0 }; // Burst every second
        params.frequency *= burst;
        params.speed *= burst;
        
        params
    }
}

/// Current VJ state for rendering
#[derive(Debug, Clone)]
pub struct VJState {
    pub pattern: PatternType,
    pub palette: PaletteType,
    pub color_mode: ColorMode,
    pub morph_factor: f32,
    pub energy_level: f32,
    pub mood: MusicMood,
    pub bpm: f32,
}
