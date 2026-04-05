#!/usr/bin/env node
/**
 * convert.mjs — Unified source-to-markdown conversion pipeline
 *
 * Hybrid approach: PDF for text extraction, Word for image extraction.
 * Both are merged into final markdown files with correctly placed images.
 *
 * Prerequisites:
 *   brew install poppler   (provides pdftotext)
 *   npm install             (provides mammoth)
 *
 * Usage:
 *   npm run convert               # full pipeline (text + images)
 *   npm run convert:text           # text only (no image extraction/insertion)
 *   npm run convert:images         # images only (extract from Word, no text regen)
 *
 * Source files:
 *   src/content/source/manual.pdf   — text source (pdftotext -layout)
 *   src/content/source/manual.docx  — image source (mammoth)
 *
 * Output:
 *   src/content/pages/*.md          — markdown files with image references
 *   public/images/docx/*            — extracted image files
 */

import { promises as fs } from 'node:fs'
import path from 'node:path'
import { execSync } from 'node:child_process'
import mammoth from 'mammoth'

// ─── Paths ──────────────────────────────────────────────────────────────────

const ROOT = path.resolve(import.meta.dirname, '..')
const PDF_PATH = path.join(ROOT, 'src/content/source/manual.pdf')
const DOCX_PATH = path.join(ROOT, 'src/content/source/manual.docx')
const PAGES_DIR = path.join(ROOT, 'src/content/pages')
const IMAGES_DIR = path.join(ROOT, 'public/images/docx')

// ─── Section Definitions ────────────────────────────────────────────────────
//
// Each section is the single source of truth for:
//   - PDF text extraction: pattern, endBefore
//   - Word image extraction: headingId (per image rule)
//   - Image placement: images[] rules
//
// Image placement rules:
//   position: 'start'          → after the # title line
//   position: 'end'            → at the end of the file
//   after: '## Heading Text'   → right after that heading line
//   after: 'text fragment'     → after the first line containing this text
//
// Each image rule extracts from Word using its own headingId/endHeadingId,
// allowing one markdown file to pull images from multiple Word sections.

