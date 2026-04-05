#!/usr/bin/env node
/**
 * convert-aegis.mjs — Source-to-markdown pipeline for FX Aegis Ultra manual
 *
 * Usage:
 *   npm run convert:aegis              # full pipeline (text + images)
 *   npm run convert:aegis:text         # text only
 *   npm run convert:aegis:images       # images only
 *
 * Source:  src/content/source/aegisultra.pdf + aegisultra.docx
 * Output:  src/content/pages/aegis-ultra/*.md  +  public/images/aegis-ultra/*
 */

import { promises as fs } from 'node:fs'
import path from 'node:path'
import { execSync } from 'node:child_process'
import mammoth from 'mammoth'

const ROOT = path.resolve(import.meta.dirname, '..')
const PDF_PATH = path.join(ROOT, 'src/content/source/aegisultra.pdf')
const DOCX_PATH = path.join(ROOT, 'src/content/source/aegisultra.docx')
const PAGES_DIR = path.join(ROOT, 'src/content/pages/aegis-ultra')
const IMAGES_DIR = path.join(ROOT, 'public/images/aegis-ultra')

// ─── Section Definitions ────────────────────────────────────────────────────

const SECTIONS = [
  // ── Legal & Safety ────────────────────────────────────────────────────────
  {
    chapter: 1,
    file: 'legal-statement.md',
    title: 'Legal Statement',
    pattern: /^Legal Statement\s*$/m,
    endBefore: /^Usage Restrictions & Safety Notes/m,
  },
  {
    chapter: 1,
    file: 'usage-restrictions.md',
    title: 'Usage Restrictions & Safety Notes',
    pattern: /^Usage Restrictions & Safety Notes\s*$/m,
    endBefore: /^Battery & Charging\s*$/m,
  },
  {
    chapter: 1,
    file: 'battery-charging.md',
    title: 'Battery & Charging Precautions',
    pattern: /^Battery & Charging\s*$/m,
    endBefore: /^Product Overview & Components/m,
  },

  // ── Product Description ───────────────────────────────────────────────────
  {
    chapter: 2,
    file: 'product-overview.md',
    title: 'Product Overview & Components',
    pattern: /^Product Overview & Components\s*$/m,
    endBefore: /^Expansion Interface Ports/m,
    images: [
      { position: 'start', headingId: 'heading_12', endHeadingId: 'heading_13', name: 'product-overview',
        alts: ['FX Aegis Ultra'] },
    ],
  },
  {
    chapter: 2,
    file: 'expansion-interface.md',
    title: 'Expansion Interface Ports',
    pattern: /^Expansion Interface Ports\s*$/m,
    endBefore: /^Lighting Effects Description/m,
    images: [
      { position: 'start', headingId: 'heading_13', endHeadingId: 'heading_14', name: 'expansion-interface',
        alts: ['Expansion interface overview', 'Expansion interface detail'] },
    ],
    tables: [
      {
        headerPattern: /No\.\s{2,}Interface\s{2,}Qty\s{2,}Description/,
        replaceToEnd: true,
        hardcoded: [
          '| No. | Interface | Qty | Description |',
          '| --- | --- | --- | --- |',
          '| 1 | Ethernet Port | 1 | RJ45 Interface: Supports 1,000 Mbps transmission for high-speed data communication. Used for network connectivity, remote monitoring, data transmission and other related applications. |',
          '| 2 | USB Port | 2 | Type-A interface: used to connect external storage devices, cameras, sensors, and other USB devices. It provides high-speed data transfer and power supply. |',
          '| 3 | DC Power Port | 2 | Standard DC Power Interface: Provides stable power supply, supporting 12V and 24V voltage outputs, meeting the power requirements of the robotic dog and its mounted devices. |',
          '| 4 | SBUS Port | 1 | Standard SBUS Interface: used to connect remote controller receivers or other communication devices supporting the SBUS protocol, enabling precise remote control command transmission. |',
          '| 5 | UART Port | 1 | Standard UART interface: Used to connect embedded systems, communications devices, or other devices supporting the UART protocol. It facilitates data exchange and control between devices through asynchronous serial communication. |',
        ].join('\n'),
      },
    ],
  },
  {
    chapter: 2,
    file: 'lighting-effects.md',
    title: 'Lighting Effects Description',
    pattern: /^Lighting Effects Description\s*$/m,
    endBefore: /^Power Supply Introduction/m,
    images: [
      { position: 'start', headingId: 'heading_14', endHeadingId: 'heading_15', name: 'lighting-effects',
        alts: ['Tail light location', 'Tail light detail'] },
    ],
    tables: [
      {
        headerPattern: /Light Color\/Pattern\s{2,}Meaning/,
        replaceToEnd: true,
        hardcoded: [
          '| Light Color/Pattern | Meaning |',
          '| --- | --- |',
          '| Blue — Always On | Boot complete |',
          '| Blue — Flashing | Rebooting |',
          '| White — Always On | Range Mode enabled — improved movement & special skills unlocked |',
          '| Green — Always On | Tracking Mode enabled |',
          '| Yellow — Always On | Battery charge is critically low — Rage Mode unavailable |',
          '| Yellow — Flashing | Battery below 5% — charge immediately |',
          '| Red — Always On | Joints too hot — needs cooling |',
          '| Red — Flashing | System abnormal — contact after-sales service |',
        ].join('\n'),
      },
    ],
  },

  // ── Power Supply ──────────────────────────────────────────────────────────
  {
    chapter: 3,
    file: 'power-supply.md',
    title: 'Power Supply Introduction',
    pattern: /^Power Supply Introduction\s*$/m,
    endBefore: /^Preparation Before First Use/m,
    images: [
      { position: 'end', headingId: 'heading_17', endHeadingId: 'heading_18', name: 'battery-idle',
        alts: ['Battery LED idle/discharge chart', 'Battery LED idle table'] },
      { position: 'end', headingId: 'heading_18', endHeadingId: 'heading_19', name: 'battery-charge',
        alts: ['Battery LED charge state'] },
      { position: 'end', headingId: 'heading_19', endHeadingId: 'heading_20', name: 'power-adapter',
        alts: ['Power adapter front', 'Power adapter back'] },
    ],
    tables: [
      {
        headerPattern: /No\.\s{2,}SOC\s*\(%\)\s{2,}LED\s*1\s{2,}LED\s*2\s{2,}LED\s*3\s{2,}LED\s*4/,
        matchIndex: 0,
        hardcoded: [
          '| No. | SOC (%) | LED 1 | LED 2 | LED 3 | LED 4 |',
          '| --- | --- | --- | --- | --- | --- |',
          '| 1 | 0 – 14% | Flashing | OFF | OFF | OFF |',
          '| 2 | 15 – 24% | ON | OFF | OFF | OFF |',
          '| 3 | 25 – 49% | ON | ON | OFF | OFF |',
          '| 4 | 50 – 74% | ON | ON | ON | OFF |',
          '| 5 | 75 – 100% | ON | ON | ON | ON |',
        ].join('\n'),
      },
      {
        headerPattern: /No\.\s{2,}SOC\s*\(%\)\s{2,}LED\s*1\s{2,}LED\s*2\s{2,}LED\s*3\s{2,}LED\s*4/,
        matchIndex: 1,
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

  // ── Preparation & Remote Control ──────────────────────────────────────────
  {
    chapter: 4,
    file: 'first-use.md',
    title: 'Preparation Before First Use',
    pattern: /^Preparation Before First Use\s*$/m,
    endBefore: /^Remote Control User Guide/m,
  },
  {
    chapter: 4,
    file: 'remote-control.md',
    title: 'Remote Control User Guide',
    pattern: /^Remote Control User Guide\s*$/m,
    endBefore: /^Product Parameters\s*$/m,
    images: [
      { position: 'end', headingId: 'heading_22', endHeadingId: 'heading_23', name: 'rc-intro',
        alts: ['Controller power on', 'Smart Robot Controller app', 'APP main page', 'System settings',
               'Connection screen', 'WiFi selection', 'WiFi connected', 'Connection successful'] },
      { position: 'end', headingId: 'heading_23', endHeadingId: 'heading_24', name: 'rc-operations',
        alts: ['Operations mode table'] },
      { position: 'end', headingId: 'heading_24', endHeadingId: 'heading_25', name: 'rc-lab-mode',
        alts: ['Lab mode step 1', 'Lab mode step 2', 'Lab mode confirm', 'Lab mode enabled'] },
      { position: 'end', headingId: 'heading_25', endHeadingId: 'heading_26', name: 'rc-functions',
        alts: ['Basic control entry', 'Control page', 'Screen recording start', 'Screen recording stop'] },
    ],
    tables: [
      {
        headerPattern: /Normal\/laboratory mode switch/,
        replaceToEnd: false,
        hardcoded: [
          '| Category | Action | Normal Mode | Lab Mode |',
          '| --- | --- | --- | --- |',
          '| Normal/laboratory mode switch | | APP | APP |',
          '| General Actions | Stand | APP | APP |',
          '| | Stand Damping (Slowly Lie Down) | APP | APP |',
          '| | Lie Down / Emergency Stop | L1+R1 or APP | L1+R1 or APP |',
          '| Movement actions | Forward / Backward / Left / Right | Left Stick | Left Stick |',
          '| In-place Actions | Idle/Moving Switch | APP | APP |',
          '| | Pitch Adjustment | Push Right Joystick Fwd/Back | Push Right Joystick Fwd/Back |',
          '| | Horizontal Turn | Push Right Joystick L/R | Push Right Joystick L/R |',
          '| | Left/Right Head Tilt | Y/A | Y/A |',
          '| | High / Low Posture | X/B | X/B |',
          '| Special Actions | Jump Up | — | APP |',
          '| | Forward Jump | — | APP |',
          '| | Backflip | — | APP |',
          '| | Waving Greeting | — | APP |',
          '| | Biped Standing | — | APP |',
        ].join('\n'),
      },
    ],
  },

  // ── Product Parameters ────────────────────────────────────────────────────
  {
    chapter: 5,
    file: 'product-parameters.md',
    title: 'Product Parameters',
    pattern: /^Product Parameters\s*$/m,
    endBefore: /^Troubleshooting\s*$/m,
    images: [
      { position: 'end', headingId: 'heading_26', endHeadingId: 'heading_28', name: 'product-parameters',
        alts: ['Product parameters overview'] },
    ],
    tables: [
      {
        headerPattern: /Category\s{2,}Specification\s{2,}Value/,
        replaceToEnd: false,
        hardcoded: [
          '| Category | Specification | Value |',
          '| --- | --- | --- |',
          '| Basic Info | Material | Aluminum alloy + high-strength engineering plastic |',
          '| | Standing Dimensions (L×W×H) | 24.8" × 14.2" × 16.5" (630 × 360 × 420 mm) |',
          '| | Lying Down Dimensions (L×W×H) | 26.4" × 17.1" × 5.7" (670 × 435 × 145 mm) |',
          '| | Total Weight (with battery) | 35.3 lbs (16 kg) |',
          '| | Operating Temperature | 32°F – 104°F (0°C – 40°C) |',
          '| | Ingress Protection | IP54 |',
          '| Performance | Maximum Speed | 8.3 mph (3.7 m/s) |',
          '| | Effective Payload | 11.0 lbs (5 kg) |',
          '| | Continuous Stair-Climbing Height | 6.3 in (16 cm) |',
          '| | Maximum Climbing Angle | 30° standard / up to 40° maximum |',
          '| | Vertical Jump Height | 13.8 in (35 cm) |',
          '| Electrical | Battery | 4.6 Ah rated capacity, 43.2 V |',
          '| | Charging Duration | 1 hour |',
          '| | Battery Life (Operating) | 1 – 2 hours |',
          '| | Operating Range | 3.7 mi (6 km) |',
        ].join('\n'),
      },
    ],
  },

  // ── Troubleshooting ───────────────────────────────────────────────────────
  {
    chapter: 6,
    file: 'troubleshooting.md',
    title: 'Troubleshooting',
    pattern: /^Troubleshooting\s*$/m,
    endBefore: /^Transportation & Storage/m,
    images: [
      { position: 'end', headingId: 'heading_28', endHeadingId: 'heading_29', name: 'troubleshooting',
        alts: ['Troubleshooting reference'] },
    ],
    tables: [
      {
        headerPattern: /Frequently asked questions\s{2,}Treatment measure/,
        replaceToEnd: false,
        hardcoded: [
          '| Frequently Asked Questions | Treatment Measure |',
          '| --- | --- |',
          '| What if the remote control can\'t connect to the robot dog? | First, confirm that the robot dog has been started, and then confirm that no other version of the APP is running in the background of the remote control. If you still cannot connect to the robot dog, restart the robot dog and the APP and try to connect again. |',
          '| What if the handle operation of the connected robot dog has no response? | Make sure the handle is connected to the correct robot WiFi. If it is connected but still cannot control, wait 10 seconds and try again. If there is no response, restart the robot. |',
          '| Is it normal for a robot dog to stop moving on its own? | It may be that the robot dog\'s protection function is triggered. Please wait for 10 minutes and try again. If you still cannot control the robot dog to continue moving, please check whether the battery is sufficient first, and then check whether the handle signal is disconnected. |',
        ].join('\n'),
      },
    ],
  },

  // ── Transportation & Storage ──────────────────────────────────────────────
  {
    chapter: 7,
    file: 'transportation-storage.md',
    title: 'Transportation & Storage',
    pattern: /^Transportation & Storage\s*$/m,
    endBefore: /^\s+Hazardous Substances/m,
  },

  // ── Hazardous Substances ──────────────────────────────────────────────────
  {
    chapter: 8,
    file: 'hazardous-substances.md',
    title: 'Hazardous Substances Information',
    pattern: /Hazardous Substances\s*$/m,
    endBefore: /^Warranty Information/m,
    images: [
      { position: 'end', headingId: 'heading_30', endHeadingId: 'heading_31', name: 'hazardous-substances',
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
    chapter: 9,
    file: 'warranty.md',
    title: 'Warranty Information',
    pattern: /^Warranty Information\s*$/m,
    endBefore: /^___NEVER_MATCH___$/m,
    images: [
      { position: 'end', headingId: 'heading_31', endHeadingId: 'heading_33', name: 'warranty',
        alts: ['Warranty overview'] },
    ],
    tables: [
      {
        headerPattern: /Component\s{2,}Warranty Period\s{2,}Start of Warranty/,
        hardcoded: [
          '| Component | Warranty Period | Start of Warranty |',
          '| --- | --- | --- |',
          '| Whole Machine (Bionic Quadruped Robot) | 12 months | Upon activation (or 90 days after receipt if not activated) |',
          '| Motherboard | 12 months | Upon activation (or 90 days after receipt) |',
          '| Joint Module Motor | 12 months | Upon activation (or 90 days after receipt) |',
          '| Telecontroller (Screen) | 6 months | Upon activation (or 90 days after receipt) |',
          '| Charger | 6 months | Upon activation (or 90 days after receipt) |',
          '| Battery Cell | 6 months / 200 cycles | Upon activation (or 90 days after receipt) |',
          '| FPV Camera | 6 months | Upon activation (or 90 days after receipt) |',
        ].join('\n'),
      },
    ],
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
    if (i < len && (i - spaceStart) >= 2) positions.push(i)
  }
  positions[0] = 0
  return positions
}

function findTableEnd(lines, startLine) {
  let blanks = 0
  for (let j = startLine; j < lines.length; j++) {
    if (lines[j].trim() === '') { blanks++; if (blanks >= 3) return j - blanks + 1 }
    else { blanks = 0; if (/^\d+\.\d+(\.\d+)*\s/.test(lines[j].trim())) return j }
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
    }
  }
  replacements.sort((a, b) => b.startLine - a.startLine)
  const result = [...lines]
  for (const rep of replacements) result.splice(rep.startLine, rep.endLine - rep.startLine, ...rep.replacement.split('\n'))
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
  while ((m = headingRegex.exec(fullMd)) !== null) headings.push({ id: m[1], pos: m.index })
  console.log(`  Found ${headings.length} headings in Word document`)
  await fs.mkdir(IMAGES_DIR, { recursive: true })

  const extractionRules = []
  for (const section of sections) {
    if (!section.images) continue
    for (const rule of section.images)
      if (!extractionRules.find(r => r.headingId === rule.headingId && r.name === rule.name))
        extractionRules.push(rule)
  }

  const imageMap = new Map()
  for (const rule of extractionRules) {
    const headingIdx = headings.findIndex(h => h.id === rule.headingId)
    if (headingIdx === -1) { console.warn(`  Warning: ${rule.headingId} not found, skipping ${rule.name}`); imageMap.set(rule.name, []); continue }
    const startPos = headings[headingIdx].pos
    let endPos = fullMd.length
    if (rule.endHeadingId) { const endIdx = headings.findIndex(h => h.id === rule.endHeadingId); if (endIdx !== -1) endPos = headings[endIdx].pos }
    else if (headingIdx + 1 < headings.length) endPos = headings[headingIdx + 1].pos
    const sectionMd = fullMd.substring(startPos, endPos)
    const imgRegex = /!\[([^\]]*)\]\(data:image\/([^;]+);base64,([^)]+)\)/g
    let imgMatch, imageIndex = 0
    const imageFiles = []
    while ((imgMatch = imgRegex.exec(sectionMd)) !== null) {
      imageIndex++
      const ext = imgMatch[2] === 'x-emf' ? 'png' : imgMatch[2]
      const filename = `${rule.name}-${imageIndex}.${ext}`
      await fs.writeFile(path.join(IMAGES_DIR, filename), Buffer.from(imgMatch[3], 'base64'))
      imageFiles.push(filename)
    }
    imageMap.set(rule.name, imageFiles)
    console.log(`  ${rule.name}: ${imageFiles.length} image(s)`)
  }
  return imageMap
}

// ─── Step 2: Text Extraction (PDF → markdown) ──────────────────────────────

function extractPdfText(pdfPath) {
  try { return execSync(`pdftotext -layout "${pdfPath}" -`, { encoding: 'utf-8', maxBuffer: 50 * 1024 * 1024 }) }
  catch (err) { console.error('Error: pdftotext failed. Install with: brew install poppler'); throw err }
}

function findPatternPos(fullText, afterPos, pattern) {
  const remaining = fullText.substring(afterPos)
  const match = remaining.match(pattern)
  return match ? afterPos + match.index : fullText.length
}

function convertToMarkdown(rawText) {
  const lines = rawText.split('\n')
  const mdLines = []
  let current = '', currentType = ''
  function flush() { if (current.trim()) { mdLines.push(current); current = ''; currentType = '' } }
  function leadingSpaces(line) { const m = line.match(/^(\s*)/); return m ? m[1].length : 0 }

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i], trimmed = line.trim(), indent = leadingSpaces(line)
    if (!trimmed) { flush(); if (mdLines.length > 0 && mdLines[mdLines.length - 1].startsWith('|')) mdLines.push(''); continue }
    if (trimmed.startsWith('|')) { flush(); mdLines.push(trimmed); continue }
    if (/^\d+$/.test(trimmed)) continue

    const subHeadingMatch = trimmed.match(/^(\d+(?:\.\d+){2,})\s{1,3}(.+)/)
    if (subHeadingMatch && indent < 4) { flush(); const depth = subHeadingMatch[1].split('.').length; mdLines.push(`\n${depth <= 3 ? '##' : '###'} ${subHeadingMatch[2].trim()}\n`); continue }

    const numberedMatch = trimmed.match(/^(\d+)\.\s{2,}(.*)/)
    if (numberedMatch && indent < 4) { flush(); current = `${numberedMatch[1]}. ${numberedMatch[2]}`; currentType = 'num'; continue }

    const subItemMatch = trimmed.match(/^([a-z])\.\s+(.*)/)
    if (subItemMatch && indent >= 4) { flush(); current = `   ${subItemMatch[1]}. ${subItemMatch[2]}`; currentType = 'sub'; continue }

    const bulletMatch = trimmed.match(/^[•·]\s+(.*)/)
    if (bulletMatch) { flush(); current = `- ${bulletMatch[1]}`; currentType = 'bullet'; continue }

    if (trimmed.endsWith(':') && trimmed.length < 50 && indent < 4 && !/^\d/.test(trimmed)) { flush(); mdLines.push(''); mdLines.push(trimmed); continue }

    if (current) {
      if (currentType === 'sub' && indent >= 4) { current += ' ' + trimmed; continue }
      if (currentType === 'num' && indent < 4) { current += ' ' + trimmed; continue }
      if (currentType === 'bullet' && indent >= 4) { current += ' ' + trimmed; continue }
      if (currentType === 'para') { current += ' ' + trimmed; continue }
    }
    flush(); current = trimmed; currentType = 'para'
  }
  flush()
  let result = mdLines.join('\n')
  result = result.replace(/\n{3,}/g, '\n\n').replace(/  +/g, ' ')
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
    { ch: 2, pattern: /^Product Overview & Components/m },
    { ch: 3, pattern: /^Power Supply Introduction/m },
    { ch: 4, pattern: /^Preparation Before First Use/m },
    { ch: 5, pattern: /^Product Parameters\s*$/m },
    { ch: 6, pattern: /^Troubleshooting\s*$/m },
    { ch: 7, pattern: /^Transportation & Storage/m },
    { ch: 8, pattern: /Hazardous Substances/m },
    { ch: 9, pattern: /^Warranty Information/m },
  ]

  const chapterOffsets = new Map()
  for (const { ch, pattern } of chapterDefs) {
    let lastMatch = null, searchFrom = 0
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
    if (!headingMatch) { console.warn(`  Warning: "${section.title}" not found, skipping ${section.file}`); continue }
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

// ─── Step 3: Merge ──────────────────────────────────────────────────────────

function buildImageRefs(filenames, alts) {
  return filenames.map((f, i) => `![${alts && alts[i] ? alts[i] : ''}](/images/aegis-ultra/${f})`).join('\n\n')
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
      if (targetIdx !== -1) { lines.splice(targetIdx + 1, 0, '', refs, ''); result = lines.join('\n') }
      else result = result.trimEnd() + '\n\n' + refs + '\n'
    }
  }
  return result.replace(/\n{3,}/g, '\n\n')
}

