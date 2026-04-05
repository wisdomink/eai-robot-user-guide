#!/usr/bin/env node
/**
 * convert-aegisedu.mjs — Source-to-markdown pipeline for FX Aegis EDU manual
 *
 * Hybrid approach: PDF for text extraction, Word for image extraction.
 *
 * Usage:
 *   npm run convert:aegisedu              # full pipeline (text + images)
 *   npm run convert:aegisedu:text         # text only
 *   npm run convert:aegisedu:images       # images only
 *
 * Source files:
 *   src/content/source/aegisedu.pdf   — text source
 *   src/content/source/aegisedu.docx  — image source
 *
 * Output:
 *   src/content/pages/aegis-edu/*.md   — markdown files
 *   public/images/aegis-edu/*          — extracted images
 */

import { promises as fs } from 'node:fs'
import path from 'node:path'
import { execSync } from 'node:child_process'
import mammoth from 'mammoth'

// ─── Paths ──────────────────────────────────────────────────────────────────

const ROOT = path.resolve(import.meta.dirname, '..')
const PDF_PATH = path.join(ROOT, 'src/content/source/aegisedu.pdf')
const DOCX_PATH = path.join(ROOT, 'src/content/source/aegisedu.docx')
const PAGES_DIR = path.join(ROOT, 'src/content/pages/aegis-edu')
const IMAGES_DIR = path.join(ROOT, 'public/images/aegis-edu')

// ─── Section Definitions ────────────────────────────────────────────────────

