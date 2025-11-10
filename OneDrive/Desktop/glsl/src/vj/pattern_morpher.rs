use anyhow::Result;
use std::time::{Duration, Instant};
use crate::params::{PatternType, ShaderParams};

/// Cross-Pattern Morphing Engine
/// 
/// Handles smooth transitions between different shader patterns using:
/// - GPU-accelerated interpolation
/// - Parameter blending
/// - Visual continuity preservation
pub struct PatternMorpher {
    // Morphing state
    morphing: bool,
    morph_start_time: Instant,
    morph_duration: Duration,
    morph_progress: f32,
    
    // Source and target states
    source_pattern: PatternType,
    target_pattern: PatternType,
    source_params: ShaderParams,
    target_params: ShaderParams,
    
    // Morphing configuration
    morph_types: Vec<MorphType>,
    current_morph_type: MorphType,
    
    // Performance optimization
    interpolation_cache: Vec<f32>,
    cache_size: usize,
}

#[derive(Debug, Clone, Copy, PartialEq)]
pub enum MorphType {
    Linear,           // Simple linear interpolation
    Smooth,           // Smooth easing (cubic)
    BeatSync,         // Beat-synchronized morphing
    EnergyDriven,     // Energy-based morphing speed
    TempoSync,        // Tempo-synchronized morphing
}

impl PatternMorpher {
    /// Create a new pattern morpher
    pub fn new() -> Self {
        Self {
            morphing: false,
            morph_start_time: Instant::now(),
            morph_duration: Duration::from_millis(2000),
            morph_progress: 0.0,
            
            source_pattern: PatternType::Plasma,
            target_pattern: PatternType::Plasma,
            source_params: ShaderParams::default(),
            target_params: ShaderParams::default(),
            
            morph_types: vec![
                MorphType::Smooth,
                MorphType::BeatSync,
                MorphType::EnergyDriven,
                MorphType::TempoSync,
            ],
            current_morph_type: MorphType::Smooth,
            
            interpolation_cache: Vec::new(),
            cache_size: 1024,
        }
    }
    
    /// Start morphing between two patterns
    pub fn start_morph(
        &mut self,
        from_pattern: PatternType,
        to_pattern: PatternType,
        from_params: ShaderParams,
        to_params: ShaderParams,
        morph_type: Option<MorphType>,
        duration: Option<Duration>,
    ) -> Result<()> {
        self.morphing = true;
        self.morph_start_time = Instant::now();
        self.morph_duration = duration.unwrap_or(Duration::from_millis(2000));
        self.morph_progress = 0.0;
        
        self.source_pattern = from_pattern;
        self.target_pattern = to_pattern;
        self.source_params = from_params;
        self.target_params = to_params;
        
        self.current_morph_type = morph_type.unwrap_or(MorphType::Smooth);
        
        // Pre-calculate interpolation values for performance
        self.precalculate_interpolation()?;
        
        Ok(())
    }
    
    /// Update morphing progress
    pub fn update_morph(&mut self, bpm: f32, energy: f32, beat_detected: bool) -> Result<f32> {
        if !self.morphing {
            return Ok(1.0);
        }
        
        let elapsed = self.morph_start_time.elapsed();
        
        // Calculate base progress
        let base_progress = elapsed.as_secs_f32() / self.morph_duration.as_secs_f32();
        
        // Apply morphing type-specific adjustments
        let adjusted_progress = match self.current_morph_type {
            MorphType::Linear => base_progress,
            MorphType::Smooth => self.smooth_easing(base_progress),
            MorphType::BeatSync => self.beat_sync_morphing(base_progress, beat_detected),
            MorphType::EnergyDriven => self.energy_driven_morphing(base_progress, energy),
            MorphType::TempoSync => self.tempo_sync_morphing(base_progress, bpm),
        };
        
        self.morph_progress = adjusted_progress.clamp(0.0, 1.0);
        
        // Check if morphing is complete
        if self.morph_progress >= 1.0 {
            self.morphing = false;
            self.morph_progress = 1.0;
        }
        
        Ok(self.morph_progress)
    }
    
