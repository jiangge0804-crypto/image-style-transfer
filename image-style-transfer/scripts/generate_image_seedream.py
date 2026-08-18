#!/usr/bin/env python3
"""
Generate images with Jimeng (即梦) "图片 5.0 Lite" = Volcano Ark Seedream 5.0 Lite
(doubao-seedream-5-0-lite-260128) via the Ark API.

- Sync flow: POST /api/v3/images/generations -> data[].url
- Auth: Authorization: Bearer $ARK_API_KEY
- Text-to-image: prompt only
- Image-to-image: additionally --image <local path> (sent in "image" field as a
  base64 data URL; Ark also accepts public URLs)
- Size: pass "adaptive" (follow the reference image's aspect ratio, best for
  style transfer), a tier keyword (1K/2K/4K), or explicit WIDTHxHEIGHT
- Python standard library only; no third-party SDK required
"""

import argparse
import base64
import json
import mimetypes
import os
import re
import sys
import urllib.request
import urllib.error

API_BASE = "https://ark.cn-beijing.volces.com/api/v3"
DEFAULT_MODEL = "doubao-seedream-5-0-lite-260128"
MAX_INLINE_IMAGE_BYTES = 10 * 1024 * 1024  # keep well under platform limits

# 2K-tier presets published for Seedream 5.x Lite (width x height)
ASPECT_PRESETS_2K = {
    "1:1": (2048, 2048),
    "4:3": (2304, 1728),
    "3:4": (1728, 2304),
    "16:9": (2848, 1600),
    "9:16": (1600, 2848),
    "3:2": (2496, 1664),
    "2:3": (1664, 2496),
    "21:9": (4704, 2016),
}


def get_api_key(args):
    if args.api_key:
        return args.api_key
    env_key = os.environ.get("ARK_API_KEY")
    if env_key:
        return env_key
    env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env")
    if os.path.exists(env_file):
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("ARK_API_KEY="):
                    return line.split("=", 1)[1].strip()
    return None