async function mergeAndWrite(textMap, imageMap, sections) {
  console.log('\n── Step 3: Merging text + images ──')
  await fs.mkdir(PAGES_DIR, { recursive: true })
  for (const section of sections) {
    const text = textMap.get(section.file)
    if (!text) continue
    const final = insertImages(text, section, imageMap)
    await fs.writeFile(path.join(PAGES_DIR, section.file), final, 'utf-8')
    const imgCount = (section.images || []).reduce((s, r) => s + (imageMap.get(r.name) || []).length, 0)
    console.log(`  Written: ${section.file}${imgCount > 0 ? ` + ${imgCount} image(s)` : ''}`)
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
  console.log('║  FX Aegis Ultra: Source-to-Markdown Pipeline     ║')
  console.log('║  PDF (text) + Word (images) → Markdown           ║')
  console.log('╚══════════════════════════════════════════════════╝')
  if (chapterFilter != null) console.log(`\n  Filtering: Chapter ${chapterFilter} only (${sections.length} sections)`)

  if (imagesOnly) { await extractImages(sections); console.log('\n✓ Images extracted.'); return }

  let imageMap = new Map()
  if (!textOnly) imageMap = await extractImages(sections)
  else console.log('\n── Skipping image extraction (--text-only) ──')

  const textMap = extractText(sections)
  await mergeAndWrite(textMap, imageMap, sections)
  console.log('\n✓ Done! Files written to src/content/pages/aegis-ultra/')
}

main().catch(err => { console.error('Error:', err); process.exit(1) })
