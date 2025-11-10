async function globalTeardown() {
  console.log('🧹 Starting global test teardown...')
  const skipApi = process.env.SKIP_API === '1' || process.env.SKIP_API === 'true'

  // Clean up API server unless skipped
  if (!skipApi && process.env.API_SERVER_PID) {
    const { exec } = require('child_process')
    const util = require('util')
    const execAsync = util.promisify(exec)

    try {
      if (process.platform === 'win32') {
        // Windows: use taskkill to kill process tree
        await execAsync(`taskkill /pid ${process.env.API_SERVER_PID} /t /f`)
      } else {
        // Unix-like systems: use pkill
        await execAsync(`pkill -f "python api_server.py"`)
      }
      console.log('✅ API server cleaned up')
    } catch (error) {
      console.warn('⚠️  API server cleanup warning:', error instanceof Error ? error.message : String(error))
    }
  }

  // Clean up any test artifacts or temporary files
  const fs = require('fs').promises
  const path = require('path')

  const cleanupDirs = [
    path.join(__dirname, '..', 'test-results', 'temp'),
    path.join(__dirname, '..', 'playwright-report', 'temp')
  ]

  for (const dir of cleanupDirs) {
    try {
      await fs.rm(dir, { recursive: true, force: true })
    } catch (error) {
      // Ignore if directory doesn't exist
    }
  }

  console.log('✅ Global teardown complete')
}

export default globalTeardown
