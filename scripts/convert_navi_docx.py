#!/usr/bin/env python3
"""
Convert NAVI Series Product Manual .docx → Markdown
Extracts images to apps/web/public/images/navi/
Outputs MD to apps/web/src/content/source/v3/NAVI Series Product Manual.md
"""

import re
import shutil
import zipfile
from pathlib import Path

from docx import Document

DOCX_PATH = Path(__file__).parent.parent / "docs" / "NAVI Series Product Manual .docx"
IMG_OUT_DIR = Path(__file__).parent.parent / "apps" / "web" / "public" / "images" / "navi"
MD_OUT_PATH = Path(__file__).parent.parent / "apps" / "web" / "src" / "content" / "source" / "v3" / "NAVI Series Product Manual.md"

# Map paragraph index → heading level (0 = body text)
# Determined by manual structure analysis of the document
HEADING_MAP: dict[int, int] = {
    0:  1,   # NAVI Series Product Manual (title, duplicate — keep first)
    2:  2,   # Scope of This Manual
    5:  2,   # Terminology and Definitions
    6:  3,   # NAVI (term)
    8:  3,   # Large Language Model (LLM)
    10: 2,   # Product Features and Main Functions
    11: 3,   # Graphical Programming
    14: 3,   # Multi-Function Remote Control
    16: 2,   # Component Names
    30: 2,   # Accessories List
    35: 2,   # Safety Notice
    38: 2,   # FCC Compliance Notice
    45: 3,   # RF exposure statement
    55: 2,   # Pre-Use Checklist
    63: 2,   # Pre-Operation Guidelines
    64: 3,   # Operator Requirements
    67: 3,   # Pre-Operation Preparation
    75: 2,   # Power On/Off Instructions
    76: 3,   # Pre-Startup Posture Requirements
    81: 3,   # Power Button Location
    84: 3,   # How to Power On
    87: 3,   # How to Power Off
    90: 4,   # Standard Shutdown
    93: 4,   # Force Shutdown
    97: 3,   # Accidental Power Button Activation
    98: 4,   # When No Pre-Startup Preparation Is Needed
    100: 2,  # Unboxing Guide
    101: 3,  # Packing List
    104: 3,  # Quick Unboxing
    106: 4,  # Before Unboxing
    109: 4,  # Unboxing Steps
    110: 4,  # Unboxing Troubleshooting
    118: 3,  # Powering On Outside the Box
    120: 4,  # Hard and Level Surface
    122: 4,  # No Obvious Obstructions on the Surface
    124: 4,  # Lower Legs Folded to Structural Stop
    126: 4,  # Hip Joint Actuator Angle Requirements
    128: 2,  # Activation
    130: 3,  # Activation Steps
    133: 2,  # Network Settings
    134: 3,  # Connecting to the Robot Dog Hotspot via App
    139: 4,  # Troubleshooting (hotspot)
    143: 3,  # Configuring Wi-Fi for the Robot Dog via App
    147: 4,  # Troubleshooting (wifi)
    149: 3,  # Using the Robot Dog's 4G Network
    152: 2,  # User Guide
    153: 3,  # Direct Wired Charging
    155: 3,  # Understanding Charging and Operating Status
    156: 4,  # Indicator Light Meanings
    162: 4,  # Operating Mode Indicator Light Status
    163: 4,  # Charging Mode Indicator Light Status
    165: 2,  # Fingertip Remote Controller Instructions
    167: 3,  # Button and Function Description
    173: 3,  # Initial Pairing Method
    185: 3,  # Daily Use
    187: 3,  # Fingertip Remote Controller Specifications
    189: 2,  # Technical Specifications
    190: 3,  # Physical Parameters
    191: 2,  # Safety and Legal Information
    192: 3,  # Safety Warnings for Regular Use and Maintenance
    193: 3,  # Legal Disclaimer
    200: 3,  # Precautions
    227: 2,  # Maintenance and Care
    228: 3,  # Usage Care
    229: 4,  # Post-Operation Care
    232: 4,  # Parts Requiring Regular Maintenance or Replacement
    233: 4,  # Main Unit Maintenance
    240: 4,  # Battery Maintenance
    249: 2,  # Troubleshooting
    250: 3,  # Common Issues and Solutions
    257: 2,  # Help
    264: 2,  # Responsible AI & Robotics Use Guidelines
}

# Paragraphs to skip entirely (blank spacers, duplicate title, etc.)
SKIP_INDICES = {1, 4, 19, 21, 31, 33, 34, 37, 42, 44, 49, 79, 83, 170, 172, 179, 180, 184, 263, 280, 281}

