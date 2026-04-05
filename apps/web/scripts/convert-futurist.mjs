#!/usr/bin/env node
/**
 * convert-futurist.mjs — Source-to-markdown pipeline for FF Futurist manual
 *
 * Hybrid approach: PDF for text extraction, Word for image extraction.
 *
 * Prerequisites:
 *   brew install poppler   (provides pdftotext)
 *   npm install             (provides mammoth)
 *
 * Usage:
 *   npm run convert:futurist              # full pipeline (text + images)
 *   npm run convert:futurist:text         # text only
 *   npm run convert:futurist:images       # images only
 *
 * Source files:
 *   src/content/source/futurist.pdf   — text source
 *   src/content/source/futurist.docx  — image source
 *
 * Output:
 *   src/content/pages/futurist-ultra/*.md   — markdown files
 *   public/images/futurist-ultra/*          — extracted images
 */

import { promises as fs } from 'node:fs'
import path from 'node:path'
import { execSync } from 'node:child_process'
import mammoth from 'mammoth'

// ─── Paths ──────────────────────────────────────────────────────────────────

const ROOT = path.resolve(import.meta.dirname, '..')
const PDF_PATH = path.join(ROOT, 'src/content/source/futurist.pdf')
const DOCX_PATH = path.join(ROOT, 'src/content/source/futurist.docx')
const PAGES_DIR = path.join(ROOT, 'src/content/pages/futurist-ultra')
const IMAGES_DIR = path.join(ROOT, 'public/images/futurist-ultra')

// ─── Section Definitions ────────────────────────────────────────────────────