const SECTIONS = [
  // ── Version Statement ─────────────────────────────────────────────────────
  {
    chapter: 1,
    file: 'legal-statement.md',
    title: 'Legal Statement',
    pattern: /^Legal Statement\s*$/m,
    endBefore: /^Notes to be Observed/m,
  },
  {
    chapter: 1,
    file: 'notes.md',
    title: 'Notes to be Observed',
    pattern: /^Notes to be Observed\s*$/m,
    endBefore: /^Battery and Charging Precautions/m,
  },
  {
    chapter: 1,
    file: 'battery-charging-precautions.md',
    title: 'Battery and Charging Precautions',
    pattern: /^Battery and Charging Precautions\s*$/m,
    endBefore: /^Product Overview\s*$/m,
  },

  // ── Product Description ───────────────────────────────────────────────────
  {
    chapter: 2,
    file: 'product-overview.md',
    title: 'Product Overview',
    pattern: /^Product Overview\s*$/m,
    endBefore: /^Component Introduction/m,
  },
  {
    chapter: 2,
    file: 'component-introduction.md',
    title: 'Component Introduction',
    pattern: /^Component Introduction\s*$/m,
    endBefore: /^Introduction to Tail Lights/m,
    images: [
      { position: 'start', headingId: 'heading_8', endHeadingId: 'heading_9', name: 'component',
        alts: ['Product Overview', 'Component Introduction', 'Expansion Interface', 'Expansion Interface Cover', 'Tail Lights'] },
    ],
    tables: [
      {
        headerPattern: /No\.\s{2,}Interface\s{2,}Qty\s{2,}Description/,
        replaceToEnd: true,
        hardcoded: [
          '| No. | Interface | Qty | Description |',
          '| --- | --- | --- | --- |',
          '| 1 | Ethernet Port | 1 | RJ45 Interface: Supports 1,000 Mbps transmission for high-speed data transfer. It facilitates network connectivity, remote monitoring, data transmission and other related applications. |',
          '| 2 | USB Interface | 2 | Type-A interface: used to connect external storage devices, cameras, sensors, and other USB devices. It provides high-speed data transfer and power delivery. |',
          '| 3 | Power Interface | 2 | Standard DC power interface provides stable power supply, supporting 12V and 24V voltage outputs, meeting the power requirements of the robot dog and its onboard equipment. |',
          '| 4 | SBUS Interface | 1 | Standard SBUS interface for connecting to remote control receivers or other communication devices supporting the SBUS protocol, enabling precise transmission of remote control commands. |',
          '| 5 | UART Interface | 1 | Standard UART interface for connecting embedded systems, communication devices, or other UART-protocol-compliant equipment, enabling data exchange and control between devices via asynchronous serial communication. |',
        ].join('\n'),
      },
    ],
  },
  {
    chapter: 2,
    file: 'tail-lights.md',
    title: 'Introduction to Tail Lights',
    pattern: /^Introduction to Tail Lights\s*$/m,
    endBefore: /^Power Supply Introduction/m,
    tables: [
      {
        headerPattern: /Lighting\s{2,}Light Language\s{2,}Note/,
        replaceToEnd: true,
        hardcoded: [
          '| Lighting | Light Language | Note |',
          '| --- | --- | --- |',
          '| Blue light is constantly on | The system has booted up. | |',
          '| Blue flashing | Booting up. | |',
          '| Constantly illuminated in white | Laboratory mode | In this mode, your movement ability is enhanced and special tricks are unlocked. |',
          '| The green light is always on. | Tracking mode activated. | |',
          '| The yellow light is always on. | The battery power is less than 20%. | The battery is low and the Beast Mode cannot be activated. |',
          '| The yellow light is flashing. | The battery power is less than 5% | The battery is low and needs to be charged immediately. |',
          '| The red light is always on | The joint temperature is too high and needs to be cooled. | |',
          '| The red light is flashing. | System error. Please contact after-sales service. | |',
        ].join('\n'),
      },
    ],
  },
  {
    chapter: 2,
    file: 'power-supply.md',
    title: 'Power Supply Introduction',
    pattern: /^Power Supply Introduction\s*$/m,
    endBefore: /^Preparation Before First Use/m,
    images: [
      { position: 'end', headingId: 'heading_9', endHeadingId: 'heading_10', name: 'power-supply',
        alts: ['Battery display - idle/discharge', 'Battery LED indicator'] },
      { position: 'end', headingId: 'heading_10', endHeadingId: 'heading_11', name: 'battery-charge',
        alts: ['Battery display - charge state'] },
      { position: 'end', headingId: 'heading_11', endHeadingId: 'heading_12', name: 'power-adapter',
        alts: ['Power adapter front', 'Power adapter back'] },
      { position: 'end', headingId: 'heading_12', endHeadingId: 'heading_22', name: 'charging-instructions',
        alts: ['Charging steps', 'Charging dock'] },
    ],
    tables: [
      {
        headerPattern: /NO\.\s{2,}SOC/,
        hardcoded: [
          '| NO. | SOC(%) | LED1 | LED2 | LED3 | LED4 |',
          '| --- | --- | --- | --- | --- | --- |',
          '| 1 | 0 to 14 | Flashing | OFF | OFF | OFF |',
          '| 2 | 15 to 24 | ON | OFF | OFF | OFF |',
          '| 3 | 25 to 49 | ON | ON | OFF | OFF |',
          '| 4 | 50 to 74 | ON | ON | ON | OFF |',
          '| 5 | 75 to 100 | ON | ON | ON | ON |',
        ].join('\n'),
      },
      {
        headerPattern: /No\.\s{2,}SOC\s*\(%\)/,
        hardcoded: [
          '| No. | SOC (%) | LED 1 | LED 2 | LED 3 | LED 4 |',
          '| --- | --- | --- | --- | --- | --- |',
          '| 1 | 0 – 24% | Flashing | OFF | OFF | OFF |',
          '| 2 | 25 – 49% | ON | Flashing | OFF | OFF |',
          '| 3 | 50 – 74% | ON | ON | Flashing | OFF |',
          '| 4 | 75 – 99% | ON | ON | ON | Flashing |',
          '| 5 | 100% | ON | ON | ON | ON |',
        ].join('\n'),
      },
    ],
  },

  // ── Product Usage ─────────────────────────────────────────────────────────
  {
    chapter: 3,
    file: 'first-use.md',
    title: 'Preparation Before First Use',
    pattern: /^Preparation Before First Use\s*$/m,
    endBefore: /^Remote Control User Manual/m,
    images: [
      { position: 'end', headingId: 'heading_22', endHeadingId: 'heading_23', name: 'first-use',
        alts: ['Power on', 'Battery insertion', 'Power off'] },
    ],
  },
  {
    chapter: 3,
    file: 'remote-control.md',
    title: 'Remote Control User Guide',
    pattern: /^Remote Control User Manual\s*$/m,
    endBefore: /^APP User Guide/m,
    images: [
      { position: 'end', headingId: 'heading_23', endHeadingId: 'heading_24', name: 'remote-control-intro',
        alts: ['Remote controller overview', 'Remote controller top view', 'Remote controller front'] },
      { position: 'end', headingId: 'heading_24', endHeadingId: 'heading_25', name: 'remote-control-ops',
        alts: ['Operations instructions table'] },
    ],
    tables: [
      {
        headerPattern: /Key Position\s{2,}Names and Functions/,
        hardcoded: [
          '| Key Position | Names and Functions |',
          '| --- | --- |',
          '| Left mouse button / trigger | LB and LT buttons |',
          '| Right-click / Trigger | RB and RT buttons |',
          '| Direction keys | Left cross key |',
          '| Joystick | LS: Left Stick (Forward, Backward, Move Left, Move Right); RS: Right Stick (Rotate direction) |',
          '| Mode button | / |',
          '| Mode/Status indicator light | Status indicator light |',
          '| Vibration button | / |',
          '| Four action buttons | Function keys A, B, X and Y |',
          '| "START" button | START button |',
          '| Button | / |',
          '| Back button | / |',
        ].join('\n'),
      },
      {
        headerPattern: /Key Position\s{2,}Action\s{2,}Button/,
        replaceToEnd: true,
        hardcoded: [
          '| Key Position | Action | Button |',
          '| --- | --- | --- |',
          '| Switch between regular mode and laboratory mode | | START+BACK |',
          '| General actions | Stand up | LB+Y |',
          '| | Damping (slowly crouch down) | LB+X |',
          '| | Drop (Emergency stop) | LB+RB |',
          '| Movement action | Move left and right, forward and backward | Left Stick |',
          '| In-place movements | In-place / Mobile switching | START+B |',
          '| | Pitch adjustment | Push the right joystick forward/backward |',
          '| | Horizontal turn | Push the right joystick left or right |',
          '| | Left/Right probe | X/B |',
          '| | Tall/short stature | Y/A |',
          '| Stunt performance | Jump up | RB+A |',
          '| | Jump forward | RB+X |',
          '| | Backwards somersault | RB+B |',
          '| | Say hello | RB+Y |',
          '| | Stand with both legs | LB+A |',
        ].join('\n'),
      },
    ],
  },
  {
    chapter: 3,
    file: 'app-guide.md',
    title: 'APP User Guide',
    pattern: /^APP User Guide\s*$/m,
    endBefore: /^Product OTA [Uu]pgrade/m,
    images: [
      { position: 'end', headingId: 'heading_25', endHeadingId: 'heading_26', name: 'app-download',
        alts: ['APP download', 'Account registration', 'Add robot', 'Select robot', 'Network mode'] },
      { position: 'end', headingId: 'heading_26', endHeadingId: 'heading_27', name: 'app-connecting',
        alts: ['WiFi connecting'] },
      { position: 'end', headingId: 'heading_27', endHeadingId: 'heading_28', name: 'app-operations',
        alts: ['Connection successful', 'AP connection mode', 'Home page', 'Mobile mode', 'Stationary mode',
               'Emergency stop', 'Stunt moves', 'Speed setting', 'Forward jump', 'Upward jump',
               'Backflip', 'Speed slider', 'Warning stunt'] },
    ],
  },
  {
    chapter: 3,
    file: 'ota-upgrade.md',
    title: 'Product OTA Upgrade',
    pattern: /^Product OTA [Uu]pgrade\s*$/m,
    endBefore: /^Product Parameters\s*$/m,
  },

  // ── Product Parameters ────────────────────────────────────────────────────
  {
    chapter: 4,
    file: 'product-parameters.md',
    title: 'Product Parameters',
    pattern: /^Product Parameters\s*$/m,
    endBefore: /^Troubleshooting\s*$/m,
    images: [
      { position: 'end', headingId: 'heading_28', endHeadingId: 'heading_29', name: 'product-parameters',
        alts: ['Product parameters overview'] },
    ],
    tables: [
      {
        headerPattern: /Category\s{2,}Specification\s{2,}Description/,
        replaceToEnd: false,
        hardcoded: [
          '| Category | Specification | Description |',
          '| --- | --- | --- |',
          '| Basic Information | Material | Aluminum alloy with high-strength engineering plastic |',
          '| | Standing Dimensions (L x W x H) | 635 mm x 360 mm x 420 mm |',
          '| | Lying Down Dimensions (L x W x H) | 675 mm x 435 mm x 145 mm |',
          '| | Total Weight (with battery) | 15.5kg |',
          '| | Operating Temperature | 0°C–40°C |',
          '| | Ingress Protection Rating | IP54 |',
          '| Performance Parameters | Maximum Speed | 3.5 m/s |',
          '| | Effective Payload | 5kg |',
          '| | Continuous Stair-Climbing Height | 16 cm |',
          '| | Maximum Climbing Angle | 30° standard, up to 40° maximum |',
          '| | Vertical Jump Height | 35 cm |',
          '| Electrical Parameters | Battery Module | Rated Capacity: 4.6Ah, Voltage: 43.2v |',
          '| | Charging Duration | 1 hour |',
          '| | Battery Life (Operating Time) | 1–2 hours |',
          '| | Operating Range | 6km |',
        ].join('\n'),
      },
    ],
  },

  // ── Troubleshooting ───────────────────────────────────────────────────────
  {
    chapter: 5,
    file: 'troubleshooting.md',
    title: 'Troubleshooting',
    pattern: /^Troubleshooting\s*$/m,
    endBefore: /^Product Transportation/m,
    images: [
      { position: 'end', headingId: 'heading_29', endHeadingId: 'heading_30', name: 'troubleshooting',
        alts: ['Troubleshooting reference'] },
    ],
    tables: [
      {
        headerPattern: /Issues\s{2,}Recommended Actions/,
        replaceToEnd: true,
        hardcoded: [
          '| Issues | Recommended Actions |',
          '| --- | --- |',
          '| What should I do if the remote control cannot connect to the robotic dog? | 1. Ensure the robot is powered on. 2. Confirm that no other version of the APP is running in the background on the remote controller. 3. If the connection still fails, restart both the robot and the APP, then attempt to connect again. |',
          '| What should I do if the controller is unresponsive after connecting to the robotic dog? | 1. Confirm that the controller is connected to the correct Wi-Fi network of the robotic dog. 2. If it remains unresponsive, wait for 10 seconds and try operating the robot again. 3. If there is still no response, restart the robot. |',
          '| Is it normal for the robotic dog to stop moving on its own? | This may be due to the activation of the robot\'s protection function. 1. Please wait for 10 minutes and then try again. 2. If you still cannot control the robot to resume movement, first check if the battery level is sufficient, and then check if the controller signal has been disconnected. |',
        ].join('\n'),
      },
    ],
  },

  // ── Transportation and Storage ────────────────────────────────────────────
  {
    chapter: 6,
    file: 'transportation.md',
    title: 'Product Transportation',
    pattern: /^Product Transportation\s*$/m,
    endBefore: /^Storage Environment/m,
  },
  {
    chapter: 6,
    file: 'storage.md',
    title: 'Storage Environment',
    pattern: /^Storage Environment\s*$/m,
    endBefore: /^Battery Precautions\s*$/m,
  },
  {
    chapter: 6,
    file: 'battery-precautions-storage.md',
    title: 'Battery Precautions',
    pattern: /^Battery Precautions\s*$/m,
    endBefore: /^Handle with care/m,
  },
  {
    chapter: 6,
    file: 'handle-with-care.md',
    title: 'Handle with Care',
    pattern: /^Handle with care\.\s*$/m,
    endBefore: /^Hazardous Substances/m,
  },

  // ── Hazardous Substances ──────────────────────────────────────────────────
  {
    chapter: 7,
    file: 'hazardous-substances.md',
    title: 'Hazardous Substances',
    pattern: /^Hazardous Substances Description\s*$/m,
    endBefore: /^Warranty Instructions/m,
    images: [
      { position: 'end', headingId: 'heading_35', endHeadingId: 'heading_36', name: 'hazardous-substances',
        alts: ['Hazardous substances table'] },
    ],
    tables: [
      {
        headerPattern: /Component\s{2,}Lead\s*\(Pb\)/,
        replaceToEnd: false,
        hardcoded: [
          '| Component | Lead (Pb) | Mercury (Hg) | Cadmium (Cd) | Hexavalent Chromium (Cr(VI)) | Polybrominated Biphenyls (PBB) | Polybrominated Diphenyl Ethers (PBDE) |',
          '| --- | --- | --- | --- | --- | --- | --- |',
          '| Circuit Board | X | O | O | O | O | O |',
          '| Metal Plate | X | O | O | O | O | O |',
          '| Housing | O | O | O | O | O | O |',
          '| Battery | X | O | O | O | O | O |',
          '| Other Components | O | O | O | O | O | O |',
        ].join('\n'),
      },
    ],
  },

  // ── Warranty Information ──────────────────────────────────────────────────
  {
    chapter: 8,
    file: 'warranty.md',
    title: 'Warranty Instructions',
    pattern: /^Warranty Instructions\s*$/m,
    endBefore: /^___NEVER_MATCH___$/m,
  },
]

