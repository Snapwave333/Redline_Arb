import { chromium } from '@playwright/test'

async function globalSetup() {
  console.log('🚀 Starting global test setup...')

  const skipApi = process.env.SKIP_API === '1' || process.env.SKIP_API === 'true'

  // Start API server if not already running (unless explicitly skipped)
  const { spawn } = require('child_process')
  const path = require('path')

  if (!skipApi) {
    // Start the Python API server
    const apiServer = spawn('python', ['api_server.py'], {
      cwd: path.join(__dirname, '..'),
      detached: true,
      stdio: 'inherit'
    })

    // Store the process ID for cleanup
    process.env.API_SERVER_PID = apiServer.pid?.toString()

    // Wait for API server to be ready
    console.log('⏳ Waiting for API server to start...')
    await new Promise(resolve => setTimeout(resolve, 3000))

    // Verify API server is responding
    try {
      const response = await fetch('http://localhost:5000/api/health')
      if (!response.ok) {
        throw new Error(`API server health check failed: ${response.status}`)
      }
      console.log('✅ API server is ready')
    } catch (error) {
      console.error('❌ API server failed to start:', error)
      throw error
    }
  } else {
    console.log('🔕 SKIP_API enabled — skipping API server startup and health check.')
  }

  // Pre-warm browser for faster tests
  console.log('🌐 Pre-warming browser...')
  const browser = await chromium.launch()
  const page = await browser.newPage()

  // Visit the app to warm up caches
  try {
    await page.goto(process.env.BASE_URL || 'http://localhost:3000', {
      waitUntil: 'domcontentloaded',
      timeout: 30000
    })
    console.log('✅ Browser pre-warmed')
  } catch (error) {
    console.warn('⚠️  Browser pre-warm failed, continuing:', error instanceof Error ? error.message : String(error))
  } finally {
    await browser.close()
  }

  console.log('✅ Global setup complete')
}

export default globalSetup