const SECTIONS = [
  // ── Foreword ──────────────────────────────────────────────────────────────
  {
    chapter: 0,
    file: 'foreword.md',
    title: 'Foreword',
    pattern: /^Foreword\s*$/m,
    endBefore: /^1\.\s+Safety Protection Measures/m,
  },

  // ── Chapter 1: Safety Protection Measures ─────────────────────────────────
  {
    chapter: 1,
    file: 'safety-guide.md',
    title: 'Safety Guide',
    pattern: /^1\.1\s+Safety Guide\s*$/m,
    endBefore: /^1\.2\s/m,
  },
  {
    chapter: 1,
    file: 'precautions.md',
    title: 'Precautions for Use',
    pattern: /^1\.2\s+Precautions for Use\s*$/m,
    endBefore: /^1\.3\s/m,
  },
  {
    chapter: 1,
    file: 'maintenance-guidelines.md',
    title: 'Maintenance and Management Guidelines',
    pattern: /^1\.3\s+Maintenance and Management Guidelines\s*$/m,
    endBefore: /^2\.\s{1,2}[A-Z]/m,
  },

  // ── Chapter 2: Product Overview ───────────────────────────────────────────
  {
    chapter: 2,
    file: 'product-introduction.md',
    title: 'Product Introduction',
    pattern: /^2\.1\s+Product Introduction\s*$/m,
    endBefore: /^3\.\s{1,2}[A-Z]/m,
  },

  // ── Chapter 3: Quick Start Guide ──────────────────────────────────────────
  {
    chapter: 3,
    file: 'startup.md',
    title: 'Startup',
    pattern: /^\s*I\.\s+Startup\s*$/m,
    endBefore: /^\s*II\.\s+Shutdown/m,
    images: [
      {
        position: 'end', headingId: 'heading_16', endHeadingId: 'heading_17', name: 'startup',
        alts: [
          'Controller power button',
          'Startup wizard',
          'Lift the robot',
          'Install the battery',
          'Power button',
          'Self-inspection complete',
          'Connect to the robot',
          'Preparing to stand',
          "Robot's feet fully touch the ground",
          'Self-standing',
          'Startup complete',
        ],
      },
    ],
  },
  {
    chapter: 3,
    file: 'shutdown.md',
    title: 'Shutdown',
    pattern: /^\s*II\.\s+Shutdown\s*$/m,
    endBefore: /^\s*III\.\s+Motion/m,
  },
  {
    chapter: 3,
    file: 'motion-control.md',
    title: 'Motion Control',
    pattern: /^\s*III\.\s+Motion control\s*$/m,
    endBefore: /^\s*IV\.\s+Charging/m,
    images: [
      { position: 'end', headingId: 'heading_19', endHeadingId: 'heading_20', name: 'walking-prep',
        alts: ['RC_Action', 'Switch to walking mode'] },
      { position: 'end', headingId: 'heading_20', endHeadingId: 'heading_21', name: 'remote-walking',
        alts: ['Remote walking', 'Controller buttons'] },
      { position: 'end', headingId: 'heading_21', endHeadingId: 'heading_22', name: 'action-display',
        alts: ['Action Library Call', 'Action List'] },
    ],
  },
  {
    chapter: 3,
    file: 'charging.md',
    title: 'Charging & Battery Swapping',
    pattern: /^\s*IV\.\s+Charging/m,
    endBefore: /^4\.\s{1,2}[A-Z]/m,
    images: [
      { position: 'end', headingId: 'heading_23', endHeadingId: 'heading_24', name: 'charging',
        alts: ['Charging port'] },
      { position: 'end', headingId: 'heading_24', endHeadingId: 'heading_25', name: 'battery-swapping',
        alts: ['Remove battery'] },
    ],
  },

  // ── Chapter 4: Maintenance and Suggestion ─────────────────────────────────
  {
    chapter: 4,
    file: 'routine-maintenance.md',
    title: 'Routine Maintenance',
    pattern: /^4\.1\s+Routine Maintenance\s*$/m,
    endBefore: /^4\.2\s/m,
  },
  {
    chapter: 4,
    file: 'battery-maintenance.md',
    title: 'Battery Maintenance',
    pattern: /^4\.2\s+Battery Maintenance\s*$/m,
    endBefore: /^5\.\s{1,2}[A-Z]/m,
  },

  // ── Chapter 5: Product Specifications ─────────────────────────────────────
  {
    chapter: 5,
    file: 'product-composition.md',
    title: 'Product Composition',
    pattern: /^5\.1\s+Product Composition\s*$/m,
    endBefore: /^5\.2\s/m,
    images: [
      { position: 'end', headingId: 'heading_29', endHeadingId: 'heading_30', name: 'product-composition',
        alts: ['Product Composition'] },
    ],
  },
  {
    chapter: 5,
    file: 'basic-parameters.md',
    title: 'Basic Parameters',
    pattern: /^5\.2\s+Basic Parameters\s*$/m,
    endBefore: /^5\.3\s/m,
    tables: [
      {
        headerPattern: /Primary\s{2,}Secondar/,
        replaceToEnd: true,
        hardcoded: [
          '| Primary Category | Secondary Category | Entry | Specifications |',
          '| --- | --- | --- | --- |',
          '| Basic Product Information | | Height | 169cm |',
          '| | | Dimensions | 169(H)×75(W)×30(L)cm |',
          '| | | Net Weight | ≈69kg |',
          '| | | Active Degrees of Freedom (DOF) | Arms: 7×2 DOF, Legs: 6×2 DOF, Head: 2 DOF, Dexterous Hands: 6×2 DOF |',
          '| Product Features | Electrical Performance | Battery Life | 2h |',
          '| | | Battery Capacity | 14.4Ah |',
          '| | | Charging Time | 2h |',
          '| | | Charging Voltage | 48V DC |',
          '| | | Charging Current | 13A |',
          '| | | Cell Type | NMC (Lithium Nickel Manganese Cobalt Oxide) |',
          '| | Charging Mode | Battery | CC-CV |',
          '| | | Remote Control | Blind charging |',
          '| | Remote Control Charger Specifications | Charger Model | UY600L |',
          '| | | Input Cable Specifications | 3(0.75~1.5) mm² |',
          '| | | Battery Types | LFP (Lithium Iron Phosphate), NCM (Nickel Cobalt Manganese), L-A (Lead-Acid) |',
          '| | Charging Environment Temperature | | Operating: -20℃ ~ +40℃; Storage: -40℃ ~ +70℃ |',
          '| Environmental Adaptability | Operating Temperature & Humidity | | 0°C to 40°C, 10%–90% RH (No condensation) |',
          '| | Storage Temperature & Humidity | | -20°C to 70°C, 10%–90% RH (No condensation) |',
          '| Site Adaptability | Minimum Passage Width | | Achieved: 900mm (Front), 1000mm (Turning); Target: 600mm (Sideways), 800mm (Front) |',
          '| | Maximum Obstacle Height | | Not currently supported; Target: 20mm |',
          '| | Maximum Operating Slope | | 2% (Angle: 1.15°) |',
          '| Safety | Arm Collision Detection | | Supported |',
          '| | Maximum Obstacle Detection Distance | | 5m |',
          '| | Minimum Obstacle Detection Height | | Under development. Target: 5cm |',
          '| Operation & Interaction | Remote Control | | Wireless Remote Controller |',
          '| | Interactive Screen | | Facial interactive screen with emotive display |',
          '| | Microphone | | Array Microphone |',
          '| | Speaker | | Built-in Speaker |',
          '| | Indicator Light | | Status Indicator Light |',
          '| Product Capabilities | Perception | Environmental Perception | LiDAR ×1, Fisheye Camera ×2, RGBD Camera ×2, RGB Camera ×1 |',
          '| | Navigation | Positioning Accuracy | ±10cm, ±10° |',
          '| | | Navigation & Obstacle Avoidance | Supports real-time autonomous navigation and obstacle avoidance |',
          '| | Mobility | Maximum Speed | Current: 0.5m/s; Target: 0.8m/s |',
          '| | | Mobility Modes | Supports translation, diagonal movement, and in-place rotation |',
          '| | IoT Capability | Communication Protocol | TCP/IP |',
          '| | | Communication Module | Wi-Fi |',
          '| | Arm Specifications | Single-Arm Payload Capacity | 1kg |',
          '| | | End-Effector Linear Speed | 1m/s |',
          '| | | Arm Workspace | J1(Shoulder pitch): ±170°; J2(Shoulder roll): -30°~95°; J3(Shoulder yaw): ±170°; J4(Elbow pitch): -1°~118°; J5(Wrist roll): ±170°; J6(Wrist pitch): ±45°; J7(Wrist yaw): ±30° |',
          '| | Leg Specifications | Leg Workspace | J1(Hip roll): -37~40°; J2(Hip yaw): ±75°; J3(Hip pitch): -50°~110°; J4(Knee pitch): -5°~140°; J5(Ankle pitch): -30°~52°; J6(Ankle roll): ±28° |',
          '| | Head Specifications | Head Workspace | Pitch Joint: ±23°; Yaw Joint: ±45° |',
          '',
          'The machine includes WIFI, 4G, Bluetooth, hotspot and LoRa wireless modules.',
          '',
          '| Wireless Module | Operating Frequency Range | Maximum Transmitting Power |',
          '| --- | --- | --- |',
          '| 2.4G WIFI | 2.400 GHz to 2.4835 GHz | 20dBm |',
          '| 5G WIFI | 5180MHz-5320MHz, 5500MHz-5825MHz | 22dBm |',
          '| 4G LTE | 824MHz to 2690MHz | 23dBm |',
          '| Bluetooth | 2400 MHz - 2483.5 MHz | 20dBm |',
          '| LoRa | 868MHz to 915MHz | 22dBm |',
        ].join('\n'),
      },
    ],
  },
  {
    chapter: 5,
    file: 'workspace.md',
    title: 'Workspace',
    pattern: /^5\.3\s+Workspace\s*$/m,
    endBefore: /^6\.\s/m,
    images: [
      { position: 'end', headingId: 'heading_31', endHeadingId: 'heading_32', name: 'workspace',
        alts: ['Arm Workspace', 'Leg Workspace', 'Head Workspace'] },
    ],
  },

  // ── Chapter 6: Product Label Description ──────────────────────────────────
  {
    chapter: 6,
    file: 'product-labels.md',
    title: 'Product Label Description',
    pattern: /^6\.\s+Product label description\s*$/m,
    endBefore: /^7\.?\s*Specifications/m,
    images: [
      { position: 'end', headingId: 'heading_32', endHeadingId: 'heading_33', name: 'product-labels',
        alts: ['WEEE symbol', 'CE mark', 'FCC compliance', 'Safety notice'] },
    ],
  },

  // ── Chapter 7: Specifications ─────────────────────────────────────────────
  {
    chapter: 7,
    file: 'rf-specifications.md',
    title: 'RF Specifications',
    pattern: /^7\.?\s*Specifications\s*$/m,
    endBefore: /^8\.\s/m,
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
    if (i < len && spaceLen >= 2) {
      positions.push(i)
    }
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
      if (currentRow) {
        rows.push(currentRow)
        currentRow = null
      }
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

    if (firstColHasContent && currentRow) {
      rows.push(currentRow)
      currentRow = null
    }

    if (!currentRow) {
      currentRow = cells.slice()
    } else {
      for (let c = 0; c < numCols; c++) {
        if (cells[c]) {
          currentRow[c] = currentRow[c] ? currentRow[c] + ' ' + cells[c] : cells[c]
        }
      }
    }
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
      if (/^\d+\.\d+(\.\d+)*\s/.test(lines[j].trim())) {
        return j
      }
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
        if (replacements.some(r => i >= r.startLine && i < r.endLine)) {
          matchCount++
          continue
        }
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

    if (imageFiles.length > 0) {
      console.log(`  ${rule.name}: ${imageFiles.length} image(s)`)
    } else {
      console.log(`  ${rule.name}: no images found`)
    }
  }

  return imageMap
}

