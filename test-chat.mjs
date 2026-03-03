/**
 * E2E test: Chat functionality
 * Run with: npx playwright test test-chat.mjs --project=chromium
 * Or standalone: node test-chat.mjs (uses playwright directly)
 */

import { chromium } from 'playwright'
import { writeFileSync } from 'fs'
import { join } from 'path'

const BASE_URL = 'http://localhost:5173'
const SCREENSHOT_DIR = join(process.cwd(), 'test-screenshots')

async function main() {
  const results = {
    chatPanelOpens: false,
    canSendMessage: false,
    receivedResponse: false,
    consoleErrors: [],
    networkErrors: [],
  }

  const browser = await chromium.launch({ headless: true })
  const context = await browser.newContext()
  const page = await context.newPage()

  // Capture console messages
  page.on('console', (msg) => {
    const type = msg.type()
    const text = msg.text()
    if (type === 'error') {
      results.consoleErrors.push(text)
    }
  })

  // Capture failed network requests
  page.on('requestfailed', (request) => {
    results.networkErrors.push({
      url: request.url(),
      failure: request.failure()?.errorText || 'unknown',
    })
  })

  try {
    // Step 1: Navigate
    await page.goto(BASE_URL, { waitUntil: 'networkidle' })
    await page.screenshot({ path: join(SCREENSHOT_DIR, '01-initial-page.png') })
    console.log('✓ Step 1: Navigated to', BASE_URL)

    // Step 2: Look for and click "Ask AI" button
    const chatBtn = page.locator('button#chatToggleBtn, button:has-text("Ask AI")').first()
    await chatBtn.waitFor({ state: 'visible', timeout: 5000 })
    await chatBtn.click()
    await page.waitForTimeout(500)

    // Check if chat panel is visible
    const chatPanel = page.locator('#chatPanel.open, .chat-panel.open')
    await chatPanel.waitFor({ state: 'visible', timeout: 3000 })
    results.chatPanelOpens = true
    console.log('✓ Step 2: Chat panel opened')

    await page.screenshot({ path: join(SCREENSHOT_DIR, '02-chat-panel-open.png') })

    // Step 3: Type and send a message (ChatKit may render in iframe)
    await page.waitForTimeout(2000) // Let ChatKit fully initialize
    let composer = page.locator('textarea[placeholder*="Ask"], textarea[placeholder*="question"], [contenteditable="true"]').first()
    let frame = page
    const iframe = page.locator('iframe[src*="openai"], iframe[src*="platform"], .chatkit-body iframe').first()
    if (await iframe.count() > 0 && await iframe.isVisible()) {
      frame = page.frameLocator('iframe[src*="openai"], iframe[src*="platform"], .chatkit-body iframe').first()
      composer = frame.locator('textarea[placeholder*="Ask"], textarea[placeholder*="question"], [contenteditable="true"]').first()
    }
    await composer.waitFor({ state: 'visible', timeout: 8000 })
    await composer.fill('What is this manual about?')
    await page.waitForTimeout(500)

    // Try to find and click send button
    const sendBtn = frame.locator('button[type="submit"], [aria-label="Send"], button:has(svg), button[aria-label*="end"]').last()
    await sendBtn.click()
    results.canSendMessage = true
    console.log('✓ Step 3: Message sent')

    // Step 4: Wait for response
    await page.waitForTimeout(10000)

    // Check for assistant response (must be in chat area, not page content)
    const chatBody = frame.locator('[class*="message"], [class*="assistant"], [role="log"]').filter({ hasText: /FF Master|manual|documentation|instruction/i })
    const assistantMessages = frame.locator('[class*="assistant"]')
    results.receivedResponse = (await assistantMessages.count()) > 0
    console.log('✓ Step 4: Waited for response, receivedResponse:', results.receivedResponse)

    await page.screenshot({ path: join(SCREENSHOT_DIR, '03-after-response.png') })
  } catch (err) {
    console.error('Test error:', err.message)
  } finally {
    await browser.close()
  }

  // Report
  console.log('\n========== REPORT ==========')
  console.log('Chat panel opens:', results.chatPanelOpens)
  console.log('Can send message:', results.canSendMessage)
  console.log('Received response:', results.receivedResponse)
  console.log('Console errors:', results.consoleErrors.length, results.consoleErrors)
  console.log('Network errors:', results.networkErrors.length, results.networkErrors)
  writeFileSync(join(SCREENSHOT_DIR, 'report.json'), JSON.stringify(results, null, 2))
}

// Ensure screenshot dir exists
import { mkdirSync } from 'fs'
try { mkdirSync(SCREENSHOT_DIR, { recursive: true }) } catch (_) {}

main().catch(console.error)