const SECTIONS = [
  // ── Chapter 1: Preliminary Notice ──────────────────────────────────────
  {
    chapter: 1,
    file: 'safety-instructions.md',
    title: 'Safety Instructions',
    pattern: /^1\.1\s+Safety Instructions\s*$/m,
    endBefore: /^1\.2\s/m,
  },
  {
    chapter: 1,
    file: 'safety-guidelines.md',
    title: 'Safety Guidelines',
    pattern: /^1\.2\s+Safety Guidelines\s*$/m,
    endBefore: /^1\.3\s/m,
  },
  {
    chapter: 1,
    file: 'maintenance.md',
    title: 'Maintenance and Management Guidelines',
    pattern: /^1\.3\s+Maintenance and Management Guidelines\s*$/m,
    endBefore: /^2\.\s{1,2}[A-Z]/m,
  },

  // ── Chapter 2: About FF Master ─────────────────────────────────────────
  {
    chapter: 2,
    file: 'packing-list.md',
    title: 'Packing List',
    pattern: /^2\.1\s+Packing List\s*$/m,
    endBefore: /^2\.2\s/m,
    images: [
      { position: 'start', headingId: 'heading_5', name: 'packing-list', alts: ['Package Contents'] },
    ],
  },
  {
    chapter: 2,
    file: 'product-overview.md',
    title: 'Product Overview',
    pattern: /^2\.2\s+Product Overview\s*$/m,
    endBefore: /^2\.3\s/m,
    images: [
      { after: '## Product Structure Diagram', headingId: 'heading_7', name: 'product-structure' },
      { after: '## User Debugging Interface', headingId: 'heading_8', name: 'debugging-interface' },
      { position: 'end', headingId: 'heading_9', name: 'sdk-interface' },
    ],
    tables: [
      {
        headerPattern: /No\.\s{2,}Interface\s{2,}Interface\s{2,}Interface/,
        matchIndex: 0,
        hardcoded: [
          '| No. | Interface Type | Interface Name | Interface Description |',
          '| --- | --- | --- | --- |',
          '| 1 | RK3588 USB | USB Type-A | Supports USB 3.0 host, 5V/1.5A power output; RK3588 USB Type-A and Type-C ports share 5 Gbps bandwidth. |',
          '| 2 | RK3588 USB | USB Type-C | Supports USB 3.0 host, 5V/1.5A power output; RK3588 USB Type-A and Type-C ports share 5 Gbps bandwidth. |',
          '| 3 | Orin NX USB | USB Type-A | Supports USB 3.0 host, 5V/1.5A power output; Orin NX USB Type-A and Type-C ports share 10 Gbps bandwidth. |',
          '| 4 | Orin NX USB | USB Type-C | Supports USB 3.0 host, 5V/1.5A power output; Orin NX USB Type-A and Type-C ports share 10 Gbps bandwidth. |',
          '| 5 | SIM card slot | SIM card slot | 5G module SIM card slot. |',
        ].join('\n'),
      },
      {
        headerPattern: /No\.\s{2,}Interface\s{2,}Interface\s{2,}Interface/,
        matchIndex: 1,
        hardcoded: [
          '| No. | Interface Type | Interface Name | Interface Description |',
          '| --- | --- | --- | --- |',
          '| 1 | RJ45 | 1000 Base-T | Gigabit Ethernet, accessible by both Orin NX and RK3588 |',
          '| 2 | RJ45 | 1000 Base-T | Gigabit Ethernet, accessible by both Orin NX and RK3588 |',
          '| 3 | XT30UPB-F | 12V Power | 12V/3A Power Output Port |',
          '| 4 | XT30UPB-F | 48V Power | 48V/5A Power Output Port |',
        ].join('\n'),
      },
    ],
  },
  {
    chapter: 2,
    file: 'computational-unit.md',
    title: 'Computational Unit',
    pattern: /^2\.3\s+Computational Unit\s*$/m,
    endBefore: /^2\.4\s/m,
    tables: [
      {
        headerPattern: /^\s*Type\s{10,}On-board/,
        hardcoded: [
          '| Configuration | Description |',
          '| --- | --- |',
          '| Type | On-board computer |',
          '| FF Master / FF Master Edu | One operation and control computing unit (PC1) and one interactive computing unit (PC3) |',
          '| FF Master Ultra | One operation and control computing unit (PC1), one interactive computing unit (PC3) and one development computing unit (PC2) |',
        ].join('\n'),
      },
      {
        headerPattern: /Parameter\s{10,}Development Computing Unit/,
        hardcoded: [
          '| Parameter | Development Computing Unit (PC2) |',
          '| --- | --- |',
          '| Processor | Jetson Orin NX |',
          '| AI Performance | 157Tops |',
          '| GPU | 1,024-core NVIDIA Ampere architecture GPU with 32 Tensor Cores |',
          '| CPU | 8-core Arm® Cortex®-A78AE v8.2 64-bit CPU |',
          '| Cache | 2MB L2 + 4MB L3 |',
          '| VRAM (Graphics Memory) | 16G |',
          '| System Memory (RAM) | 16G |',
          '| Storage | 512GB |',
        ].join('\n'),
      },
    ],
  },
  {
    chapter: 2,
    file: 'battery-indicator.md',
    title: 'Battery Indicator Lights',
    pattern: /^2\.4\s+Battery Indicator Lights\s*$/m,
    endBefore: /^2\.5\s/m,
    images: [
      { after: '## Battery Indicator Location', headingId: 'heading_11', endHeadingId: 'heading_17', name: 'battery-indicator' },
    ],
    tables: [
      {
        headerPattern: /Battery Indicator Status\s{2,}Battery Level\s{2,}Status Description/,
        matchIndex: 0,
        hardcoded: [
          '| Battery Indicator Status (Discharging) | Battery Level Description | Status Description |',
          '| --- | --- | --- |',
          '| LEDs 1–4 steady on | 75%≤SOC＜100% | Fully charged |',
          '| LEDs 1–3 steady on, remaining off | 50%≤SOC＜75% | Battery level sufficient, no action required |',
          '| LEDs 1–2 steady on, remaining off | 25%≤SOC＜50% | Normal battery level, no action required |',
          '| LED 1 steady on, remaining off | 15%≤SOC＜25% | Low battery, recharge soon |',
          '| LED 1 flashing, remaining off | SOC＜15% | Critically low power, charge immediately |',
        ].join('\n'),
      },
      {
        headerPattern: /Battery Indicator Status\s{2,}Battery Level\s{2,}Status Description/,
        matchIndex: 1,
        hardcoded: [
          '| Battery Indicator Status (Charging) | Battery Level Description | Status Description |',
          '| --- | --- | --- |',
          '| LED1 breathing, LEDs 2–4 off | SOC＜25% | Initial charging stage, low battery |',
          '| LED1 steady on, LED2 breathing, LEDs 3–4 off | 25%≤SOC＜50% | Low battery, not recommended to disconnect power during use |',
          '| LEDs 1–2 steady on, LED3 breathing, LED4 off | 50%≤SOC＜75% | Medium battery level, can be used normally, recommended to continue charging until full |',
          '| LEDs 1–3 steady on, LED4 breathing | 75%≤SOC＜100% | Battery nearly full, can be used normally, recommended to continue charging until full |',
          '| LEDs 1–4 steady on | SOC=100% | Fully charged, power can be disconnected |',
        ].join('\n'),
      },
      {
        headerPattern: /No\.\s{2,}Col/,
        hardcoded: [
          '| No. | Color | LED1 | LED2 | LED3 | LED4 | Status Description |',
          '| --- | --- | --- | --- | --- | --- | --- |',
          '| 1 | Green | Displays according to SOC status | | | | Normal |',
          '| 2 | - | Flashes once per second | Flashes once per second | Flashes once per second | Flashes once per second | Protection mode (overtemperature, overcurrent, or overvoltage) |',
          '| 3 | Red | Flashes once per second | | | | Fault (requires return for repair) |',
          '| 4 | - | All LEDs off | | | | Power-off (deep sleep) or very low SOC (< 39V) |',
        ].join('\n'),
      },
    ],
  },
  {
    chapter: 2,
    file: 'sensor-fov.md',
    title: 'Sensor Field of View',
    pattern: /^2\.5\s+Sensor Field of View\s*$/m,
    endBefore: /^2\.6\s/m,
    images: [
      {
        position: 'end', headingId: 'heading_17', name: 'sensor-fov',
        alts: ['Lidar-FOV', 'RGBD-FOV', 'Interactive RGB Camera-FOV-Vertical', 'Interactive RGB Camera-FOV-Horizontal'],
      },
    ],
    tables: [
      {
        headerPattern: /Item\s{2,}Perception Configuration\s{2,}Perception Ability/,
        replaceToEnd: true,
        hardcoded: [
          '| Item | Perception Configuration | Perception Ability |',
          '| --- | --- | --- |',
          '| FF Master / FF Master EDU | Interactive RGB Camera | Precision environmental data in real time |',
          '| FF Master Ultra | LiDAR; RGB-D Depth Camera; Front Stereo RGB Cameras; Front Interactive RGB Camera; Rear RGB Camera | LiDAR: a. Captures high-precision environmental data in real time; b. Rapidly detects and measures surrounding objects; c. Outputs high-resolution point-cloud data. Additional Camera Suite: a. RGB-D Depth Camera provides accurate 3-D spatial information; b. Stereo RGB Cameras enhances 3-D perception and distance-estimation precision; c. Rear RGB Camera covers rear field eliminating blind spots; d. Interactive Cameras enable visual recognition and response during human-robot interaction. |',
        ].join('\n'),
      },
    ],
  },
  {
    chapter: 2,
    file: 'joint-limits.md',
    title: 'Joint Name and Joint Limit',
    pattern: /^2\.6\s+Joint Name and Joint Limit\s*$/m,
    endBefore: /^2\.7\s/m,
    images: [
      { position: 'start', headingId: 'heading_18', name: 'joint-limits' },
    ],
    tables: [
      {
        headerPattern: /Joint Name\s{2,}Joint Limit/,
        replaceToEnd: true,
        hardcoded: [
          '| Joint Name | FF Master / FF Master Edu | FF Master Ultra |',
          '| --- | --- | --- |',
          '| Arm Workspace | J1(Shoulder pitch): ±146.5° | J1(Shoulder pitch): ±146.5° |',
          '| | J2(Shoulder roll): -3.5~+174.5° | J2(Shoulder roll): -3.5~+174.5° |',
          '| | J3(Shoulder yaw): ±146.5° | J3(Shoulder yaw): ±146.5° |',
          '| | J4(Elbow): -146.5~0° | J4(Elbow): -146.5~0° |',
          '| | J5(Wrist yaw): ±146.5° | J5(Wrist yaw): ±146.5° |',
          '| | / | J6(Wrist pitch): ±32° |',
          '| | / | J7(Wrist roll): ±88.5° |',
          '| Leg Workspace | J1(Hip pitch): ±146.5° | J1(Hip pitch): ±146.5° |',
          '| | J2(Hip roll): -166.5~+13.5° | J2(Hip roll): -166.5~+13.5° |',
          '| | J3(Hip yaw): -96.5°~196.5° | J3(Hip yaw): -96.5°~196.5° |',
          '| | J4(Knee): 0~121.5° | J4(Knee): 0~121.5° |',
          '| | J5(Ankle pitch): -46°~26° | J5(Ankle pitch): -46°~26° |',
          '| | J6(Ankle roll): ±15° | J6(Ankle roll): ±15° |',
          '| Head Workspace | J1(Head pitch): ±20° | J1(Head pitch): ±20° |',
          '| | J2(Head yaw): ±20° | J2(Head yaw): ±20° |',
          '| Waist Workspace | J1(Waist Yaw): -196.5~+136.5° | J1(Waist Yaw): -196.5~+136.5° |',
          '| | J2(Waist pitch): ±18° | J2(Waist pitch): ±18° |',
          '| | J3(Waist roll): ±28° | J3(Waist roll): ±28° |',
        ].join('\n'),
      },
    ],
  },
  {
    chapter: 2,
    file: 'coordinate-systems.md',
    title: 'Coordinate Systems',
    pattern: /^2\.7\s+Coordinate Systems\s*$/m,
    endBefore: /^2\.8\s/m,
    images: [
      { position: 'end', headingId: 'heading_19', name: 'coordinate-systems' },
    ],
  },
  {
    chapter: 2,
    file: 'specifications.md',
    title: 'Specifications',
    pattern: /^2\.8\s+Specifications\s*$/m,
    endBefore: /^3\.\s{1,2}[A-Z]/m,
    tables: [
      {
        headerPattern: /Item\s{2,}FF Master\s{2,}FF Master Edu\s{2,}FF Master Ultra/,
        replaceToEnd: true,
        hardcoded: [
          '| Item | Sub-item | FF Master | FF Master Edu | FF Master Ultra |',
          '| --- | --- | --- | --- | --- |',
          '| Overall | Dimensions | 1310(H)*460(W)*210(L)mm | 1310(H)*460(W)*210(L)mm | 1310(H)*460(W)*210(L)mm |',
          '| | Height | Approx. 1.31 m | Approx. 1.31 m | Approx. 1.31 m |',
          '| | Weight | Approx. 35 kg | Approx. 35 kg | Approx. 37 kg |',
          '| | Total actuated DoF | 27 | 27 | 31 |',
          '| | Neck DoF | 2 | 2 | 2 |',
          '| | Single-arm DoF | 5 | 5 | 7 |',
          '| | Waist DoF | 3 | 3 | 3 |',
          '| | Single-leg DoF | 6 | 6 | 6 |',
          '| | Single-arm reach (without end-effector) | 437mm | 437mm | 558mm |',
          '| | Operating temperature | -10℃~40℃ | -10℃~40℃ | -10℃~40℃ |',
          '| Perception System | RGB camera | RGB camera | RGB camera | Interactive RGB camera; front dual RGB cameras; rear RGB camera |',
          '| | Head touch sensor | Equipped | Equipped | Equipped |',
          '| | RGB-D camera | / | / | Equipped |',
          '| | 3D LiDAR | / | / | Equipped |',
          '| Communication | Interface | Wi-Fi, Bluetooth | Wi-Fi, Bluetooth, 4G/5G module | Wi-Fi, Bluetooth, 4G/5G module |',
          '| Interaction Module | Voice | Microphone array, mini wireless microphone, speaker | Microphone array, mini wireless microphone, speaker | Microphone array, mini wireless microphone, speaker |',
          '| | Display | Interactive screen; lighting effects | Interactive screen; lighting effects | Interactive screen; lighting effects |',
          '| Performance | Peak joint torque | 120N·m | 120N·m | 120N·m |',
          '| Parameters | Speed | Max 1.5 m/s; recommended ≤ 0.8 m/s for daily use | Max 1.5 m/s; recommended ≤ 0.8 m/s for daily use | Max 1.5 m/s; recommended ≤ 0.8 m/s for daily use |',
          '| | Payload | Specific posture: Max 3 kg (excl. end-effector); Full workspace: ≤ 1 kg (excl. end-effector) | Specific posture: Max 3 kg (excl. end-effector); Full workspace: ≤ 1 kg (excl. end-effector) | Specific posture: Max 3 kg (excl. end-effector); Full workspace: ≤ 1 kg (excl. end-effector) |',
          '| | Obstacle clearance capability | ≤50mm | ≤50mm | ≤50mm |',
          '| | Climbing capability | ≤15° | ≤15° | ≤15° |',
          '| Power System | Battery capacity | Approx. 500 Wh | Approx. 500 Wh | Approx. 500 Wh |',
          '| | Endurance | ~2 h continuous walking at 0.5 m/s | ~2 h continuous walking at 0.5 m/s | ~2 h continuous walking at 0.5 m/s |',
          '| | Energy replenishment | Supports direct charging and battery swap | Supports direct charging and battery swap | Supports direct charging and battery swap; optional automatic charging dock |',
          '| | Charging time | ≤1.5h | ≤1.5h | ≤1.5h |',
          '| | Charger input voltage | 100~220V | 100~220V | 100~220V |',
          '| | Charger output | 54.6V 10A | 54.6V 10A | 54.6V 10A |',
          '| Control & Compute | Base compute board | RK3588*2 | RK3588*2 | RK3588*2 |',
          '| | High-performance compute / secondary dev. board | / | / | Orin NX 16GB 157 TOPS |',
          '| Hardware Interfaces | USB Host | USB Type-A*1, USB Type-C*1 | USB Type-A*1, USB Type-C*1 | USB Type-A*2, USB Type-C*2 |',
          '| | Ethernet | RJ45*2 | RJ45*2 | RJ45*2 |',
          '| | Audio/Video output | / | / | miniDP*1 |',
          '| | Power input ports | / | / | 12V/3A*1, 48V/5A*1 |',
          '| Others | Smart OTA upgrade | Equipped | Equipped | Equipped |',
          '| | Handheld remote controller | Equipped | Equipped | Equipped |',
          '| | Mobile app | Under development, will release soon | Under development, will release soon | Under development, will release soon |',
          '| | Secondary development (SDK) | / | / | Equipped |',
        ].join('\n'),
      },
    ],
  },

  // ── Chapter 3: Operation Guide ────────────────────────────────────────────
  {
    chapter: 3,
    file: 'safety-precautions.md',
    title: 'Safety Precautions',
    pattern: /^3\.1\s+Safety Precautions\s*$/m,
    endBefore: /^3\.2\s/m,
  },
  {
    chapter: 3,
    file: 'startup-guide.md',
    title: 'Start-Up Guide',
    pattern: /^3\.2\s+Start-Up Guide\s*$/m,
    endBefore: /^3\.3\s/m,
    images: [
      { position: 'end', headingId: 'heading_24', endHeadingId: 'heading_25', name: 'startup-hoisting' },
      { position: 'end', headingId: 'heading_25', endHeadingId: 'heading_27', name: 'startup-supine' },
      { position: 'end', headingId: 'heading_27', endHeadingId: 'heading_28', name: 'startup-prone' },
      { position: 'end', headingId: 'heading_28', endHeadingId: 'heading_29', name: 'startup-sitting' },
    ],
  },
  {
    chapter: 3,
    file: 'shutdown-guide.md',
    title: 'Shutdown Guide',
    pattern: /^3\.3\s+Shutdown Guide\s*$/m,
    endBefore: /^3\.4\s/m,
    images: [
      { position: 'end', headingId: 'heading_30', endHeadingId: 'heading_31', name: 'shutdown-hoisted' },
      { position: 'end', headingId: 'heading_31', endHeadingId: 'heading_32', name: 'shutdown-lyingdown' },
      { position: 'end', headingId: 'heading_32', endHeadingId: 'heading_33', name: 'shutdown-sitting' },
    ],
  },
  {
    chapter: 3,
    file: 'charging-procedure.md',
    title: 'Charging Procedure',
    pattern: /^3\.4\s+Charging Procedure\s*$/m,
    endBefore: /^3\.5\s/m,
    images: [
      { position: 'end', headingId: 'heading_34', endHeadingId: 'heading_35', name: 'charging' },
      { position: 'end', headingId: 'heading_35', endHeadingId: 'heading_36', name: 'battery-replacement' },
    ],
  },
  {
    chapter: 3,
    file: 'remote-control.md',
    title: 'Remote Control User Guide',
    pattern: /^3\.5\s+Remote Control User Guide\s*$/m,
    endBefore: /^3\.6\s/m,
    images: [
      { after: '## Remote Control Button Positions', headingId: 'heading_39', name: 'remote-buttons' },
      { after: '## Description of Mode Switching Logic', headingId: 'heading_44', name: 'mode-switching-logic' },
    ],
    tables: [
      {
        headerPattern: /Concept\s{2,}Description/,
        replaceToEnd: false,
        hardcoded: [
          '| Concept | Description |',
          '| --- | --- |',
          '| Zero-Torque Mode | The default state after the robot is powered on. All motors stop active motion, and there is no damping sensation when the body is swung. Note: In zero-torque mode the robot will fall over and there is a risk of tipping. Switch to this mode with caution. |',
          '| Damping Mode | The robot is powered on, and the main controller is operating normally. All joints enter a damping state, with a clear damping feel when the body is swung. Changing joint positions is resisted; joints cannot actively change position or hold a position. Note: In damping mode, the robot will slowly collapse and there is a risk of falling. Switch with caution. |',
          '| Standing Preparation (Position-Controlled Standing) Mode | The robot is powered on, and the main controller is operating normally. The robot stands in a position-controlled posture and maintains it; the joints are locked at their current positions. In this mode, body motion cannot be commanded. It is commonly used for hoisting/lowering and is a safe posture. (The robot does not self-balance in this mode.) |',
          '| Sitting Preparation (Position-Controlled Sitting) Mode | The robot is powered on, and the main controller is operating normally. The robot enters a sitting posture and maintains it; the joints are locked at their current positions. In this mode, the robot\'s body motion cannot be commanded. It is typically used for starting up from a sitting or Supine Position and represents a safe posture. (The robot does not self-balance in this mode.) |',
          '| Stable Standing (Force-Controlled Standing) Mode | The robot is powered on, and the main controller is operating normally. The robot stands and maintains posture. If joint positions are disturbed, there will be strong resistance, and the robot will actively recover to the standing posture. The robot has a certain balancing capability. In this mode, body motions can be commanded; while standing the robot can perform upper-limb actions such as waving or handshaking. It is recommended to perform stable standing on flat, hard surfaces. Avoid standing on soft or uneven surfaces such as carpets or grass. |',
          '| Locomotion Mode | The robot is powered on, and the main controller is operating normally. The robot enters the walking mode and can move forward/backward/left/right and rotate clockwise or counterclockwise as commanded. Speed and gait can be adjusted via the joystick; start with a slow gait and then gradually increase the speed. To maintain balance, preset upper-limb actions are not supported in Locomotion mode. It is recommended to perform road tests on flat, hard surfaces and to avoid stairs, rough/uneven ground, and high-curvature ramps. |',
          '| Emergency-Stop Mode | In this mode, the robot stops safely and may fall softly to the ground. Please pay close attention to the robot\'s safety during this state. It is recommended to use a protective frame to safeguard the robot when operating in this mode. |',
          '| Off-Road Mode (Beta) | In this mode, the robot enters a fast-running control state with enhanced adaptability to rough terrain. To maintain balance, the robot\'s upper-limb preset motions are temporarily disabled during Off-Road Mode. |',
        ].join('\n'),
      },
      {
        headerPattern: /Button position\s{2,}FF MASTER/,
        hardcoded: [
          '| Button Position | Name and Meaning |',
          '| --- | --- |',
          '| B: Left Button/Trigger | L1, L2 Buttons (PS5 side view) |',
          '| A: Right Button/Trigger | R1, R2 Buttons (PS5 side view) |',
          '| A: Arrow Button | The left cross key, ↑, ↓, ←, → four direction buttons |',
          '| B: Create Button | Create Button |',
          '| C: Touchpad | Touchpad |',
          '| D: Options Button | Options Button |',
          '| E: Four Action Buttons | △, □, ○ and × Four Action Buttons |',
          '| I & F: Sticks | I: Left Stick (controls forward/backward and left/right). F: Right Stick (controls rotation). |',
          '| "PS" Button | G |',
        ].join('\n'),
      },
      {
        headerPattern: /Status Description\s{2,}LED Color/,
        hardcoded: [
          '| Status Description | LED Color/Behaviour |',
          '| --- | --- |',
          '| Controller power-on / connected | Solid blue |',
          '| Controller waiting to pair | Fast-blinking blue |',
          '| Pairing successful | Solid white |',
          '| Normal startup | Breathing white |',
          '| Battery level ≤10% | Solid amber |',
          '| Charging (0–20%) | Fast blink amber |',
          '| Charging (20–100%) | Slow blink amber |',
          '| Charging complete | Amber off |',
          '| Firmware update | Fast-blinking white |',
        ].join('\n'),
      },
      {
        headerPattern: /\s{2,}Name\s{2,}Details/,
        hardcoded: [
          '| Name | Details |',
          '| --- | --- |',
          '| Hoisted Start-Up | Process: Power on (hoisted position) → Position-Controlled Standing → Force-Controlled Standing → Remove hoisting ring → Enter Locomotion Mode. Standing Preparation Mode: L2 + X (short press). Stable Standing Mode: R2 + X (short press). "Stick-to-Move": The robot automatically enters Locomotion Mode when the joystick is pushed forward. |',
          '| Start-Up from Supine Position | Process: Power on (ensure the robot\'s hips are level with the ground and the torso is facing upward) → Supine start-up → Locomotion Mode. Supine Start-Up: Press ↑ + △ simultaneously (short press). "Stick-to-Move": joystick forward to enter Locomotion Mode. |',
          '| Start-up from Prone Position | Process: Power on (ensure the robot\'s hips are level with the ground and the torso is facing downward) → Prone start-up → Locomotion Mode. Prone Start-Up: Press ↑ + △ simultaneously (short press). "Stick-to-Move": joystick forward to enter Locomotion Mode. |',
          '| Start-up from Sitting Position | Process: Power on (sitting standby) → Enter sitting posture → Sit-to-stand → Locomotion Mode. Sitting Preparation Mode: Press ↑ + X (short press). Sitting Start-Up: Press ↑ + □ (short press). "Stick-to-Move": joystick forward to enter Locomotion Mode. |',
          '| Standing Preparation (Position-Controlled Standing) Mode | Press L2 + X simultaneously (short press). This mode can also be switched from Zero-Torque Mode. |',
          '| Sitting Preparation (Position-Controlled Sitting) Mode | Press ↑ + X simultaneously (short press). This mode can also be switched from Zero-Torque Mode. |',
          '| Stable Standing (Force-Controlled Standing) Mode | Press R2 + X simultaneously (short press). |',
          '| Zero-Torque Mode | Press L1 + R1 + Create simultaneously (short press). The robot can enter this mode from any other mode. |',
          '| Damping Mode | Press L2 + R2 + Create simultaneously (short press). The robot can enter this mode from any other mode. |',
          '| Locomotion Mode | In Stable Standing Mode, push joystick to move. Forward/Backward: left joystick up/down. Turn Left/Right: right joystick left/right. Strafe Left/Right: left joystick left/right. |',
          '| Off-Road Mode (Beta) | When in Locomotion Mode, press R2 + ↑ simultaneously (short press) to switch to Off-Road Mode. |',
          '| Sit Down / Stand Up from Sitting | In Stable Standing Mode: Sit Down: Press L2 + ← (short press). Stand Up: Press ↑ + □ (short press). |',
          '| Crouch Down / Stand Up from Crouching | In Stable Standing Mode, press △ + Left Joystick to control crouching depth. Push joystick up to stand, down to crouch. |',
          '| Emergency-Stop Mode | Press L1 + R1 + Create simultaneously (short press). The robot will slowly collapse. To exit, press L2 + X to switch to Standing Preparation Mode. |',
          '| Hoisted Shutdown | Standing Preparation Mode: L2 + X → Damping Mode: L2 + R2 + Create → Zero-Torque Mode: L1 + R1 + Create → Hoist feet off ground → Power off. |',
          '| Assisted Lying-Down Shutdown | Standing Preparation Mode: L2 + X → Manually assist robot to lie down → Damping Mode: L2 + R2 + Create → Zero-Torque Mode: L1 + R1 + Create → Power off. |',
          '| Sitting-Position Shutdown | Sit Down: L2 + ← → Damping Mode: L2 + R2 + Create → Zero-Torque Mode: L1 + R1 + Create → Power off. |',
        ].join('\n'),
      },
      {
        headerPattern: /Action\s{2,}Action\s{2,}Button Instruction/,
        hardcoded: [
          '| Action Type | Action Name | Button Instruction |',
          '| --- | --- | --- |',
          '| Head Movements | Clockwise Rotation | L1 + push left joystick right. Release to return to neutral. Hold to fix angle; press again to unlock. |',
          '| | Counterclockwise Rotation | L1 + push left joystick left. Release to return to neutral. Hold to fix; press again to unlock. |',
          '| | Downward Tilt | L1 + push left joystick down. Release to return to neutral. Hold to fix; press again to unlock. |',
          '| | Upward Tilt | L1 + push left joystick up. Release to return to neutral. Hold to fix; press again to unlock. |',
          '| Upper-Limb Movements | Wave (Left) | Create + L1 + tap △ |',
          '| | Wave (Right) | Create + R1 + tap △ |',
          '| | Handshake (Left) | Create + L1 + tap ✕ |',
          '| | Handshake (Right) | Create + R1 + tap ✕ |',
          '| | Flying Kiss (Left) | Create + L1 + tap ○ |',
          '| | Flying Kiss (Right) | Create + R1 + tap ○ |',
          '| | Salute (Left) | Create + L1 + tap □ |',
          '| | Salute (Right) | Create + R1 + tap □ |',
          '| | Fist Strike (Left) | Options + L1 + tap ↓ |',
          '| | Fist Strike (Right) | Options + R1 + tap ↓ |',
          '| | Palm Strike (Left) | Options + L1 + tap → |',
          '| | Palm Strike (Right) | Options + R1 + tap → |',
          '| | Raise Hand (Left) | Options + L1 + tap ↑ |',
          '| | Raise Hand (Right) | Options + R1 + tap ↑ |',
          '| Waist Movements | Clockwise Rotation | L1 + push right joystick right. Release to return to neutral. Hold to fix; press again to unlock. |',
          '| | Counterclockwise Rotation | L1 + push right joystick left. Release to return to neutral. Hold to fix; press again to unlock. |',
          '| | Bend Forward | L1 + push right joystick down. Release to return to neutral. Hold to fix; press again to unlock. |',
          '| | Straighten Waist | L1 + push right joystick up. Release to return to neutral. Hold to fix; press again to unlock. |',
        ].join('\n'),
      },
    ],
  },
  {
    chapter: 3,
    file: 'robot-interaction.md',
    title: 'Robot Interaction Procedures Guide',
    pattern: /^3\.6\s+Robot Interaction Procedures? Guide\s*$/m,
    endBefore: /^3\.7\s/m,
    images: [
      { position: 'end', headingId: 'heading_57', endHeadingId: 'heading_58', name: 'microphone-pairing' },
    ],
    tables: [
      {
        headerPattern: /Category\s{2,}Supported Range\s{2,}Example Voice/,
        hardcoded: [
          '| Category | Supported Range | Example Voice Command |',
          '| --- | --- | --- |',
          '| Upper Limb + Prosthetic Hand Actions | Left/Right wave, Left/Right chest-front wave, Cross arms, Left/Right raise hand, Left/Right salute, Left/Right handshake, Double-hand heart, Left/Right single-hand heart, Dynamic energy beam, Hug, High five, Cheering, Double-hand lift, Left/Right single-hand lift, Left/Right fist bump, Left/Right thumbs up, Left/Right "V" gesture | "Perform an XXX action." |',
          '| Upper Limb + Dexterous Hand Actions | Left/Right dexterous hand thumbs up, Peace gesture, Fist bump, Cheering motion; also includes all prosthetic hand actions above | "Perform an XXX action." |',
          '| Head Movements | Look left, look right, Nod, Shake head | "Look left / Look right / Nod / Shake head." |',
          '| Walking Actions | Move forward, backward, left, or right | "Walk two steps forward/backward/left/right." |',
          '| Waist Movements | Turn waist left and return, Turn waist right and return | "Turn your waist left/right." |',
          '| Expressive Actions | Head scratching, Butt scratching | "Do a head-scratch/butt-scratch action." |',
          '| Facial Screen Expressions | Blinking, Laughing, Sad/Crying, Bored, Thinking, Sleepy, Confused/Surprised, Angry, Adoring, Coquettish, Sympathetic expressions | "Show a XXX expression." |',
        ].join('\n'),
      },
      {
        headerPattern: /^Type\s{2,}Required Content\s{2,}Description/m,
        hardcoded: [
          '| Type | Required Content | Description |',
          '| --- | --- | --- |',
          '| Character Customization | Character profile (optional), desired company/business knowledge (optional). Limit: within 300 characters. Currently supported via sales representative submission; future support through the Intellectual & Interactive Platform. | Customize a corporate-specific persona, enabling the robot to understand core company knowledge. |',
          '| Q&A Customization | Question: User utterances, up to 20 characters each, with 2–5 high-frequency variations. Answer: Robot response, up to 50 characters. Currently supported via sales representative submission. | Designed for high-frequency Q&A scenarios — allows the robot to accurately answer company-specific questions. |',
          '| Facial Registration | Supports facial data entry and customization of greeting dialogues for specific individuals. | Enables personalized greetings and welcome messages for registered faces. |',
          '| Voice Tone Selection | Future customization available through the Intellectual & Interactive Platform. | Allows customization or replication of the robot\'s voice tone. |',
          '| Wake Word Customization | Future customization available through the Intellectual & Interactive Platform. | Enables defining personalized wake words for robot activation. |',
        ].join('\n'),
      },
    ],
  },
  {
    chapter: 3,
    file: 'ff-robotic-app.md',
    title: 'FF Robotic APP Manual',
    pattern: /^3\.7\s+FF Robotic APP Manual/m,
    endBefore: /^3\.8\s/m,
    images: [
      { position: 'end', headingId: 'heading_59', endHeadingId: 'heading_61', name: 'app-download' },
      { position: 'end', headingId: 'heading_61', endHeadingId: 'heading_62', name: 'controller-operations' },
    ],
  },
  {
    chapter: 3,
    file: 'others.md',
    title: 'Others',
    pattern: /^3\.8\s+Others\s*$/m,
    endBefore: /^4\.\s{1,2}[A-Z]/m,
  },

  // ── Chapter 4: Locomotion & Manipulation Platform Manual ──────────────────
  {
    chapter: 4,
    file: 'locomotion-platform.md',
    title: 'Locomotion & Manipulation Platform Manual',
    pattern: /^4\.\s+Locomotion & Manipulation Platform Manual/m,
    endBefore: /^5\.\s{1,2}[A-Z]/m,
  },

  // ── Chapter 5: Contact Information ────────────────────────────────────────
  {
    chapter: 5,
    file: 'contact-information.md',
    title: 'Contact Information',
    pattern: /^5\.\s+Contact Information\s*$/m,
    endBefore: /^6\.\s{1,2}[A-Z]/m,  // no chapter 6, so matches to end of file
  },
]