// ─── Step 2: Text Extraction (PDF → markdown) ──────────────────────────────

function extractPdfText(pdfPath) {
  try {
    return execSync(`pdftotext -layout "${pdfPath}" -`, {
      encoding: 'utf-8',
      maxBuffer: 50 * 1024 * 1024,
    })
  } catch (err) {
    console.error('Error: pdftotext failed. Is poppler installed?')
    console.error('  Install with: brew install poppler')
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
    if (current.trim()) {
      mdLines.push(current)
      current = ''
      currentType = ''
    }
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
      if (mdLines.length > 0 && mdLines[mdLines.length - 1].startsWith('|')) {
        mdLines.push('')
      }
      continue
    }

    if (trimmed.startsWith('|')) {
      flush()
      mdLines.push(trimmed)
      continue
    }

    if (/^\d+$/.test(trimmed)) continue

    // Sub-section headings: "2.2.1 Title" or Roman numeral "III.I Title"
    const subHeadingMatch = trimmed.match(/^(\d+(?:\.\d+){2,})\s{1,3}(.+)/)
    if (subHeadingMatch && indent < 4) {
      flush()
      const depth = subHeadingMatch[1].split('.').length
      const prefix = depth <= 3 ? '##' : '###'
      mdLines.push(`\n${prefix} ${subHeadingMatch[2].trim()}\n`)
      continue
    }

    // Roman numeral sub-headings within Chapter 3: "III.I Title", "III.II Title"
    const romanSubMatch = trimmed.match(/^((?:I{1,3}|IV|V))\.((?:I{1,3}|IV|V)?)\s+(.+)/)
    if (romanSubMatch && indent < 8) {
      flush()
      mdLines.push(`\n## ${romanSubMatch[3].trim()}\n`)
      continue
    }

    // "Step N:" headings
    const stepMatch = trimmed.match(/^Step\s+(\d+):\s+(.*)/)
    if (stepMatch && indent < 4) {
      flush()
      mdLines.push(`\n### Step ${stepMatch[1]}: ${stepMatch[2].trim()}\n`)
      continue
    }

    // Numbered list items
    const numberedMatch = trimmed.match(/^(\d+)\.\s{2,}(.*)/)
    if (numberedMatch && indent < 4) {
      flush()
      current = `${numberedMatch[1]}. ${numberedMatch[2]}`
      currentType = 'num'
      continue
    }

    // Sub-items
    const subItemMatch = trimmed.match(/^([a-z])\.\s+(.*)/)
    if (subItemMatch && indent >= 4) {
      flush()
      current = `   ${subItemMatch[1]}. ${subItemMatch[2]}`
      currentType = 'sub'
      continue
    }

    // Bullet points
    const bulletMatch = trimmed.match(/^[•·]\s+(.*)/)
    if (bulletMatch) {
      flush()
      current = `- ${bulletMatch[1]}`
      currentType = 'bullet'
      continue
    }

    // Label lines
    if (trimmed.endsWith(':') && trimmed.length < 50 && indent < 4 && !/^\d/.test(trimmed)) {
      flush()
      mdLines.push('')
      mdLines.push(trimmed)
      continue
    }

    // Continuation lines
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

  // Build chapter offsets (find LAST occurrence to skip TOC)
  const chapterOffsets = new Map()
  const chapterDefs = [
    { ch: 0, pattern: /^Foreword\s*$/m },
    { ch: 1, pattern: /^1\.\s{1,2}Safety/m },
    { ch: 2, pattern: /^2\.\s{1,2}Product/m },
    { ch: 3, pattern: /^3\.\s{1,2}Quick/m },
    { ch: 4, pattern: /^4\.\s{1,2}Maintenance/m },
    { ch: 5, pattern: /^5\.\s{1,2}Product/m },
    { ch: 6, pattern: /^6\.\s{1,2}Product/m },
    { ch: 7, pattern: /^7\.?\s*Specifications/m },
  ]

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
    return `![${alt}](/images/futurist-ultra/${f})`
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
      if (titleEnd !== -1) {
        result = result.substring(0, titleEnd + 2) + refs + '\n\n' + result.substring(titleEnd + 2)
      }
    } else if (rule.position === 'end') {
      result = result.trimEnd() + '\n\n' + refs + '\n'
    } else if (rule.after) {
      const lines = result.split('\n')
      const targetIdx = lines.findIndex(l => l.includes(rule.after))
      if (targetIdx !== -1) {
        let insertIdx = targetIdx + 1

        if (rule.after.startsWith('## ')) {
          for (let j = targetIdx + 1; j < lines.length; j++) {
            if (lines[j].startsWith('## ') || lines[j].startsWith('# ')) {
              insertIdx = j
              break
            }
            insertIdx = j + 1
          }
          while (insertIdx > targetIdx + 1 && lines[insertIdx - 1].trim() === '') {
            insertIdx--
          }
        } else {
          insertIdx = targetIdx + 1
        }

        lines.splice(insertIdx, 0, '', refs, '')
        result = lines.join('\n')
      } else {
        console.warn(`    Warning: "${rule.after}" not found in ${section.file}, appending at end`)
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

    const imageCount = (section.images || []).reduce((sum, r) => {
      return sum + (imageMap.get(r.name) || []).length
    }, 0)
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

  const sections = chapterFilter != null
    ? SECTIONS.filter(s => s.chapter === chapterFilter)
    : SECTIONS

  console.log('╔══════════════════════════════════════════════════╗')
  console.log('║  FF Futurist: Source-to-Markdown Pipeline        ║')
  console.log('║  PDF (text) + Word (images) → Markdown           ║')
  console.log('╚══════════════════════════════════════════════════╝')

  if (chapterFilter != null) {
    console.log(`\n  Filtering: Chapter ${chapterFilter} only (${sections.length} sections)`)
  }

  if (imagesOnly) {
    const imageMap = await extractImages(sections)
    console.log('\n✓ Images extracted. Markdown files not modified.')
    return
  }

  let imageMap = new Map()

  if (!textOnly) {
    imageMap = await extractImages(sections)
  } else {
    console.log('\n── Skipping image extraction (--text-only) ──')
  }

  const textMap = extractText(sections)

  await mergeAndWrite(textMap, imageMap, sections)

  console.log('\n✓ Done! Files written to src/content/pages/futurist-ultra/')
}

main().catch(err => {
  console.error('Error:', err)
  process.exit(1)
})
