pub mod macro_state_engine;
pub mod bpm_detector;
pub mod pattern_morpher;
pub mod autonomous_startup;
pub mod advanced_audio_analyzer;
pub mod creative_expansion_engine;
pub mod rust_autonomy_engine;
pub mod visual_orchestrator;
pub mod orchestrator_integration;

pub use macro_state_engine::{MacroStateEngine, VJState, MusicMood, TransitionEvent, TransitionTrigger};
pub use bpm_detector::{BPMDetector, BPMResult};
pub use pattern_morpher::{PatternMorpher, MorphType};
pub use autonomous_startup::{AutonomousStartup, StartupPhase, StartupUpdate};
pub use advanced_audio_analyzer::{
    AdvancedAudioAnalyzer, AudioAnalysisResult, SpectralAnalysis, BeatAnalysis, 
    SilenceAnalysis, GenreAnalysis, VisualState, MoodEngine, EmotionalTone, GenreType,
    GenreFeatures
};
pub use creative_expansion_engine::{
    CreativeExpansionEngine, VisualStyle, SynesthesiaMappings, CulturalOrigin,
    FractalGenerator, CellularAutomata, WaveformSculptor, MandalaGenerator,
    TribalPatterns, CyberpunkGlyphs, StyleMorpher, MoodTransitions, VisualMemory,
    AudioContext
};
pub use visual_orchestrator::{
    VisualOrchestrator, OrchestratorUpdate, VisualPerformance, VisualStory, StoryPhase,
    VisualMood, ColorScheme, VisualEffect, EffectTrigger, EffectParameters, Transition,
    TransitionType, EasingFunction, TransitionParameters, AudioContext as OrchestratorAudioContext, MusicGenre,
    GenreClassifier, EnergyAnalyzer, PeakDetector, ValleyDetector, PerformancePlanner,
    VisualSequence, TransitionManager, ActiveTransition, VisualState as OrchestratorVisualState, EffectCoordinator,
    ActiveEffect, ColorDirector, ColorHarmony, PerformanceMetrics, NarrativeArc,
    SpectralAnalysis as OrchestratorSpectralAnalysis
};
pub use orchestrator_integration::{
    OrchestratorIntegration, PerformanceMode, IntegrationState, PendingTransition,
    TransitionPriority, ActiveEffectState, PerformanceMetrics as IntegrationMetrics,
    AudioAnalysisSnapshot, OrchestratorIntegrationResult, OrchestratorState,
    OrchestratorOverride, PatternOverride, ColorOverride, EffectOverride, TransitionOverride,
    OrchestratorSuggestion, SuggestionType, SuggestionPriority
};
