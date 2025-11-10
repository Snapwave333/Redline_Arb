use anyhow::Result;
use std::collections::VecDeque;
use std::time::{Duration, Instant};

/// BPM Detection Engine
/// 
/// Analyzes audio input to detect beats per minute using various algorithms:
/// - Onset detection for beat timing
/// - Autocorrelation for tempo estimation
/// - Beat tracking for BPM calculation
pub struct BPMDetector {
    // Audio analysis
    sample_rate: f32,
    buffer_size: usize,
    audio_buffer: VecDeque<f32>,
    
    // Beat detection
    onset_threshold: f32,
    onset_history: VecDeque<Instant>,
    last_onset_time: Instant,
    
    // BPM calculation
    bpm_history: VecDeque<f32>,
    current_bpm: f32,
    confidence: f32,
    
    // Tempo tracking
    tempo_candidates: Vec<(f32, f32)>, // (bpm, confidence)
    tempo_stability_threshold: f32,
    
    // Configuration
    min_bpm: f32,
    max_bpm: f32,
    analysis_window: Duration,
}

impl BPMDetector {
    /// Create a new BPM detector
    pub fn new(sample_rate: f32) -> Self {
        Self {
            sample_rate,
            buffer_size: (sample_rate * 0.1) as usize, // 100ms buffer
            audio_buffer: VecDeque::with_capacity(1024),
            
            onset_threshold: 0.3,
            onset_history: VecDeque::with_capacity(64),
            last_onset_time: Instant::now(),
            
            bpm_history: VecDeque::with_capacity(16),
            current_bpm: 120.0,
            confidence: 0.0,
            
            tempo_candidates: Vec::new(),
            tempo_stability_threshold: 0.7,
            
            min_bpm: 60.0,
            max_bpm: 200.0,
            analysis_window: Duration::from_secs(8),
        }
    }
    
    /// Process audio samples and detect BPM
    pub fn process_audio(&mut self, samples: &[f32]) -> Result<BPMResult> {
        // Add samples to buffer
        for &sample in samples {
            self.audio_buffer.push_back(sample);
            if self.audio_buffer.len() > self.buffer_size {
                self.audio_buffer.pop_front();
            }
        }
        
        // Detect onsets (beats)
        let onsets = self.detect_onsets()?;
        
        // Update onset history
        for onset_time in &onsets {
            self.onset_history.push_back(*onset_time);
            self.last_onset_time = *onset_time;
        }
        
        // Clean old onsets
        let cutoff_time = Instant::now() - self.analysis_window;
        while let Some(&oldest) = self.onset_history.front() {
            if oldest < cutoff_time {
                self.onset_history.pop_front();
            } else {
                break;
            }
        }
        
        // Calculate BPM from onset intervals
        if self.onset_history.len() >= 4 {
            self.calculate_bpm()?;
        }
        
        Ok(BPMResult {
            bpm: self.current_bpm,
            confidence: self.confidence,
            beat_detected: !onsets.is_empty(),
            tempo_stable: self.confidence > self.tempo_stability_threshold,
        })
    }
    
    /// Detect onset events (beats) in the audio
    fn detect_onsets(&self) -> Result<Vec<Instant>> {
        if self.audio_buffer.len() < 2 {
            return Ok(Vec::new());
        }
        
        let mut onsets = Vec::new();
        let samples: Vec<f32> = self.audio_buffer.iter().copied().collect();
        
        // Calculate spectral flux (energy change)
        let spectral_flux = self.calculate_spectral_flux(&samples)?;
        
        // Detect peaks in spectral flux
        for (i, &flux) in spectral_flux.iter().enumerate() {
            if flux > self.onset_threshold {
                // Check if this is a local maximum
                let is_peak = self.is_local_maximum(&spectral_flux, i);
                
                if is_peak {
                    let time_offset = Duration::from_secs_f32(i as f32 / self.sample_rate);
                    let onset_time = Instant::now() - time_offset;
                    onsets.push(onset_time);
                }
            }
        }
        
        Ok(onsets)
    }
    
    /// Calculate spectral flux for onset detection
    fn calculate_spectral_flux(&self, samples: &[f32]) -> Result<Vec<f32>> {
        let window_size = 512;
        let hop_size = 256;
        let mut flux = Vec::new();
        
        for i in (0..samples.len().saturating_sub(window_size)).step_by(hop_size) {
            let window = &samples[i..i + window_size];
            
            // Apply window function (Hanning)
            let windowed: Vec<f32> = window.iter()
                .enumerate()
                .map(|(j, &sample)| {
                    let window_value = 0.5 * (1.0 - (2.0 * std::f32::consts::PI * j as f32 / (window_size - 1) as f32).cos());
                    sample * window_value
                })
                .collect();
            
            // Calculate magnitude spectrum
            let magnitude = self.calculate_magnitude_spectrum(&windowed)?;
            
            // Calculate spectral flux (sum of positive differences)
            let flux_value = magnitude.iter()
                .zip(magnitude.iter().skip(1))
                .map(|(&curr, &next)| (next - curr).max(0.0))
                .sum::<f32>();
            
            flux.push(flux_value);
        }
        
        Ok(flux)
    }
    