    /// Get morphed shader parameters
    pub fn get_morphed_params(&self) -> ShaderParams {
        if !self.morphing {
            return self.target_params.clone();
        }
        
        let mut morphed = self.source_params.clone();
        
        // Interpolate each parameter
        morphed.frequency = self.interpolate(
            self.source_params.frequency,
            self.target_params.frequency,
            self.morph_progress,
        );
        
        morphed.amplitude = self.interpolate(
            self.source_params.amplitude,
            self.target_params.amplitude,
            self.morph_progress,
        );
        
        morphed.speed = self.interpolate(
            self.source_params.speed,
            self.target_params.speed,
            self.morph_progress,
        );
        
        morphed.scale = self.interpolate(
            self.source_params.scale,
            self.target_params.scale,
            self.morph_progress,
        );
        
        morphed.brightness = self.interpolate(
            self.source_params.brightness,
            self.target_params.brightness,
            self.morph_progress,
        );
        
        morphed.contrast = self.interpolate(
            self.source_params.contrast,
            self.target_params.contrast,
            self.morph_progress,
        );
        
        morphed.saturation = self.interpolate(
            self.source_params.saturation,
            self.target_params.saturation,
            self.morph_progress,
        );
        
        morphed.hue = self.interpolate_hue(
            self.source_params.hue,
            self.target_params.hue,
            self.morph_progress,
        );
        
        morphed.noise_strength = self.interpolate(
            self.source_params.noise_strength,
            self.target_params.noise_strength,
            self.morph_progress,
        );
        
        morphed.distort_amplitude = self.interpolate(
            self.source_params.distort_amplitude,
            self.target_params.distort_amplitude,
            self.morph_progress,
        );
        
        morphed.vignette = self.interpolate(
            self.source_params.vignette,
            self.target_params.vignette,
            self.morph_progress,
        );
        
        morphed
    }
    
    /// Get current pattern (morphed between source and target)
    pub fn get_current_pattern(&self) -> PatternType {
        if !self.morphing {
            return self.target_pattern;
        }
        
        // For now, return target pattern when morphing
        // In a full implementation, this could blend between shaders
        self.target_pattern
    }
    
    /// Check if currently morphing
    pub fn is_morphing(&self) -> bool {
        self.morphing
    }
    
    /// Get morph progress (0.0 to 1.0)
    pub fn get_morph_progress(&self) -> f32 {
        self.morph_progress
    }
    
    /// Smooth easing function (cubic)
    fn smooth_easing(&self, t: f32) -> f32 {
        if t < 0.5 {
            4.0 * t * t * t
        } else {
            let f = 2.0 * t - 2.0;
            1.0 + f * f * f / 2.0
        }
    }
    
    /// Beat-synchronized morphing
    fn beat_sync_morphing(&self, base_progress: f32, beat_detected: bool) -> f32 {
        if beat_detected {
            // Accelerate morphing on beats
            base_progress * 1.2
        } else {
            // Slow down between beats
            base_progress * 0.8
        }
    }
    
    /// Energy-driven morphing
    fn energy_driven_morphing(&self, base_progress: f32, energy: f32) -> f32 {
        // Higher energy = faster morphing
        let energy_factor = 0.5 + energy * 1.0;
        base_progress * energy_factor
    }
    
    /// Tempo-synchronized morphing
    fn tempo_sync_morphing(&self, base_progress: f32, bpm: f32) -> f32 {
        // Adjust morphing speed based on tempo
        let tempo_factor = (bpm / 120.0).clamp(0.5, 2.0);
        base_progress * tempo_factor
    }
    
    /// Interpolate between two values
    fn interpolate(&self, from: f32, to: f32, t: f32) -> f32 {
        from + (to - from) * t
    }
    
    /// Interpolate hue values (handles wraparound)
    fn interpolate_hue(&self, from: f32, to: f32, t: f32) -> f32 {
        let diff = to - from;
        
        // Handle hue wraparound (0-360 degrees)
        if diff > 180.0 {
            from + (diff - 360.0) * t
        } else if diff < -180.0 {
            from + (diff + 360.0) * t
        } else {
            from + diff * t
        }
    }
    
    /// Pre-calculate interpolation values for performance
    fn precalculate_interpolation(&mut self) -> Result<()> {
        self.interpolation_cache.clear();
        self.interpolation_cache.reserve(self.cache_size);
        
        for i in 0..self.cache_size {
            let t = i as f32 / (self.cache_size - 1) as f32;
            let interpolated = self.smooth_easing(t);
            self.interpolation_cache.push(interpolated);
        }
        
        Ok(())
    }
    
    /// Get cached interpolation value
    fn get_cached_interpolation(&self, t: f32) -> f32 {
        if self.interpolation_cache.is_empty() {
            return t;
        }
        
        let index = (t * (self.cache_size - 1) as f32) as usize;
        let clamped_index = index.clamp(0, self.cache_size - 1);
        
        self.interpolation_cache[clamped_index]
    }
    
    /// Stop morphing immediately
    pub fn stop_morphing(&mut self) {
        self.morphing = false;
        self.morph_progress = 1.0;
    }
    
    /// Set morphing duration
    pub fn set_morph_duration(&mut self, duration: Duration) {
        self.morph_duration = duration;
    }
    
    /// Get available morph types
    pub fn get_available_morph_types(&self) -> &[MorphType] {
        &self.morph_types
    }
    
    /// Set morph type for next morph
    pub fn set_morph_type(&mut self, morph_type: MorphType) {
        self.current_morph_type = morph_type;
    }
}

impl Default for PatternMorpher {
    fn default() -> Self {
        Self::new()
    }
}