// ─── Table Parsing Helpers ──────────────────────────────────────────────────

function detectColumnPositions(headerLine) {
  const positions = []
  let i = 0
  const len = headerLine.length
  while (i < len && headerLine[i] === ' ') i++
  if (i >= len) return [0]
  positions.push(i)
  while (i < len) {
    while (i < len && headerLine[i] !== ' ') i++
    const spaceStart = i
    while (i < len && headerLine[i] === ' ') i++
    const spaceLen = i - spaceStart
    if (i < len && spaceLen >= 2) positions.push(i)
  }
  positions[0] = 0
  return positions
}

function parseTableRows(dataLines, colPositions) {
  const numCols = colPositions.length
  const rows = []
  let currentRow = null
  for (const line of dataLines) {
    if (line.trim() === '') {
      if (currentRow) { rows.push(currentRow); currentRow = null }
      continue
    }
    const cells = []
    for (let c = 0; c < numCols; c++) {
      const start = colPositions[c]
      const end = c + 1 < numCols ? colPositions[c + 1] : line.length
      const text = start < line.length ? line.substring(start, Math.min(end, line.length)).trim() : ''
      cells.push(text)
    }
    const firstColHasContent = cells[0] !== ''
    if (firstColHasContent && currentRow) { rows.push(currentRow); currentRow = null }
    if (!currentRow) { currentRow = cells.slice() }
    else { for (let c = 0; c < numCols; c++) { if (cells[c]) currentRow[c] = currentRow[c] ? currentRow[c] + ' ' + cells[c] : cells[c] } }
  }
  if (currentRow) rows.push(currentRow)
  return rows
}