def slugify(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")[:40] or "image"


def encode_image_data_url(image_path):
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")
    size = os.path.getsize(image_path)
    if size > MAX_INLINE_IMAGE_BYTES:
        raise RuntimeError(
            f"Image '{image_path}' is {size / (1024 * 1024):.1f} MB, too large to inline "
            f"(limit {MAX_INLINE_IMAGE_BYTES // (1024 * 1024)} MB). Compress it first."
        )
    mime_type, _ = mimetypes.guess_type(image_path)
    if not mime_type or not mime_type.startswith("image/"):
        mime_type = "image/png"
    with open(image_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def read_image_dimensions(path):
    """Minimal stdlib JPEG/PNG dimension reader."""
    with open(path, "rb") as f:
        head = f.read(32)
        f.seek(0)
        if head[:8] == b"\x89PNG\r\n\x1a\n":
            f.read(16)
            w = int.from_bytes(f.read(4), "big")
            h = int.from_bytes(f.read(4), "big")
            return w, h
        if head[:2] == b"\xff\xd8":  # JPEG: scan for SOF markers
            data = f.read()
            i = 2
            while i < len(data) - 9:
                if data[i] != 0xFF:
                    i += 1
                    continue
                marker = data[i + 1]
                if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
                              0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                    h = int.from_bytes(data[i + 5:i + 7], "big")
                    w = int.from_bytes(data[i + 7:i + 9], "big")
                    return w, h
                if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
                    i += 2
                    continue
                seg_len = int.from_bytes(data[i + 2:i + 4], "big")
                i += 2 + seg_len
    raise RuntimeError("Unsupported image format (need PNG or JPEG) to read dimensions")


def dims_at_tier(width, height, target_pixels=4 * 1024 * 1024):
    """Scale w:h to ~target total pixels (2K tier ~ 4.2MP), even numbers."""
    if width <= 0 or height <= 0:
        return "2048x2048"
    scale = (target_pixels / (width * height)) ** 0.5
    w = max(2, round(width * scale / 2) * 2)
    h = max(2, round(height * scale / 2) * 2)
    return f"{w}x{h}"


def resolve_size(args):
    """Return the value for the `size` request field (WIDTHxHEIGHT / 2k / 3k / 4k)."""
    if args.size:
        return args.size.lower()  # passthrough; API also accepts 2k/3k/4k
    if args.aspect_ratio:
        w, h = ASPECT_PRESETS_2K[args.aspect_ratio]
        return f"{w}x{h}"
    if args.image:
        w, h = read_image_dimensions(args.image)
        return dims_at_tier(w, h)  # keep the reference image's aspect ratio
    return "2k"


def generate_image(prompt, api_key, model=DEFAULT_MODEL, reference_image=None,
                   aspect_ratio=None, size=None, n=1, seed=None,
                   output_dir=".", base_name=None, watermark=False):
    payload = {
        "model": model,
        "prompt": prompt,
        "response_format": "url",
        "watermark": watermark,
        "sequential_image_generation": "disabled",
        "size": resolve_size(type("A", (), {
            "size": size, "image": reference_image, "aspect_ratio": aspect_ratio})()),
    }
    if seed is not None:
        payload["seed"] = seed
    if reference_image:
        payload["image"] = encode_image_data_url(reference_image)

    print(f"Calling Ark {model} ...")
    print(f"  prompt: {prompt[:70]}{'...' if len(prompt) > 70 else ''}")
    print(f"  size: {payload['size']} | reference: {reference_image or 'none'}")

    req = urllib.request.Request(f"{API_BASE}/images/generations",
                                 data=json.dumps(payload).encode("utf-8"),
                                 method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", f"Bearer {api_key}")

    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {e.code}: {body}")

    if result.get("error"):
        err = result["error"]
        raise RuntimeError(f"API error {err.get('code')}: {err.get('message')}")

    data = result.get("data") or []
    urls = [d.get("url") for d in data if d.get("url")]
    if not urls:
        raise RuntimeError(f"No images in response: {json.dumps(result, ensure_ascii=False)[:500]}")

    os.makedirs(output_dir, exist_ok=True)
    stem = base_name or slugify(prompt)
    saved = []
    for i, url in enumerate(urls, start=1):
        suffix = "" if n == 1 and len(urls) == 1 else f"-{i}"
        ext = ".jpg"
        m = re.search(r"\.(jpe?g|png|webp)(?:[?#]|$)", url, re.IGNORECASE)
        if m:
            ext = "." + m.group(1).lower().replace("jpeg", "jpg")
        out_path = os.path.join(output_dir, f"{stem}{suffix}{ext}")
        req_dl = urllib.request.Request(url)
        with urllib.request.urlopen(req_dl, timeout=300) as r, open(out_path, "wb") as f:
            while True:
                chunk = r.read(8192)
                if not chunk:
                    break
                f.write(chunk)
        saved.append(out_path)
        print(f"  saved: {out_path}")

    print(f"Done. {len(saved)} image(s).")
    return saved


def main():
    parser = argparse.ArgumentParser(
        description="Generate images with Jimeng Seedream 5.0 Lite via Volcano Ark (stdlib only)."
    )
    parser.add_argument("prompt", help="Text prompt (Chinese or English)")
    parser.add_argument("--image", help="Local reference image path for image-to-image")
    parser.add_argument("--aspect-ratio", choices=sorted(ASPECT_PRESETS_2K),
                        help="Output aspect ratio at the 2K tier (ignored if --image given without --aspect-ratio; then 'adaptive' follows the reference)")
    parser.add_argument("--size",
                        help="Explicit size: 1K/2K/4K, adaptive, or WIDTHxHEIGHT (overrides aspect ratio)")
    parser.add_argument("--seed", type=int, help="Random seed for reproducibility")
    parser.add_argument("--output-dir", default=".", help="Directory to save images (default cwd)")
    parser.add_argument("--name", help="Base filename for outputs (default: slugified prompt)")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Model ID (default {DEFAULT_MODEL})")
    parser.add_argument("--api-key", help="Ark API key (overrides ARK_API_KEY env)")
    args = parser.parse_args()

    api_key = get_api_key(args)
    if not api_key:
        print("Error: API key not set. Use --api-key or set ARK_API_KEY.\n"
              "Get one at: https://console.volcengine.com/ark/region:cn-beijing/apiKey",
              file=sys.stderr)
        sys.exit(1)

    try:
        saved = generate_image(
            prompt=args.prompt,
            api_key=api_key,
            model=args.model,
            reference_image=args.image,
            aspect_ratio=args.aspect_ratio,
            size=args.size,
            seed=args.seed,
            output_dir=args.output_dir,
            base_name=args.name,
        )
        for p in saved:
            print(p)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