// ─── Table Parsing Helpers ──────────────────────────────────────────────────

/**
 * Detect column start positions from a table header line.
 * Columns are separated by 2+ consecutive spaces.
 * The first column always starts at position 0.
 */
function detectColumnPositions(headerLine) {
  const positions = []
  let i = 0
  const len = headerLine.length

  // Find the first text character
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

  // First column always starts at 0 to capture data that may start before header text
  positions[0] = 0
  return positions
}

/**
 * Parse raw table data lines into rows of cell arrays.
 * Multi-line cells are joined with spaces.
 * A new row starts when the first column has non-empty content.
 */
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

/**
 * Format rows as a markdown table string.
 */
function formatMarkdownTable(columns, rows) {
  const lines = []
  lines.push('| ' + columns.join(' | ') + ' |')
  lines.push('| ' + columns.map(() => '---').join(' | ') + ' |')
  for (const row of rows) {
    const paddedRow = [...row]
    while (paddedRow.length < columns.length) paddedRow.push('')
    // Escape pipe characters in cell content
    const escaped = paddedRow.map(cell => cell.replace(/\|/g, '\\|'))
    lines.push('| ' + escaped.join(' | ') + ' |')
  }
  return lines.join('\n')
}

/**
 * Find where a table region ends in the raw text lines.
 * Ends at: next sub-heading, or 3+ blank lines, or end of text.
 */
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