function formatMarkdownTable(columns, rows) {
  const lines = []
  lines.push('| ' + columns.join(' | ') + ' |')
  lines.push('| ' + columns.map(() => '---').join(' | ') + ' |')
  for (const row of rows) {
    const paddedRow = [...row]
    while (paddedRow.length < columns.length) paddedRow.push('')
    const escaped = paddedRow.map(cell => cell.replace(/\|/g, '\\|'))
    lines.push('| ' + escaped.join(' | ') + ' |')
  }
  return lines.join('\n')
}

function findTableEnd(lines, startLine) {
  let blanks = 0
  for (let j = startLine; j < lines.length; j++) {
    if (lines[j].trim() === '') {
      blanks++
      if (blanks >= 3) return j - blanks + 1
    } else {
      blanks = 0
      if (/^\d+\.\d+(\.\d+)*\s/.test(lines[j].trim())) return j
    }
  }
  return lines.length
}

function processTablesInRawText(rawText, tableDefs) {
  if (!tableDefs || tableDefs.length === 0) return rawText
  const lines = rawText.split('\n')
  const replacements = []
  for (const def of tableDefs) {
    if (def.hardcoded) {
      let matchCount = 0
      const targetIndex = def.matchIndex || 0
      for (let i = 0; i < lines.length; i++) {
        if (!def.headerPattern.test(lines[i])) continue
        if (replacements.some(r => i >= r.startLine && i < r.endLine)) { matchCount++; continue }
        if (matchCount === targetIndex) {
          const endLine = def.replaceToEnd ? lines.length : findTableEnd(lines, i)
          replacements.push({ startLine: i, endLine, replacement: def.hardcoded })
          break
        }
        matchCount++
      }
      continue
    }
    for (let i = 0; i < lines.length; i++) {
      if (replacements.some(r => i >= r.startLine && i < r.endLine)) continue
      if (!def.headerPattern.test(lines[i])) continue
      const colPositions = def.colPositions || detectColumnPositions(lines[i])
      let headerEnd = i + 1
      while (headerEnd < lines.length && lines[headerEnd].trim() !== '') headerEnd++
      while (headerEnd < lines.length && lines[headerEnd].trim() === '') headerEnd++
      const dataEnd = findTableEnd(lines, headerEnd)
      const dataLines = lines.slice(def.includeHeaderAsData ? i : headerEnd, dataEnd)
      const rows = parseTableRows(dataLines, colPositions)
      if (rows.length > 0) {
        const mdTable = formatMarkdownTable(def.columns, rows)
        replacements.push({ startLine: i, endLine: dataEnd, replacement: mdTable })
      }
    }
  }
  replacements.sort((a, b) => b.startLine - a.startLine)
  const result = [...lines]
  for (const rep of replacements) {
    result.splice(rep.startLine, rep.endLine - rep.startLine, ...rep.replacement.split('\n'))
  }
  return result.join('\n')
}

