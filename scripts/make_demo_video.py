#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "demo-video"
W, H = 1280, 720
GREEN = (96, 255, 64)
INK = (19, 27, 22)
PAPER = (246, 248, 241)
MUTED = (92, 105, 94)
CARD = (255, 255, 255)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/SFNS.ttf",
        "/Library/Fonts/Arial.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


TITLE = font(54, True)
SUBTITLE = font(30)
BODY = font(26)
SMALL = font(21)
MONO = font(20)


def rounded(draw: ImageDraw.ImageDraw, box, fill, outline=None, width=1, radius=18):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def wrapped(draw: ImageDraw.ImageDraw, text: str, xy, max_width: int, fnt, fill=INK, spacing=8):
    words = text.split()
    lines = []
    current = ""
    for word in words:
        trial = f"{current} {word}".strip()
        if draw.textbbox((0, 0), trial, font=fnt)[2] <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    x, y = xy
    for line in lines:
        draw.text((x, y), line, font=fnt, fill=fill)
        y += fnt.size + spacing
    return y


def base(title: str, subtitle: str | None = None) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (W, H), PAPER)
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, W, 14), fill=GREEN)
    draw.text((72, 58), "Paid Bounty Triage Agent", font=SMALL, fill=MUTED)
    draw.text((72, 112), title, font=TITLE, fill=INK)
    if subtitle:
        wrapped(draw, subtitle, (74, 188), 980, SUBTITLE, MUTED, spacing=10)
    return img, draw


def bullets(draw: ImageDraw.ImageDraw, items: list[str], y: int, x: int = 96, width: int = 1040):
    for item in items:
        draw.ellipse((x, y + 10, x + 14, y + 24), fill=GREEN)
        y = wrapped(draw, item, (x + 30, y), width, BODY, INK, spacing=8) + 18
    return y


def save_slide(idx: int, img: Image.Image):
    OUT.mkdir(exist_ok=True)
    path = OUT / f"slide-{idx:02d}.png"
    img.save(path)
    return path


def make_slides() -> list[Path]:
    slides: list[Path] = []

    img, draw = base(
        "Bounty decisions should be callable",
        "A requester submits a bounty or hackathon link and pays for a fast agent triage before spending serious build time.",
    )
    bullets(draw, [
        "Input: bounty, GitHub issue, or hackathon URL",
        "Output: priority, token estimate, cash probability, risks, and delivery checklist",
        "Commerce loop: paid call record, settlement request, receipt, and reproducible artifacts",
    ], 310)
    slides.append(save_slide(1, img))

    img, draw = base("Agent call flow")
    columns = [
        ("1. Call", "CLI call or HTTP POST /call"),
        ("2. Triage", "Fit, priority, token budget, cash odds"),
        ("3. Settle", "Mock USDC receipt today; CAP adapter boundary for real settlement"),
    ]
    x = 72
    for heading, text in columns:
        rounded(draw, (x, 230, x + 340, 520), CARD, outline=(210, 219, 203), radius=14)
        draw.text((x + 28, 258), heading, font=SUBTITLE, fill=INK)
        wrapped(draw, text, (x + 28, 324), 280, BODY, MUTED)
        x += 390
    slides.append(save_slide(2, img))

    receipt_path = ROOT / "artifacts/latest-http-demo/receipt.json"
    receipt = json.loads(receipt_path.read_text()) if receipt_path.exists() else {}
    img, draw = base("Mock receipt is explicit")
    rounded(draw, (72, 235, 1208, 560), CARD, outline=(210, 219, 203), radius=14)
    lines = [
        f"settlement_status: {receipt.get('settlement_status', 'MOCK_SETTLED')}",
        f"amount: {receipt.get('amount', 0.25)} USDC",
        f"tx_hash: {receipt.get('tx_hash', 'mock-croo-...')}",
        "events: NEGOTIATION_CREATED -> ORDER_CREATED -> ORDER_PAID -> ORDER_COMPLETED",
        "private_keys_handled: false",
        "wallet confirmation in real mode: required",
    ]
    y = 270
    for line in lines:
        draw.text((106, y), line, font=MONO, fill=INK)
        y += 44
    slides.append(save_slide(3, img))

    img, draw = base("Verified local run")
    screenshot_path = ROOT / "artifacts/latest-http-demo/run-screenshot.png"
    if screenshot_path.exists():
        shot = Image.open(screenshot_path).convert("RGB")
        shot.thumbnail((1040, 430))
        rounded(draw, (72, 210, 1208, 645), CARD, outline=(210, 219, 203), radius=14)
        img.paste(shot, (120, 235))
    else:
        bullets(draw, ["Screenshot missing; rerun the local demo to regenerate it."], 300)
    slides.append(save_slide(4, img))

    img, draw = base("Real CROO CAP replacement")
    bullets(draw, [
        "Python SDK: croo-sdk; Node SDK: @croo-network/sdk",
        "Requester: negotiate_order, then pay_order after AA wallet funding and human approval",
        "Provider: accept_negotiation, then deliver_order",
        "Requester retrieves delivery with get_delivery",
        "Default SDK RPC points to Base mainnet; payment asset is USDC",
    ], 240)
    slides.append(save_slide(5, img))

    img, draw = base("Submission package is ready")
    bullets(draw, [
        "Public repo: github.com/Lukeknow0/paid-bounty-triage-agent",
        "README, architecture diagram, rules check, submission copy, and release zip",
        "Evidence: triage_report.md, receipt.json, demo.log, run-screenshot.png",
        "Remaining external step: record/upload final video URL and submit DoraHacks BUIDL",
    ], 250)
    slides.append(save_slide(6, img))
    return slides


def main() -> int:
    slides = make_slides()
    concat = OUT / "slides.txt"
    duration = 7
    lines: list[str] = []
    for slide in slides:
        lines.append(f"file '{slide.name}'")
        lines.append(f"duration {duration}")
    lines.append(f"file '{slides[-1].name}'")
    concat.write_text("\n".join(lines) + "\n", encoding="utf-8")
    mp4 = OUT / "paid-bounty-triage-demo.mp4"
    subprocess.run([
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        concat.name,
        "-vf",
        "fps=30,format=yuv420p",
        "-movflags",
        "+faststart",
        mp4.name,
    ], cwd=OUT, check=True)
    print(mp4)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