    /// Calculate magnitude spectrum using FFT
    fn calculate_magnitude_spectrum(&self, samples: &[f32]) -> Result<Vec<f32>> {
        // Simple FFT implementation (for production, use a proper FFT library)
        let n = samples.len();
        let mut real: Vec<f32> = samples.to_vec();
        let mut imag = vec![0.0; n];
        
        // Pad to power of 2
        let padded_size = n.next_power_of_two();
        real.resize(padded_size, 0.0);
        imag.resize(padded_size, 0.0);
        
        // Simple DFT (replace with FFT for performance)
        let mut magnitude = Vec::new();
        for k in 0..padded_size / 2 {
            let mut real_sum = 0.0;
            let mut imag_sum = 0.0;
            
            for i in 0..padded_size {
                let angle = -2.0 * std::f32::consts::PI * k as f32 * i as f32 / padded_size as f32;
                real_sum += real[i] * angle.cos();
                imag_sum += real[i] * angle.sin();
            }
            
            let magnitude_value = (real_sum * real_sum + imag_sum * imag_sum).sqrt();
            magnitude.push(magnitude_value);
        }
        
        Ok(magnitude)
    }
    
    /// Check if a point is a local maximum
    fn is_local_maximum(&self, data: &[f32], index: usize) -> bool {
        if index == 0 || index >= data.len() - 1 {
            return false;
        }
        
        let value = data[index];
        let left = data[index - 1];
        let right = data[index + 1];
        
        value > left && value > right
    }
    
    /// Calculate BPM from onset intervals
    fn calculate_bpm(&mut self) -> Result<()> {
        if self.onset_history.len() < 4 {
            return Ok(());
        }
        
        // Calculate intervals between onsets
        let mut intervals = Vec::new();
        let onsets: Vec<Instant> = self.onset_history.iter().copied().collect();
        
        for i in 1..onsets.len() {
            let interval = onsets[i].duration_since(onsets[i - 1]);
            intervals.push(interval.as_secs_f32());
        }
        
        // Find most common interval (tempo)
        let tempo_intervals = self.find_tempo_intervals(&intervals)?;
        
        // Convert intervals to BPM
        let mut bpm_candidates = Vec::new();
        for interval in tempo_intervals {
            let bpm = 60.0 / interval;
            
            // Check if BPM is in valid range
            if bpm >= self.min_bpm && bpm <= self.max_bpm {
                bpm_candidates.push(bpm);
            }
            
            // Also check half-time and double-time
            let half_bpm = bpm / 2.0;
            let double_bpm = bpm * 2.0;
            
            if half_bpm >= self.min_bpm && half_bpm <= self.max_bpm {
                bpm_candidates.push(half_bpm);
            }
            
            if double_bpm >= self.min_bpm && double_bpm <= self.max_bpm {
                bpm_candidates.push(double_bpm);
            }
        }
        
        // Find most stable BPM
        if let Some(best_bpm) = self.find_most_stable_bpm(&bpm_candidates) {
            self.current_bpm = best_bpm;
            self.confidence = self.calculate_confidence(&bpm_candidates, best_bpm);
            
            // Update BPM history
            self.bpm_history.push_back(best_bpm);
            if self.bpm_history.len() > 16 {
                self.bpm_history.pop_front();
            }
        }
        
        Ok(())
    }
    
    /// Find tempo intervals from onset intervals
    fn find_tempo_intervals(&self, intervals: &[f32]) -> Result<Vec<f32>> {
        // Group similar intervals
        let mut groups: Vec<(f32, usize)> = Vec::new();
        
        for &interval in intervals {
            let mut found_group = false;
            
            for (group_interval, count) in &mut groups {
                let ratio = interval / *group_interval;
                if ratio > 0.8 && ratio < 1.2 {
                    *group_interval = (*group_interval * *count as f32 + interval) / (*count + 1) as f32;
                    *count += 1;
                    found_group = true;
                    break;
                }
            }
            
            if !found_group {
                groups.push((interval, 1));
            }
        }
        
        // Return intervals with sufficient support
        let min_support = intervals.len() / 4;
        Ok(groups.iter()
            .filter(|(_, count)| *count >= min_support)
            .map(|(interval, _)| *interval)
            .collect())
    }
    
    /// Find the most stable BPM from candidates
    fn find_most_stable_bpm(&self, candidates: &[f32]) -> Option<f32> {
        if candidates.is_empty() {
            return None;
        }
        
        // Use histogram to find most common BPM
        let mut histogram: std::collections::HashMap<i32, usize> = std::collections::HashMap::new();
        
        for &bpm in candidates {
            let rounded = (bpm.round() as i32).clamp(60, 200);
            *histogram.entry(rounded).or_insert(0) += 1;
        }
        
        // Find BPM with highest count
        histogram.iter()
            .max_by_key(|(_, &count)| count)
            .map(|(&bpm, _)| bpm as f32)
    }
    
    /// Calculate confidence in BPM detection
    fn calculate_confidence(&self, candidates: &[f32], target_bpm: f32) -> f32 {
        if candidates.is_empty() {
            return 0.0;
        }
        
        // Count how many candidates are close to target BPM
        let tolerance = 5.0; // ±5 BPM tolerance
        let close_count = candidates.iter()
            .filter(|&&bpm| (bpm - target_bpm).abs() <= tolerance)
            .count();
        
        close_count as f32 / candidates.len() as f32
    }
    
    /// Get current BPM
    pub fn get_bpm(&self) -> f32 {
        self.current_bpm
    }
    
    /// Get confidence in current BPM
    pub fn get_confidence(&self) -> f32 {
        self.confidence
    }
    
    /// Check if tempo is stable
    pub fn is_tempo_stable(&self) -> bool {
        self.confidence > self.tempo_stability_threshold
    }
    
    /// Reset the detector
    pub fn reset(&mut self) {
        self.audio_buffer.clear();
        self.onset_history.clear();
        self.bpm_history.clear();
        self.tempo_candidates.clear();
        self.current_bpm = 120.0;
        self.confidence = 0.0;
    }
}

/// Result of BPM detection
#[derive(Debug, Clone)]
pub struct BPMResult {
    pub bpm: f32,
    pub confidence: f32,
    pub beat_detected: bool,
    pub tempo_stable: bool,
}