// ─── Step 1: Image Extraction (Word → images) ──────────────────────────────

async function extractImages(sections) {
  console.log('\n── Step 1: Extracting images from Word ──')
  console.log('Reading:', DOCX_PATH)

  const docxBuffer = await fs.readFile(DOCX_PATH)
  const result = await mammoth.convertToMarkdown({ buffer: docxBuffer })
  const fullMd = result.value

  const headingRegex = /<a id="(heading_\d+)"><\/a>/g
  const headings = []
  let m
  while ((m = headingRegex.exec(fullMd)) !== null) {
    headings.push({ id: m[1], pos: m.index })
  }
  console.log(`  Found ${headings.length} headings in Word document`)

  await fs.mkdir(IMAGES_DIR, { recursive: true })

  const extractionRules = []
  for (const section of sections) {
    if (!section.images) continue
    for (const rule of section.images) {
      if (!extractionRules.find(r => r.headingId === rule.headingId && r.name === rule.name)) {
        extractionRules.push(rule)
      }
    }
  }

  const imageMap = new Map()

  for (const rule of extractionRules) {
    const headingIdx = headings.findIndex(h => h.id === rule.headingId)
    if (headingIdx === -1) {
      console.warn(`  Warning: Heading ${rule.headingId} not found, skipping ${rule.name}`)
      imageMap.set(rule.name, [])
      continue
    }

    const startPos = headings[headingIdx].pos
    let endPos = fullMd.length
    if (rule.endHeadingId) {
      const endIdx = headings.findIndex(h => h.id === rule.endHeadingId)
      if (endIdx !== -1) endPos = headings[endIdx].pos
    } else if (headingIdx + 1 < headings.length) {
      endPos = headings[headingIdx + 1].pos
    }

    const sectionMd = fullMd.substring(startPos, endPos)
    const imgRegex = /!\[([^\]]*)\]\(data:image\/([^;]+);base64,([^)]+)\)/g
    let imgMatch
    let imageIndex = 0
    const imageFiles = []

    while ((imgMatch = imgRegex.exec(sectionMd)) !== null) {
      imageIndex++
      const ext = imgMatch[2] === 'x-emf' ? 'png' : imgMatch[2]
      const filename = `${rule.name}-${imageIndex}.${ext}`
      const filepath = path.join(IMAGES_DIR, filename)
      const buffer = Buffer.from(imgMatch[3], 'base64')
      await fs.writeFile(filepath, buffer)
      imageFiles.push(filename)
    }

    imageMap.set(rule.name, imageFiles)
    if (imageFiles.length > 0) console.log(`  ${rule.name}: ${imageFiles.length} image(s)`)
    else console.log(`  ${rule.name}: no images found`)
  }

  return imageMap
}

