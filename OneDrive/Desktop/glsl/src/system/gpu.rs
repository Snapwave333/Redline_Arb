//! GPU metrics provider with optional integrations
//! If vendor APIs are available (via features), returns real GPU load/VRAM.
//! Otherwise returns None and callers should fallback to simulated metrics.

// NVML (NVIDIA)
#[cfg(feature = "nvml")]
use nvml_wrapper::Nvml;

// NVIDIA via NVML
#[cfg(feature = "nvml")]
fn try_get_gpu_load_nvml() -> Option<f32> {
    let nvml = Nvml::init().ok()?;
    let device = nvml.device_by_index(0).ok()?;
    let util = device.utilization_rates().ok()?;
    Some(util.gpu as f32)
}

#[cfg(not(feature = "nvml"))]
fn try_get_gpu_load_nvml() -> Option<f32> { None }

#[cfg(feature = "nvml")]
fn try_get_vram_usage_mb_nvml() -> Option<(f32, f32)> {
    let nvml = Nvml::init().ok()?;
    let device = nvml.device_by_index(0).ok()?;
    let mem = device.memory_info().ok()?; // bytes
    let used_mb = (mem.used as f32) / (1024.0 * 1024.0);
    let total_mb = (mem.total as f32) / (1024.0 * 1024.0);
    Some((used_mb, total_mb))
}

#[cfg(not(feature = "nvml"))]
fn try_get_vram_usage_mb_nvml() -> Option<(f32, f32)> { None }

// AMD fallback (stub)
#[cfg(feature = "amd")]
fn try_get_gpu_load_amd() -> Option<f32> {
    // TODO: implement via ADL/ROCm/Windows counters
    None
}
#[cfg(not(feature = "amd"))]
fn try_get_gpu_load_amd() -> Option<f32> { None }

#[cfg(feature = "amd")]
fn try_get_vram_usage_mb_amd() -> Option<(f32, f32)> {
    // TODO: implement via ADL/ROCm/Windows counters
    None
}
#[cfg(not(feature = "amd"))]
fn try_get_vram_usage_mb_amd() -> Option<(f32, f32)> { None }

// Intel fallback (stub)
#[cfg(feature = "intel")]
fn try_get_gpu_load_intel() -> Option<f32> {
    // TODO: implement via DXGI/WMI/Windows counters
    None
}
#[cfg(not(feature = "intel"))]
fn try_get_gpu_load_intel() -> Option<f32> { None }

#[cfg(feature = "intel")]
fn try_get_vram_usage_mb_intel() -> Option<(f32, f32)> {
    // TODO: implement via DXGI/WMI/Windows counters
    None
}
#[cfg(not(feature = "intel"))]
fn try_get_vram_usage_mb_intel() -> Option<(f32, f32)> { None }

/// Try to get GPU load as percentage (0..100)
pub fn try_get_gpu_load() -> Option<f32> {
    // Prefer NVML, then AMD, then Intel
    if let Some(val) = try_get_gpu_load_nvml() { return Some(val); }
    if let Some(val) = try_get_gpu_load_amd() { return Some(val); }
    if let Some(val) = try_get_gpu_load_intel() { return Some(val); }
    None
}

/// Try to get VRAM usage in megabytes (used, total)
pub fn try_get_vram_usage_mb() -> Option<(f32, f32)> {
    // Prefer NVML, then AMD, then Intel
    if let Some(val) = try_get_vram_usage_mb_nvml() { return Some(val); }
    if let Some(val) = try_get_vram_usage_mb_amd() { return Some(val); }
    if let Some(val) = try_get_vram_usage_mb_intel() { return Some(val); }
    None
}