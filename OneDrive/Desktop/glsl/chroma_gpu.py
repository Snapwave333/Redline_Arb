







###############################################################
# CHROMA VJ AUTONOMOUS CINEMATIC ROADMAP (VERSION 1.0)
# Goal: To create a fully autonomous, non-customizable, virtual VJ
#       (Video Jockey) that runs a compelling 2.5-3 hour performance
#       driven entirely by advanced musical analysis.
#
# Note: All features must be implemented without a traditional GUI,
#       relying on the existing terminal framework.
###############################################################

## I. AUTONOMOUS VJ CORE LOGIC (MASTER PERFORMANCE SEQUENCER - MPS)

1.  **Master Performance Sequencer (MPS):** The central state machine managing the 2.5-3 hour runtime, ensuring structured progression and dramatic arcs.
2.  **Thematic Acts:** Define 3-5 distinct "Acts" (e.g., Genesis, Conflict, Resolution) for the performance, with the MPS managing the time budget and general intensity of each Act.
3.  **Cross-Pattern Morphing:** Implement GPU-accelerated transition logic to smoothly morph between two entirely different shaders (e.g., Plasma to Voronoi) over a short, tempo-synchronized duration.
4.  **Intelligent Auto-Randomization Scope:** Automatically choose a subset of parameters to randomize based on the current musical 'mood' or 'energy' detected by the audio.
5.  **Pattern Blacklist Aging:** Patterns used early in the set (Act I) gain a higher probability of being reused in the final act (Act III) for a sense of visual history and callback.
6.  **"Sleeper" Uniforms:** For complex shaders, the MPS will keep a key uniform near zero for a long period (e.g., 30+ minutes) before dramatically increasing it, revealing a hidden visual over time.
7.  **The "Finale" Cue:** Program the last 5 minutes to engage a locked sequence of the most complex pattern chains and maximum BPM sensitivity for a high-impact conclusion.

## II. ADVANCED AUDIO ANALYSIS (THE VJ ENGINE)

8.  **Tempo/BPM Detection & Synchronization:** Crucially detect the music's BPM and use it to precisely time all transitions, speed settings, and animation cycles.
9.  **Advanced Beat Mapping:** Differentiate and track specific rhythmic elements (Kick, Snare, Hi-Hat) to allow for granular visual reactions tied to different percussion layers.
10. **Frequency Band Mapping (Intelligent):** Automatically map the main bands (Bass, Mid, Treble) to the most visually effective shader uniform for the currently active pattern.
11. **Musical Energy/Mood Detection:** Analyze the audio to determine the overall energy (loudness, complexity) and emotional mood (major/minor key bias) to drive major visual theme shifts.
12. **Pitch/Key Mood Shift:** Bias color palette selection towards Warm/Pastel/Rainbow for Major keys and Cool/Cyberpunk for Minor keys.
13. **"Density" Meter:** Track the **harmonic and rhythmic complexity** of the music. This value controls the switch between simple (Standard) and complex (Braille) ASCII palettes.
14. **Silence/Sustained Note Cue:** Trigger a dramatic, sudden switch to a monochrome, slow-moving "Stasis" pattern (minimal speed/color) upon detection of near-silence or a long, sustained note.
15. **Audio Noise Gate:** A configured threshold to ignore low-level noise or quiet audio input, ensuring the visuals only react to meaningful musical content.

## III. VJ VISUAL REFINEMENTS & STABILITY

16. **Braille ASCII Density:** Implement the highly granular Braille character set to significantly improve the apparent visual resolution and detail.
17. **Shader Chaining/Layering (Automated):** Automatically load multiple shaders, and have the MPS determine the blend mode and weight between them.
18. **Gradient/Ramp Support (Dynamic):** Allow the MPS to dynamically generate multi-point color gradients to replace/supplement fixed color modes, enabling infinitely varied color schemes.
19. **The "Lens" Filter:** Implement a universal, automated filter (e.g., oscillating chromatic aberration or subtle digital glitch) applied over the final output to give the entire performance a cohesive visual signature.
20. **Dynamic Color Inversion:** Trigger a momentary, full-screen color inversion during very sharp, loud percussive hits for a "flashbulb" effect.
21. **New Visual Pattern: Reaction-Diffusion:** Add this complex, organic pattern type to the autonomous pool for dramatic, evolving visuals.
22. **WGPU Buffer Pipelining:** Crucial low-level optimization to ensure the demanding GPU computations run smoothly and maintain high frame rates.
23. **Shader Caching:** Pre-compile common shaders to minimize the delay when the MPS calls for a new pattern.
24. **Autonomous Startup Sequence:** Running the simple command `chroma` automatically selects the audio device, detects BPM, and synchronizes the first major visual drop with the music.

## IV. FUTURISTIC VJ ODOMETER STATUS BAR

**Goal:** Implement a sleek, single-row, non-interactive diagnostic display at the bottom of the terminal in a "Cyberpunk/Tron" style.

**Aesthetic:** Glowing Electric Cyan/Neon Pink digits on a dark background, framed by sharp box drawing characters (`│`, `─`).

**Metrics (Displayed in Framed Pods):**

25. **FPS (Frames Per Second):** Displays the rendering speed (e.g., `[::FPS::] 120`).
26. **GPU (GPU Load):** Displays system GPU percentage (e.g., `[::GPU::] 75%`). Includes a color-shift alert to **Bright Red** if load exceeds 90%.
27. **RAM (Memory Usage):** Displays system memory used (e.g., `[::RAM::] 2.1G`).
28. **BPM (Beats Per Minute):** Displays the detected musical tempo (e.g., `[::BPM::] 128`). The digit should subtly brighten or 'pulse' in time with the detected beat.
29. **Implementation Constraint 1 (Non-Interactive):** The entire status bar must be display-only; no user input is allowed.
30. **Implementation Constraint 2 (Toggle):** A simple keybind (e.g., `H`) toggles the visibility of the entire diagnostic strip.