// ─── Step 2: Text Extraction (PDF → markdown) ──────────────────────────────

function extractPdfText(pdfPath) {
  try {
    return execSync(`pdftotext -layout "${pdfPath}" -`, { encoding: 'utf-8', maxBuffer: 50 * 1024 * 1024 })
  } catch (err) {
    console.error('Error: pdftotext failed. Install with: brew install poppler')
    throw err
  }
}

function findPatternPos(fullText, afterPos, pattern) {
  const remaining = fullText.substring(afterPos)
  const match = remaining.match(pattern)
  return match ? afterPos + match.index : fullText.length
}

function convertToMarkdown(rawText) {
  const lines = rawText.split('\n')
  const mdLines = []
  let current = ''
  let currentType = ''

  function flush() {
    if (current.trim()) { mdLines.push(current); current = ''; currentType = '' }
  }

  function leadingSpaces(line) {
    const match = line.match(/^(\s*)/)
    return match ? match[1].length : 0
  }

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i]
    const trimmed = line.trim()
    const indent = leadingSpaces(line)

    if (!trimmed) {
      flush()
      if (mdLines.length > 0 && mdLines[mdLines.length - 1].startsWith('|')) mdLines.push('')
      continue
    }

    if (trimmed.startsWith('|')) { flush(); mdLines.push(trimmed); continue }
    if (/^\d+$/.test(trimmed)) continue

    const subHeadingMatch = trimmed.match(/^(\d+(?:\.\d+){2,})\s{1,3}(.+)/)
    if (subHeadingMatch && indent < 4) {
      flush()
      const depth = subHeadingMatch[1].split('.').length
      const prefix = depth <= 3 ? '##' : '###'
      mdLines.push(`\n${prefix} ${subHeadingMatch[2].trim()}\n`)
      continue
    }

    const numberedMatch = trimmed.match(/^(\d+)\.\s{2,}(.*)/)
    if (numberedMatch && indent < 4) {
      flush()
      current = `${numberedMatch[1]}. ${numberedMatch[2]}`
      currentType = 'num'
      continue
    }

    const subItemMatch = trimmed.match(/^([a-z])\.\s+(.*)/)
    if (subItemMatch && indent >= 4) {
      flush()
      current = `   ${subItemMatch[1]}. ${subItemMatch[2]}`
      currentType = 'sub'
      continue
    }

    const bulletMatch = trimmed.match(/^[•·]\s+(.*)/)
    if (bulletMatch) {
      flush()
      current = `- ${bulletMatch[1]}`
      currentType = 'bullet'
      continue
    }

    if (trimmed.endsWith(':') && trimmed.length < 50 && indent < 4 && !/^\d/.test(trimmed)) {
      flush()
      mdLines.push('')
      mdLines.push(trimmed)
      continue
    }

    if (current) {
      if (currentType === 'sub' && indent >= 4) { current += ' ' + trimmed; continue }
      if (currentType === 'num' && indent < 4) { current += ' ' + trimmed; continue }
      if (currentType === 'bullet' && indent >= 4) { current += ' ' + trimmed; continue }
      if (currentType === 'para') { current += ' ' + trimmed; continue }
    }

    flush()
    current = trimmed
    currentType = 'para'
  }
  flush()

  let result = mdLines.join('\n')
  result = result.replace(/\n{3,}/g, '\n\n')
  result = result.replace(/  +/g, ' ')
  return result.trim()
}

