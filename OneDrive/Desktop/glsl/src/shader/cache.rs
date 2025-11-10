use anyhow::Result;
use std::collections::HashMap;
use std::fs;
use std::path::Path;
use std::sync::Arc;
use wgpu::{ComputePipeline, Device};

/// Shader cache for pre-compiled compute pipelines
pub struct ShaderCache {
    device: Arc<Device>,
    cache_dir: std::path::PathBuf,
    pipelines: HashMap<String, Arc<ComputePipeline>>,
}

impl ShaderCache {
    /// Create a new shader cache
    pub fn new(device: Arc<Device>) -> Self {
        let cache_dir = dirs::cache_dir()
            .unwrap_or_else(|| std::env::temp_dir())
            .join("chroma")
            .join("shader_cache");

        // Ensure cache directory exists
        if let Err(e) = fs::create_dir_all(&cache_dir) {
            eprintln!("Warning: Failed to create shader cache directory: {}", e);
        }

        Self {
            device,
            cache_dir,
            pipelines: HashMap::new(),
        }
    }

    /// Get or compile a compute pipeline
    pub fn get_or_compile_pipeline(
        &mut self,
        shader_source: &str,
        entry_point: &str,
        label: Option<&str>,
    ) -> Result<Arc<ComputePipeline>> {
        let cache_key = self.generate_cache_key(shader_source, entry_point);
        
        // Check if pipeline is already in memory
        if let Some(pipeline) = self.pipelines.get(&cache_key) {
            return Ok(pipeline.clone());
        }

        // Check if compiled shader exists on disk
        let cache_file = self.cache_dir.join(format!("{}.wgsl", cache_key));
        if cache_file.exists() {
            if let Ok(pipeline) = self.load_pipeline_from_cache(&cache_file, entry_point, label) {
                self.pipelines.insert(cache_key.clone(), pipeline.clone());
                return Ok(pipeline);
            }
        }

        // Compile new pipeline
        let pipeline = self.compile_pipeline(shader_source, entry_point, label)?;
        
        // Save to cache
        if let Err(e) = self.save_pipeline_to_cache(&cache_file, shader_source) {
            eprintln!("Warning: Failed to save shader to cache: {}", e);
        }

        self.pipelines.insert(cache_key, pipeline.clone());
        Ok(pipeline)
    }

    /// Generate a cache key for the shader
    fn generate_cache_key(&self, shader_source: &str, entry_point: &str) -> String {
        use std::collections::hash_map::DefaultHasher;
        use std::hash::{Hash, Hasher};
        
        let mut hasher = DefaultHasher::new();
        shader_source.hash(&mut hasher);
        entry_point.hash(&mut hasher);
        format!("{:x}", hasher.finish())
    }

    /// Compile a compute pipeline from source
    fn compile_pipeline(
        &self,
        shader_source: &str,
        entry_point: &str,
        label: Option<&str>,
    ) -> Result<Arc<ComputePipeline>> {
        let shader_module = self.device.create_shader_module(wgpu::ShaderModuleDescriptor {
            label,
            source: wgpu::ShaderSource::Wgsl(shader_source.into()),
        });

        let pipeline_layout = self.device.create_pipeline_layout(&wgpu::PipelineLayoutDescriptor {
            label: Some("Compute Pipeline Layout"),
            bind_group_layouts: &[],
            push_constant_ranges: &[],
        });

        Ok(Arc::new(self.device.create_compute_pipeline(&wgpu::ComputePipelineDescriptor {
            label,
            layout: Some(&pipeline_layout),
            module: &shader_module,
            entry_point,
            cache: None,
            compilation_options: wgpu::PipelineCompilationOptions::default(),
        })))
    }

    /// Load pipeline from cache file
    fn load_pipeline_from_cache(
        &self,
        cache_file: &Path,
        entry_point: &str,
        label: Option<&str>,
    ) -> Result<Arc<ComputePipeline>> {
        let shader_source = fs::read_to_string(cache_file)?;
        self.compile_pipeline(&shader_source, entry_point, label)
    }

    /// Save pipeline source to cache file
    fn save_pipeline_to_cache(&self, cache_file: &Path, shader_source: &str) -> Result<()> {
        fs::write(cache_file, shader_source)?;
        Ok(())
    }

    /// Clear the cache
    pub fn clear_cache(&mut self) -> Result<()> {
        self.pipelines.clear();
        
        if self.cache_dir.exists() {
            fs::remove_dir_all(&self.cache_dir)?;
            fs::create_dir_all(&self.cache_dir)?;
        }
        
        Ok(())
    }

    /// Get cache statistics
    pub fn get_cache_stats(&self) -> CacheStats {
        let memory_pipelines = self.pipelines.len();
        let disk_files = if self.cache_dir.exists() {
            fs::read_dir(&self.cache_dir)
                .map(|dir| dir.count())
                .unwrap_or(0)
        } else {
            0
        };

        CacheStats {
            memory_pipelines,
            disk_files,
            cache_dir: self.cache_dir.clone(),
        }
    }
}

/// Cache statistics
#[derive(Debug)]
pub struct CacheStats {
    pub memory_pipelines: usize,
    pub disk_files: usize,
    pub cache_dir: std::path::PathBuf,
}

impl std::fmt::Display for CacheStats {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(
            f,
            "Shader Cache Stats:\n  Memory pipelines: {}\n  Disk files: {}\n  Cache dir: {}",
            self.memory_pipelines,
            self.disk_files,
            self.cache_dir.display()
        )
    }
}
