"""Simple performance stub.

Will evolve to measure actual frame rendering once embedded pygame surface is
implemented. For now it simulates frame timing to validate harness.
"""
from __future__ import annotations

from time import perf_counter, sleep
import json


def run(duration_s: float = 2.0, target_fps: float = 60.0) -> dict[str, float]:
    frame_interval = 1.0 / target_fps
    start = perf_counter()
    frames = 0
    while True:
        now = perf_counter()
        if now - start >= duration_s:
            break
        # simulate lightweight work
        sleep(frame_interval * 0.4)  # sleep less than full interval to simulate processing
        frames += 1
    elapsed = perf_counter() - start
    return {"frames": frames, "duration_s": elapsed, "avg_fps": frames / elapsed if elapsed else 0.0}


def main() -> None:  # pragma: no cover - simple script
    data = run()
    print(json.dumps(data))


if __name__ == "__main__":
    main()