function extractText(sections) {
  console.log('\n── Step 2: Extracting text from PDF ──')
  console.log('Reading:', PDF_PATH)

  const rawText = extractPdfText(PDF_PATH)
  const fullText = rawText.replace(/\f/g, '')
  console.log(`  Extracted: ${fullText.length} characters`)

  const textMap = new Map()

  const chapterDefs = [
    { ch: 1, pattern: /^Legal Statement\s*$/m },
    { ch: 2, pattern: /^Product Overview\s*$/m },
    { ch: 3, pattern: /^Preparation Before First Use\s*$/m },
    { ch: 4, pattern: /^Product Parameters\s*$/m },
    { ch: 5, pattern: /^Troubleshooting\s*$/m },
    { ch: 6, pattern: /^Product Transportation\s*$/m },
    { ch: 7, pattern: /^Hazardous Substances/m },
    { ch: 8, pattern: /^Warranty Instructions\s*$/m },
  ]

  const chapterOffsets = new Map()
  for (const { ch, pattern } of chapterDefs) {
    let lastMatch = null
    let searchFrom = 0
    while (true) {
      const remaining = fullText.substring(searchFrom)
      const m = remaining.match(pattern)
      if (!m) break
      lastMatch = { index: searchFrom + m.index }
      searchFrom = searchFrom + m.index + m[0].length
    }
    if (lastMatch) chapterOffsets.set(ch, lastMatch.index)
  }

  for (const section of sections) {
    const chapterStart = chapterOffsets.get(section.chapter) || 0
    const searchRegion = fullText.substring(chapterStart)
    const headingMatch = section.pattern.exec(searchRegion)
    if (!headingMatch) {
      console.warn(`  Warning: "${section.title}" not found, skipping ${section.file}`)
      continue
    }

    const startPos = chapterStart + headingMatch.index + headingMatch[0].length
    const endPos = findPatternPos(fullText, startPos, section.endBefore)
    const rawContent = fullText.substring(startPos, endPos)

    const tableProcessed = processTablesInRawText(rawContent, section.tables)
    const mdContent = convertToMarkdown(tableProcessed)

    textMap.set(section.file, `# ${section.title}\n\n${mdContent}\n`)
    console.log(`  ${section.file}: ${mdContent.length} chars`)
  }

  return textMap
}