/**
 * Process raw section text to detect and convert tables to markdown format.
 * Returns modified text with table regions replaced by markdown tables.
 */
function processTablesInRawText(rawText, tableDefs) {
  if (!tableDefs || tableDefs.length === 0) return rawText

  const lines = rawText.split('\n')
  const replacements = []

  for (const def of tableDefs) {
    // Handle hardcoded tables (matchIndex selects which occurrence, default 0)
    if (def.hardcoded) {
      let matchCount = 0
      const targetIndex = def.matchIndex || 0
      for (let i = 0; i < lines.length; i++) {
        if (!def.headerPattern.test(lines[i])) continue
        // Count ALL pattern matches, even those already covered by a prior replacement
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

    // Auto-parse tables
    for (let i = 0; i < lines.length; i++) {
      if (replacements.some(r => i >= r.startLine && i < r.endLine)) continue
      if (!def.headerPattern.test(lines[i])) continue

      const colPositions = def.colPositions || detectColumnPositions(lines[i])

      // Find header extent (skip non-blank continuation lines, then blank lines)
      let headerEnd = i + 1
      while (headerEnd < lines.length && lines[headerEnd].trim() !== '') headerEnd++
      while (headerEnd < lines.length && lines[headerEnd].trim() === '') headerEnd++

      const dataEnd = findTableEnd(lines, headerEnd)

      // Data lines: optionally include header as first data row
      const dataLines = lines.slice(def.includeHeaderAsData ? i : headerEnd, dataEnd)
      const rows = parseTableRows(dataLines, colPositions)

      if (rows.length > 0) {
        const mdTable = formatMarkdownTable(def.columns, rows)
        replacements.push({ startLine: i, endLine: dataEnd, replacement: mdTable })
      }
    }
  }

  // Apply replacements in reverse order to preserve line numbers
  replacements.sort((a, b) => b.startLine - a.startLine)
  const result = [...lines]
  for (const rep of replacements) {
    result.splice(rep.startLine, rep.endLine - rep.startLine, ...rep.replacement.split('\n'))
  }

  return result.join('\n')
}

// ─── Step 1: Image Extraction (Word → images) ──────────────────────────────

/**
 * Extract images from Word document using mammoth.
 * @param {typeof SECTIONS} sections — filtered sections to process
 * Returns a map: imageName → [filename1, filename2, ...]
 */
async function extractImages(sections) {
  console.log('\n── Step 1: Extracting images from Word ──')
  console.log('Reading:', DOCX_PATH)

  const docxBuffer = await fs.readFile(DOCX_PATH)
  const result = await mammoth.convertToMarkdown({ buffer: docxBuffer })
  const fullMd = result.value

  // Find all heading positions
  const headingRegex = /<a id="(heading_\d+)"><\/a>/g
  const headings = []
  let m
  while ((m = headingRegex.exec(fullMd)) !== null) {
    headings.push({ id: m[1], pos: m.index })
  }
  console.log(`  Found ${headings.length} headings in Word document`)

  await fs.mkdir(IMAGES_DIR, { recursive: true })

  // Collect all unique image extraction rules across filtered sections
  const extractionRules = []
  for (const section of sections) {
    if (!section.images) continue
    for (const rule of section.images) {
      // Avoid duplicates (same headingId + name)
      if (!extractionRules.find(r => r.headingId === rule.headingId && r.name === rule.name)) {
        extractionRules.push(rule)
      }
    }
  }

  // Extract images for each rule
  /** @type {Map<string, string[]>} name → [filename, ...] */
  const imageMap = new Map()

  for (const rule of extractionRules) {
    const headingIdx = headings.findIndex(h => h.id === rule.headingId)
    if (headingIdx === -1) {
      console.warn(`  Warning: Heading ${rule.headingId} not found, skipping ${rule.name}`)
      imageMap.set(rule.name, [])
      continue
    }

    const startPos = headings[headingIdx].pos

    // Determine end position
    let endPos = fullMd.length
    if (rule.endHeadingId) {
      const endIdx = headings.findIndex(h => h.id === rule.endHeadingId)
      if (endIdx !== -1) endPos = headings[endIdx].pos
    } else if (headingIdx + 1 < headings.length) {
      endPos = headings[headingIdx + 1].pos
    }

    const sectionMd = fullMd.substring(startPos, endPos)

    // Extract and save base64 images
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

/**
 * Extract text from PDF using pdftotext with layout preservation.
 * The -layout flag preserves indentation which is critical for nested lists.
 */
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

/**
 * Find the position of a regex in fullText, starting search from afterPos.
 */
function findPatternPos(fullText, afterPos, pattern) {
  const remaining = fullText.substring(afterPos)
  const match = remaining.match(pattern)
  return match ? afterPos + match.index : fullText.length
}

/**
 * Convert raw PDF text (with layout indentation) into clean Markdown.
 *
 * pdftotext -layout indentation patterns:
 *   Numbered items:  "1.     Text" — col 0, text at ~col 7
 *   Sub-items:       "     a. Text" — 4-7 spaces before "a."
 *   Bullet points:   "   • Text" — indented with bullet char
 *   Sub-headings:    "2.2.1 Title" — section number + title → ## / ###
 */
function convertToMarkdown(rawText) {
  const lines = rawText.split('\n')
  const mdLines = []
  let current = ''
  let currentType = '' // 'num', 'sub', 'bullet', 'para'

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

    // Empty lines flush current block and preserve separation after tables
    if (!trimmed) {
      flush()
      if (mdLines.length > 0 && mdLines[mdLines.length - 1].startsWith('|')) {
        mdLines.push('')
      }
      continue
    }

    // Preserve markdown table lines (already formatted by table parser)
    if (trimmed.startsWith('|')) {
      flush()
      mdLines.push(trimmed)
      continue
    }

    // Skip standalone page numbers
    if (/^\d+$/.test(trimmed)) continue

    // Sub-section headings: "2.2.1 Title" or "2.4.2.1 Title"
    const subHeadingMatch = trimmed.match(/^(\d+(?:\.\d+){2,})\s{1,3}(.+)/)
    if (subHeadingMatch && indent < 4) {
      flush()
      const depth = subHeadingMatch[1].split('.').length
      const prefix = depth <= 3 ? '##' : '###'
      mdLines.push(`\n${prefix} ${subHeadingMatch[2].trim()}\n`)
      continue
    }

    // Numbered list items: "1.  Text" at low indent
    const numberedMatch = trimmed.match(/^(\d+)\.\s{2,}(.*)/)
    if (numberedMatch && indent < 4) {
      flush()
      current = `${numberedMatch[1]}. ${numberedMatch[2]}`
      currentType = 'num'
      continue
    }

    // Sub-items: "a. Text" with 4+ spaces indent
    const subItemMatch = trimmed.match(/^([a-z])\.\s+(.*)/)
    if (subItemMatch && indent >= 4) {
      flush()
      current = `   ${subItemMatch[1]}. ${subItemMatch[2]}`
      currentType = 'sub'
      continue
    }

    // Bullet points: "•" or "·"
    const bulletMatch = trimmed.match(/^[•·]\s+(.*)/)
    if (bulletMatch) {
      flush()
      current = `- ${bulletMatch[1]}`
      currentType = 'bullet'
      continue
    }

    // Label lines: standalone labels like "FF Master:", "Type:", "Parameter"
    // Short lines at col 0 ending with ":" that aren't numbered items.
    // These must NOT be merged into the previous paragraph.
    // A blank line before the label ensures markdown renders it as a new paragraph
    // (otherwise it gets swallowed into the preceding list).
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

    // New paragraph
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

/**
 * Extract all section texts from PDF.
 * @param {typeof SECTIONS} sections — filtered sections to process
 * Returns a map: filename → markdown content (without images)
 */
function extractText(sections) {
  console.log('\n── Step 2: Extracting text from PDF ──')
  console.log('Reading:', PDF_PATH)

  const rawText = extractPdfText(PDF_PATH)
  const fullText = rawText.replace(/\f/g, '') // Strip form feeds from page boundaries
  console.log(`  Extracted: ${fullText.length} characters`)

  /** @type {Map<string, string>} file → markdown */
  const textMap = new Map()

  // Find chapter heading positions to skip the Table of Contents.
  // The TOC at the beginning of the PDF can contain entries that match
  // section patterns (e.g. "3.3 Shutdown Guide" appears both in the TOC
  // and in the actual content). We skip past the chapter heading to avoid
  // matching TOC entries.
  const chapterOffsets = new Map()
  for (const ch of [1, 2, 3, 4, 5]) {
    const chPattern = new RegExp(`^${ch}\\.\\s{1,2}[A-Z]`, 'm')
    // Find the LAST occurrence (actual content, not TOC)
    let lastMatch = null
    let searchFrom = 0
    while (true) {
      const remaining = fullText.substring(searchFrom)
      const m = remaining.match(chPattern)
      if (!m) break
      lastMatch = { index: searchFrom + m.index }
      searchFrom = searchFrom + m.index + m[0].length
    }
    if (lastMatch) chapterOffsets.set(ch, lastMatch.index)
  }

  for (const section of sections) {
    // Start searching from the chapter's actual heading position (skip TOC)
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

    // Pre-process tables before general markdown conversion
    const tableProcessed = processTablesInRawText(rawContent, section.tables)
    const mdContent = convertToMarkdown(tableProcessed)

    textMap.set(section.file, `# ${section.title}\n\n${mdContent}\n`)
    console.log(`  ${section.file}: ${mdContent.length} chars`)
  }

  return textMap
}

// ─── Step 3: Merge (text + images → final markdown) ────────────────────────

/**
 * Build markdown image reference lines for a list of filenames.
 */
function buildImageRefs(filenames, alts) {
  return filenames.map((f, i) => {
    const alt = alts && alts[i] ? alts[i] : ''
    return `![${alt}](/images/docx/${f})`
  }).join('\n\n')
}

/**
 * Insert image references into markdown text according to placement rules.
 */
function insertImages(markdown, section, imageMap) {
  if (!section.images || section.images.length === 0) return markdown

  let result = markdown

  for (const rule of section.images) {
    const filenames = imageMap.get(rule.name) || []
    if (filenames.length === 0) continue

    const refs = buildImageRefs(filenames, rule.alts)

    if (rule.position === 'start') {
      // Insert after the # title line
      const titleEnd = result.indexOf('\n\n')
      if (titleEnd !== -1) {
        result = result.substring(0, titleEnd + 2) + refs + '\n\n' + result.substring(titleEnd + 2)
      }
    } else if (rule.position === 'end') {
      // Append at end
      result = result.trimEnd() + '\n\n' + refs + '\n'
    } else if (rule.after) {
      // Find the target line and insert after it
      const lines = result.split('\n')
      const targetIdx = lines.findIndex(l => l.includes(rule.after))
      if (targetIdx !== -1) {
        // Find the end of the content block after this target line
        // For headings (## ...), insert right after the heading + next blank line
        // For text fragments, insert after that line + next blank line
        let insertIdx = targetIdx + 1

        // Skip any non-empty continuation lines after the target
        if (rule.after.startsWith('## ')) {
          // For headings: insert after the heading line itself
          // Find the next heading or end of content for this sub-section
          for (let j = targetIdx + 1; j < lines.length; j++) {
            if (lines[j].startsWith('## ') || lines[j].startsWith('# ')) {
              insertIdx = j
              break
            }
            insertIdx = j + 1
          }
          // Back up past trailing empty lines
          while (insertIdx > targetIdx + 1 && lines[insertIdx - 1].trim() === '') {
            insertIdx--
          }
        } else {
          // For text fragments: insert right after that line
          insertIdx = targetIdx + 1
        }

        lines.splice(insertIdx, 0, '', refs, '')
        result = lines.join('\n')
      } else {
        // Fallback: append at end if target not found
        console.warn(`    Warning: "${rule.after}" not found in ${section.file}, appending at end`)
        result = result.trimEnd() + '\n\n' + refs + '\n'
      }
    }
  }

  // Clean up excessive blank lines introduced by insertions
  result = result.replace(/\n{3,}/g, '\n\n')

  return result
}

/**
 * Merge text and images for all sections, write final markdown files.
 * @param {typeof SECTIONS} sections — filtered sections to process
 */
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

  // --chapter N: only process sections belonging to chapter N
  const chapterIdx = args.indexOf('--chapter')
  const chapterFilter = chapterIdx !== -1 ? Number(args[chapterIdx + 1]) : null

  // Filter sections by chapter if specified
  const sections = chapterFilter
    ? SECTIONS.filter(s => s.chapter === chapterFilter)
    : SECTIONS

  console.log('╔══════════════════════════════════════════════╗')
  console.log('║  Source-to-Markdown Conversion Pipeline      ║')
  console.log('║  PDF (text) + Word (images) → Markdown       ║')
  console.log('╚══════════════════════════════════════════════╝')

  if (chapterFilter) {
    console.log(`\n  Filtering: Chapter ${chapterFilter} only (${sections.length} sections)`)
  }

  if (imagesOnly) {
    // Images-only mode: extract images from Word, don't touch markdown
    const imageMap = await extractImages(sections)
    console.log('\n✓ Images extracted. Markdown files not modified.')
    return
  }

  // Full or text-only mode
  let imageMap = new Map()

  if (!textOnly) {
    // Step 1: Extract images from Word
    imageMap = await extractImages(sections)
  } else {
    console.log('\n── Skipping image extraction (--text-only) ──')
  }

  // Step 2: Extract text from PDF
  const textMap = extractText(sections)

  // Step 3: Merge and write
  await mergeAndWrite(textMap, imageMap, sections)

  console.log('\n✓ Done! Files written to src/content/pages/')
}

main().catch(err => {
  console.error('Error:', err)
  process.exit(1)
})
