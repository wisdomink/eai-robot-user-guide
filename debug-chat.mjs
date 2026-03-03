/**
 * Debug ChatKit SDK: capture screenshots and network activity
 * Run: node debug-chat.mjs
 */

import { chromium } from 'playwright'
import { writeFileSync, mkdirSync } from 'fs'
import { join } from 'path'

const BASE_URL = 'http://localhost:5173'
const SCREENSHOT_DIR = join(process.cwd(), 'test-screenshots')

const networkLog = []
const consoleLog = []

async function main() {
  const browser = await chromium.launch({ headless: true })
  const context = await browser.newContext()
  const page = await context.newPage()

  // Log ALL network requests
  page.on('request', (req) => {
    networkLog.push({
      time: new Date().toISOString(),
      type: 'request',
      method: req.method(),
      url: req.url(),
      resourceType: req.resourceType(),
    })
  })
  page.on('response', (res) => {
    networkLog.push({
      time: new Date().toISOString(),
      type: 'response',
      url: res.url(),
      status: res.status(),
      headers: res.status() >= 400 ? Object.fromEntries(res.headers()) : undefined,
    })
  })
  page.on('requestfailed', (req) => {
    networkLog.push({
      time: new Date().toISOString(),
      type: 'failed',
      url: req.url(),
      error: req.failure()?.errorText || 'unknown',
    })
  })

  page.on('console', (msg) => {
    consoleLog.push({
      type: msg.type(),
      text: msg.text(),
    })
  })

  try {
    // Step 1-2: Navigate and wait for load
    await page.goto(BASE_URL, { waitUntil: 'networkidle' })
    console.log('Step 1-2: Page loaded')

    // Step 3: Click "Ask AI"
    const chatBtn = page.locator('button#chatToggleBtn, button:has-text("Ask AI")').first()
    await chatBtn.click()
    await page.waitForTimeout(500)
    const chatPanel = page.locator('#chatPanel.open, .chat-panel.open')
    await chatPanel.waitFor({ state: 'visible', timeout: 3000 })
    console.log('Step 3: Chat panel opened')

    // Step 4: Screenshot after opening
    await page.screenshot({ path: join(SCREENSHOT_DIR, 'debug-01-panel-open.png') })
    console.log('Step 4: Screenshot 1 saved')

    // Step 5: Type "Hello" and send (ChatKit may be in iframe)
    await page.waitForTimeout(2000)
    let composer = page.locator('textarea[placeholder*="Ask"], textarea[placeholder*="question"], [contenteditable="true"]').first()
    let frame = page
    const iframe = page.locator('iframe[src*="openai"], iframe[src*="platform"], .chatkit-body iframe').first()
    if (await iframe.count() > 0 && await iframe.isVisible()) {
      frame = page.frameLocator('iframe[src*="openai"], iframe[src*="platform"], .chatkit-body iframe').first()
      composer = frame.locator('textarea[placeholder*="Ask"], textarea[placeholder*="question"], [contenteditable="true"]').first()
    }
    await composer.waitFor({ state: 'visible', timeout: 8000 })
    await composer.fill('Hello')
    await page.waitForTimeout(300)
    const sendBtn = frame.locator('button[type="submit"], [aria-label="Send"], button:has(svg), button[aria-label*="end"]').last()
    await sendBtn.click()
    console.log('Step 5: Sent "Hello"')

    // Step 6-7: Wait 3s, screenshot
    await page.waitForTimeout(3000)
    await page.screenshot({ path: join(SCREENSHOT_DIR, 'debug-02-after-3s.png') })
    console.log('Step 6-7: Screenshot 2 saved (after 3s)')

    // Step 8-9: Wait 5s more, final screenshot
    await page.waitForTimeout(5000)
    await page.screenshot({ path: join(SCREENSHOT_DIR, 'debug-03-after-8s.png') })
    console.log('Step 8-9: Screenshot 3 saved (after 8s total)')
  } catch (err) {
    console.error('Error:', err.message)
  } finally {
    await browser.close()
  }

  // Save network and console logs
  writeFileSync(join(SCREENSHOT_DIR, 'debug-network.json'), JSON.stringify(networkLog, null, 2))
  writeFileSync(join(SCREENSHOT_DIR, 'debug-console.json'), JSON.stringify(consoleLog, null, 2))
  console.log('\nNetwork log saved to test-screenshots/debug-network.json')
  console.log('Console log saved to test-screenshots/debug-console.json')
}

try { mkdirSync(SCREENSHOT_DIR, { recursive: true }) } catch (_) {}

main().catch(console.error)
