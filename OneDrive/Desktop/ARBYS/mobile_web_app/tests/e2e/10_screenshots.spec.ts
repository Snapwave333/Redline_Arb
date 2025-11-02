import { test } from '@playwright/test'
import * as path from 'path'

// Helper to resolve paths at repo root from mobile_web_app cwd
const repoRoot = path.resolve(process.cwd(), '..')
const readmePreviewPath = path.join(repoRoot, 'preview_ui.png')
const socialPreviewPath = path.join(repoRoot, 'GitHub_README_Assets', 'social_preview.png')

// Common init: skip onboarding, disable animations
async function prep(page) {
  await page.addInitScript(() => {
    localStorage.setItem('noOnboarding', 'true')
    localStorage.setItem('welcomeCompleted', 'true')
  })
  await page.addStyleTag({
    content: `
      *, *::before, *::after {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
        scroll-behavior: auto !important;
      }
    `
  })
}

test.describe('Generate screenshots for README and Social Preview', () => {
  test('README UI Preview (1280x720, full page)', async ({ page }) => {
    await prep(page)
    await page.setViewportSize({ width: 1280, height: 720 })
    await page.goto('/')
    try { await page.waitForSelector('[data-testid="app"]', { timeout: 8000 }) } catch {}
    await page.waitForLoadState('networkidle')
    await page.screenshot({ path: readmePreviewPath, fullPage: true })
    console.log(`Saved README UI preview to: ${readmePreviewPath}`)
  })

  test('GitHub Social Preview (1200x630, full page)', async ({ page }) => {
    await prep(page)
    await page.setViewportSize({ width: 1200, height: 630 })
    await page.goto('/')
    try { await page.waitForSelector('[data-testid="app"]', { timeout: 8000 }) } catch {}
    await page.waitForLoadState('networkidle')
    await page.screenshot({ path: socialPreviewPath, fullPage: true })
    console.log(`Saved social preview to: ${socialPreviewPath}`)
  })
})