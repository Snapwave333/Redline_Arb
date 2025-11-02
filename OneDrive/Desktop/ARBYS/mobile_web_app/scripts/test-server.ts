#!/usr/bin/env ts-node

/**
 * Test server bootstrap script
 * Auto-detects framework and launches appropriate dev server
 * Waits for health endpoint to be available
 */

import { spawn, ChildProcess } from 'child_process'
import * as fs from 'fs'
import * as path from 'path'
import * as http from 'http'

const PORT = process.env.PORT || '3000'
const HEALTH_TIMEOUT = 120000 // 2 minutes
const POLL_INTERVAL = 1000 // 1 second

interface FrameworkConfig {
  name: string
  detectFiles: string[]
  startCommand: string[]
  healthEndpoint: string
  buildCommand?: string[]
}

// Resolve local binaries for cross-platform spawning
const BIN = {
  viteJs: path.join(process.cwd(), 'node_modules', 'vite', 'bin', 'vite.js'),
}

const frameworks: FrameworkConfig[] = [
  {
    name: 'Vite',
    detectFiles: ['vite.config.ts', 'vite.config.js'],
    // Spawn node with vite.js for cross-platform compatibility
    startCommand: ['node', BIN.viteJs, '--port', PORT, '--host'],
    healthEndpoint: `http://localhost:${PORT}/`,
  },
  {
    name: 'Next.js',
    detectFiles: ['next.config.js', 'next.config.ts', 'pages/', 'app/'],
    startCommand: ['npm', 'run', 'dev', '--', '-p', PORT],
    healthEndpoint: `http://localhost:${PORT}/api/health`,
  },
  {
    name: 'Create React App',
    detectFiles: ['public/index.html', 'src/index.js', 'src/App.js'],
    startCommand: ['npm', 'start'],
    healthEndpoint: `http://localhost:${PORT}/`,
  },
  {
    name: 'Nuxt.js',
    detectFiles: ['nuxt.config.js', 'nuxt.config.ts'],
    startCommand: ['npm', 'run', 'dev', '--', '--port', PORT],
    healthEndpoint: `http://localhost:${PORT}/`,
  },
]

function detectFramework(): FrameworkConfig | null {
  for (const framework of frameworks) {
    const hasAllFiles = framework.detectFiles.every(file => {
      try {
        return fs.existsSync(path.join(process.cwd(), file))
      } catch {
        return false
      }
    })

    if (hasAllFiles) {
      console.log(`🎯 Detected framework: ${framework.name}`)
      return framework
    }
  }

  console.log('⚠️  No supported framework detected, defaulting to Vite')
  return frameworks[0] // Default to Vite
}

async function waitForHealthCheck(endpoint: string, timeout: number): Promise<void> {
  return new Promise((resolve, reject) => {
    const startTime = Date.now()

    const checkHealth = () => {
      const req = http.get(endpoint, (res) => {
        if (res.statusCode === 200) {
          console.log(`✅ Health check passed: ${endpoint}`)
          resolve()
          return
        }

        // Continue checking if not ready yet
        if (Date.now() - startTime < timeout) {
          setTimeout(checkHealth, POLL_INTERVAL)
        } else {
          reject(new Error(`Health check timeout: ${endpoint} (status: ${res.statusCode})`))
        }
      })

      req.on('error', (error) => {
        // Continue checking if server not ready yet
        if (Date.now() - startTime < timeout) {
          setTimeout(checkHealth, POLL_INTERVAL)
        } else {
          reject(new Error(`Health check failed: ${endpoint} (${error.message})`))
        }
      })

      req.setTimeout(5000, () => {
        req.destroy()
        if (Date.now() - startTime < timeout) {
          setTimeout(checkHealth, POLL_INTERVAL)
        } else {
          reject(new Error(`Health check timeout: ${endpoint}`))
        }
      })
    }

    console.log(`⏳ Waiting for server at ${endpoint}...`)
    checkHealth()
  })
}

async function startServer(framework: FrameworkConfig): Promise<ChildProcess> {
  console.log(`🚀 Starting ${framework.name} dev server on port ${PORT}...`)

  const [command, ...args] = framework.startCommand
  const serverProcess = spawn(command, args, {
    cwd: process.cwd(),
    stdio: ['inherit', 'inherit', 'inherit'],
    env: {
      ...process.env,
      PORT,
      NODE_ENV: 'development',
      BROWSER: 'none', // Prevent browser auto-open
    },
  })

  // Handle server process events
  serverProcess.on('error', (error) => {
    console.error(`❌ Failed to start ${framework.name} server:`, error)
    process.exit(1)
  })

  serverProcess.on('exit', (code) => {
    if (code !== 0) {
      console.error(`❌ ${framework.name} server exited with code ${code}`)
      process.exit(code || 1)
    }
  })

  // Store process ID for cleanup
  if (serverProcess.pid) {
    fs.writeFileSync('.test-server-pid', serverProcess.pid.toString())
  }

  return serverProcess
}

async function main() {
  try {
    const framework = detectFramework()
    if (!framework) {
      throw new Error('No supported framework detected')
    }

    const serverProcess = await startServer(framework)

    // Wait for server to be ready
    await waitForHealthCheck(framework.healthEndpoint, HEALTH_TIMEOUT)

    console.log(`🎉 ${framework.name} server ready and healthy!`)
    console.log(`📡 Server running at: ${framework.healthEndpoint}`)

    // Keep the process running
    process.on('SIGINT', () => {
      console.log('\n🛑 Shutting down test server...')
      serverProcess.kill('SIGINT')
      process.exit(0)
    })

    process.on('SIGTERM', () => {
      console.log('\n🛑 Shutting down test server...')
      serverProcess.kill('SIGTERM')
      process.exit(0)
    })

    // Keep alive
    await new Promise(() => {}) // Never resolves, keeps process alive

  } catch (error) {
    console.error('❌ Test server startup failed:', error instanceof Error ? error.message : String(error))
    process.exit(1)
  }
}

// Handle cleanup on exit
process.on('exit', () => {
  try {
    if (fs.existsSync('.test-server-pid')) {
      const pid = parseInt(fs.readFileSync('.test-server-pid', 'utf8'))
      process.kill(pid, 'SIGTERM')
      fs.unlinkSync('.test-server-pid')
    }
  } catch (error) {
    // Ignore cleanup errors
  }
})

// In ESM environments, `require` is undefined; run main unconditionally
// since this script is invoked directly via npm script (ts-node).
main()