# Paragraphs to render as a list item (- prefix)
LIST_ITEM_INDICES = {
    57, 58, 59, 60, 61, 62,           # Pre-Use Checklist items
    40, 41, 51, 52, 53, 54,           # FCC sub-items
    201, 202, 203, 204, 205, 206,     # Precautions
    207, 208, 209, 210, 211, 212,
    213, 214, 215, 216, 217, 218,
    219, 220, 221, 222, 223, 224, 225, 226,
    230, 231,                          # Post-operation care
    234, 235, 236, 237, 238, 239,     # Main unit maintenance
    241, 242, 243, 244, 245, 246, 247, 248,  # Battery maintenance
    136, 137, 138,                     # Hotspot steps
    141, 142,                          # Hotspot troubleshooting
    144, 145, 146,                     # Wi-Fi config steps
    131, 132,                          # Activation steps
}

# rId → output image filename
RID_TO_FILENAME = {
    "rId6":  "navi-cover.png",
    "rId7":  "navi-component-front.png",
    "rId8":  "navi-component-back.png",
    "rId9":  "navi-component-side.png",
    "rId12": "navi-startup-posture.png",
    "rId13": "navi-power-button.png",
    "rId14": "navi-remote-front.png",
    "rId15": "navi-remote-back.png",
    "rId16": "navi-remote-buttons.png",
    "rId17": "navi-pairing-step2.png",
    "rId18": "navi-pairing-step3.png",
}

# Alt text for each image
RID_TO_ALT = {
    "rId6":  "NAVI Product Overview",
    "rId7":  "NAVI Component Names – Front View",
    "rId8":  "NAVI Component Names – Back View",
    "rId9":  "NAVI Component Names – Side View",
    "rId12": "NAVI Pre-Startup Posture",
    "rId13": "NAVI Power Button Location",
    "rId14": "Fingertip Remote Controller – Front",
    "rId15": "Fingertip Remote Controller – Back",
    "rId16": "Fingertip Remote Controller – Button Layout",
    "rId17": "Initial Pairing – Step 2",
    "rId18": "Initial Pairing – Step 3",
}


def extract_images(docx_path: Path, out_dir: Path) -> dict[str, Path]:
    """Extract images from docx zip, return {target_ref: saved_path}."""
    out_dir.mkdir(parents=True, exist_ok=True)
    saved: dict[str, Path] = {}
    with zipfile.ZipFile(docx_path) as z:
        for name in z.namelist():
            if name.startswith("word/media/"):
                stem = Path(name).name  # e.g. image1.png
                dest = out_dir / stem
                with z.open(name) as src, open(dest, "wb") as dst:
                    shutil.copyfileobj(src, dst)
                saved[f"media/{stem}"] = dest
    return saved


def get_para_image_rids(para) -> list[str]:
    """Extract rId references from a paragraph's XML."""
    xml = para._element.xml
    return re.findall(r'r:embed="(rId\d+)"', xml)


def clean_text(text: str) -> str:
    return text.strip().rstrip()


def para_to_md(idx: int, text: str, rids: list[str], doc_rels: dict) -> str:
    """Convert one paragraph to Markdown line(s)."""
    lines = []

    # Emit image(s) first
    for rid in rids:
        if rid in RID_TO_FILENAME:
            fname = RID_TO_FILENAME[rid]
            alt = RID_TO_ALT[rid]
            lines.append(f"![{alt}](/images/navi/{fname})\n")

    text = clean_text(text)
    if not text:
        return "\n".join(lines) if lines else ""

    level = HEADING_MAP.get(idx, 0)

    if level > 0:
        lines.append(f"{'#' * level} {text}")
    elif idx in LIST_ITEM_INDICES:
        lines.append(f"- {text}")
    else:
        lines.append(text)

    return "\n".join(lines)


def convert():
    print(f"Reading: {DOCX_PATH}")
    doc = Document(str(DOCX_PATH))

    # Build rel map: rId → target_ref
    doc_rels = {rid: rel.target_ref for rid, rel in doc.part.rels.items()}

    # Extract images
    print(f"Extracting images → {IMG_OUT_DIR}")
    extract_images(DOCX_PATH, IMG_OUT_DIR)

    # Build markdown
    blocks: list[str] = []
    for idx, para in enumerate(doc.paragraphs):
        if idx in SKIP_INDICES:
            continue

        rids = get_para_image_rids(para)
        text = para.text

        md = para_to_md(idx, text, rids, doc_rels)
        if md:
            blocks.append(md)

    # Join: headings get blank line before them
    output_lines: list[str] = []
    for block in blocks:
        first_line = block.split("\n")[0]
        if first_line.startswith("#") and output_lines:
            output_lines.append("")
        output_lines.append(block)

    content = "\n".join(output_lines) + "\n"

    MD_OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    MD_OUT_PATH.write_text(content, encoding="utf-8")
    print(f"Written: {MD_OUT_PATH}")
    print(f"Lines: {len(content.splitlines())}")


if __name__ == "__main__":
    convert()
