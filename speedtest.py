#!/usr/bin/env python3
"""Measure download speed by fetching a URL several times in a row."""

import argparse
import sys
import time
import urllib.error
import urllib.request

CHUNK_SIZE = 64 * 1024  # read the body in 64 KiB pieces


def fetch(url: str, timeout: float) -> tuple[int, float]:
    """Download the whole response body. Return (bytes received, seconds taken)."""
    request = urllib.request.Request(
        url,
        headers={
            # Ask intermediate caches not to serve a stored copy.
            "Cache-Control": "no-cache",
            "User-Agent": "speedtest-script/1.0",
        },
    )
    start = time.perf_counter()
    size = 0
    with urllib.request.urlopen(request, timeout=timeout) as response:
        while chunk := response.read(CHUNK_SIZE):
            size += len(chunk)
    elapsed = time.perf_counter() - start
    return size, elapsed


def format_bytes(n: int) -> str:
    """Human-readable size using decimal units (1 MB = 1,000,000 bytes)."""
    if n < 1000:
        return f"{n} B"
    value = float(n)
    for unit in ("KB", "MB", "GB"):
        value /= 1000
        if value < 1000 or unit == "GB":
            break
    return f"{value:.2f} {unit}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Measure download speed for a URL.")
    parser.add_argument("url", help="address to download, e.g. a large image")
    parser.add_argument("-n", "--count", type=int, default=10,
                        help="number of sequential requests (default: 10)")
    parser.add_argument("-t", "--timeout", type=float, default=30,
                        help="per-request timeout in seconds (default: 30)")
    args = parser.parse_args()

    if args.count < 1:
        parser.error("--count must be at least 1")

    total_bytes = 0
    total_time = 0.0

    for i in range(1, args.count + 1):
        try:
            size, elapsed = fetch(args.url, args.timeout)
        except (urllib.error.URLError, TimeoutError, ValueError) as exc:
            print(f"Request {i} failed: {exc}", file=sys.stderr)
            return 1
        total_bytes += size
        total_time += elapsed
        print(f"Request {i:>2}: {format_bytes(size):>10} in {elapsed:.3f} s")

    avg_time = total_time / args.count
    # bytes * 8 = bits; / 1_000_000 = megabits; / seconds = Mbit/s
    speed_mbps = total_bytes * 8 / 1_000_000 / total_time if total_time > 0 else 0.0

    print()
    print(f"Requests:         {args.count}")
    print(f"Average time:     {avg_time:.3f} s")
    print(f"Total downloaded: {format_bytes(total_bytes)} ({total_bytes} bytes)")
    print(f"Download speed:   {speed_mbps:.2f} Mbit/s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
