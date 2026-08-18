#!/usr/bin/env python3
"""
Generate images with MiniMax image-01 via the MiniMax open platform API
(api.minimaxi.com, mainland-China direct).

- Sync flow: POST /v1/image_generation -> data.image_urls / data.image_base64
- Auth: Authorization: Bearer $MINIMAX_API_KEY (same key as MiniMax-H3 video)
- Text-to-image: --prompt only
- Image-to-image: additionally --image <local path> (sent as subject_reference,
  base64 data URL inline; up to 1 reference for image-01)
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

API_BASE = "https://api.minimaxi.com"
DEFAULT_MODEL = "image-01"
ASPECT_RATIOS = ["1:1", "16:9", "4:3", "3:2", "2:3", "3:4", "9:16", "21:9"]
MAX_INLINE_IMAGE_BYTES = 10 * 1024 * 1024  # keep well under platform limits


def get_api_key(args):
    if args.api_key:
        return args.api_key
    env_key = os.environ.get("MINIMAX_API_KEY")
    if env_key:
        return env_key
    env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env")
    if os.path.exists(env_file):
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("MINIMAX_API_KEY="):
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


def generate_image(prompt, api_key, model=DEFAULT_MODEL, aspect_ratio=None,
                   reference_image=None, n=1, seed=None, output_dir=".",
                   base_name=None, watermark=False):
    payload = {
        "model": model,
        "prompt": prompt,
        "n": n,
        "response_format": "url",
        "watermark": watermark,
    }
    if aspect_ratio:
        payload["aspect_ratio"] = aspect_ratio
    if seed is not None:
        payload["seed"] = seed
    if reference_image:
        payload["subject_reference"] = [
            {"type": "character", "image_file": encode_image_data_url(reference_image)}
        ]

    print(f"Calling MiniMax {model} ...")
    print(f"  prompt: {prompt[:70]}{'...' if len(prompt) > 70 else ''}")
    print(f"  aspect_ratio: {aspect_ratio or 'default(1:1)'} | n: {n} | reference: {reference_image or 'none'}")

    req = urllib.request.Request(f"{API_BASE}/v1/image_generation",
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

    base_resp = result.get("base_resp") or {}
    if base_resp.get("status_code", 0) not in (0, None):
        raise RuntimeError(f"API error {base_resp.get('status_code')}: {base_resp.get('status_msg')}")

    urls = (result.get("data") or {}).get("image_urls") or []
    if not urls:
        raise RuntimeError(f"No images in response: {json.dumps(result, ensure_ascii=False)[:500]}")

    os.makedirs(output_dir, exist_ok=True)
    stem = base_name or slugify(prompt)
    saved = []
    for i, url in enumerate(urls, start=1):
        suffix = "" if n == 1 else f"-{i}"
        # MiniMax returns jpeg/png URLs; keep extension from URL, default jpg
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

    meta = result.get("metadata") or {}
    print(f"Done. success={meta.get('success_count', len(saved))} failed={meta.get('failed_count', 0)}")
    return saved


def main():
    parser = argparse.ArgumentParser(
        description="Generate images with MiniMax image-01 (api.minimaxi.com, stdlib only)."
    )
    parser.add_argument("prompt", help="Text prompt (Chinese or English, max 1500 chars)")
    parser.add_argument("--image", help="Local reference image path for image-to-image (subject_reference)")
    parser.add_argument("--aspect-ratio", choices=ASPECT_RATIOS,
                        help="Output aspect ratio (default: 1:1; with reference image, keep same ratio as source for style transfer)")
    parser.add_argument("--n", type=int, default=1, help="Number of images, 1-9 (default 1)")
    parser.add_argument("--seed", type=int, help="Random seed for reproducibility")
    parser.add_argument("--output-dir", default=".", help="Directory to save images (default cwd)")
    parser.add_argument("--name", help="Base filename for outputs (default: slugified prompt)")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Model name (default {DEFAULT_MODEL})")
    parser.add_argument("--api-key", help="MiniMax API key (overrides MINIMAX_API_KEY env)")
    args = parser.parse_args()

    if not 1 <= args.n <= 9:
        print("Error: --n must be between 1 and 9.", file=sys.stderr)
        sys.exit(1)

    api_key = get_api_key(args)
    if not api_key:
        print("Error: API key not set. Use --api-key or set MINIMAX_API_KEY.\n"
              "Get one at: https://platform.minimaxi.com/user-center/basic-information/interface-key",
              file=sys.stderr)
        sys.exit(1)

    try:
        saved = generate_image(
            prompt=args.prompt,
            api_key=api_key,
            model=args.model,
            aspect_ratio=args.aspect_ratio,
            reference_image=args.image,
            n=args.n,
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