// ─── Step 3: Merge (text + images → final markdown) ────────────────────────

function buildImageRefs(filenames, alts) {
  return filenames.map((f, i) => {
    const alt = alts && alts[i] ? alts[i] : ''
    return `![${alt}](/images/aegis-edu/${f})`
  }).join('\n\n')
}

function insertImages(markdown, section, imageMap) {
  if (!section.images || section.images.length === 0) return markdown
  let result = markdown
  for (const rule of section.images) {
    const filenames = imageMap.get(rule.name) || []
    if (filenames.length === 0) continue
    const refs = buildImageRefs(filenames, rule.alts)
    if (rule.position === 'start') {
      const titleEnd = result.indexOf('\n\n')
      if (titleEnd !== -1) result = result.substring(0, titleEnd + 2) + refs + '\n\n' + result.substring(titleEnd + 2)
    } else if (rule.position === 'end') {
      result = result.trimEnd() + '\n\n' + refs + '\n'
    } else if (rule.after) {
      const lines = result.split('\n')
      const targetIdx = lines.findIndex(l => l.includes(rule.after))
      if (targetIdx !== -1) {
        let insertIdx = targetIdx + 1
        if (rule.after.startsWith('## ')) {
          for (let j = targetIdx + 1; j < lines.length; j++) {
            if (lines[j].startsWith('## ') || lines[j].startsWith('# ')) { insertIdx = j; break }
            insertIdx = j + 1
          }
          while (insertIdx > targetIdx + 1 && lines[insertIdx - 1].trim() === '') insertIdx--
        }
        lines.splice(insertIdx, 0, '', refs, '')
        result = lines.join('\n')
      } else {
        result = result.trimEnd() + '\n\n' + refs + '\n'
      }
    }
  }
  result = result.replace(/\n{3,}/g, '\n\n')
  return result
}

async function mergeAndWrite(textMap, imageMap, sections) {
  console.log('\n── Step 3: Merging text + images ──')
  await fs.mkdir(PAGES_DIR, { recursive: true })
  for (const section of sections) {
    const text = textMap.get(section.file)
    if (!text) continue
    const final = insertImages(text, section, imageMap)
    const outPath = path.join(PAGES_DIR, section.file)
    await fs.writeFile(outPath, final, 'utf-8')
    const imageCount = (section.images || []).reduce((sum, r) => sum + (imageMap.get(r.name) || []).length, 0)
    const imageInfo = imageCount > 0 ? ` + ${imageCount} image(s)` : ''
    console.log(`  Written: ${section.file}${imageInfo}`)
  }
}

// ─── CLI ────────────────────────────────────────────────────────────────────

async function main() {
  const args = process.argv.slice(2)
  const textOnly = args.includes('--text-only')
  const imagesOnly = args.includes('--images-only')
  const chapterIdx = args.indexOf('--chapter')
  const chapterFilter = chapterIdx !== -1 ? Number(args[chapterIdx + 1]) : null
  const sections = chapterFilter != null ? SECTIONS.filter(s => s.chapter === chapterFilter) : SECTIONS

  console.log('╔══════════════════════════════════════════════════╗')
  console.log('║  FX Aegis EDU: Source-to-Markdown Pipeline       ║')
  console.log('║  PDF (text) + Word (images) → Markdown           ║')
  console.log('╚══════════════════════════════════════════════════╝')

  if (chapterFilter != null) console.log(`\n  Filtering: Chapter ${chapterFilter} only (${sections.length} sections)`)

  if (imagesOnly) {
    await extractImages(sections)
    console.log('\n✓ Images extracted. Markdown files not modified.')
    return
  }

  let imageMap = new Map()
  if (!textOnly) imageMap = await extractImages(sections)
  else console.log('\n── Skipping image extraction (--text-only) ──')

  const textMap = extractText(sections)
  await mergeAndWrite(textMap, imageMap, sections)
  console.log('\n✓ Done! Files written to src/content/pages/aegis-edu/')
}

main().catch(err => { console.error('Error:', err); process.exit(1) })
