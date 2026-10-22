#!/usr/bin/env python3
"""
AgroWise AI Load Testing & Concurrency Benchmark Utility (Task 4c).
Simulates concurrent farmer requests against the full recommendation pipeline and weather guidance.
Computes throughput (req/s), P50, P95, and P99 response latencies.
"""

import argparse
import asyncio
import os
import sys
import time
from typing import Any, Dict, List

# Ensure repo root is on sys.path
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

import httpx
import numpy as np

# Sample realistic Soil Health Card test payload for Cauvery Delta Rice
SAMPLE_PAYLOAD = {
    "crop": "Rice",
    "district": "Thanjavur",
    "soil_series": "Palavidhi",
    "season": "Kharif",
    "irrigation_method": "Irrigated",
    "target_yield": 6.0,
    "soil_nitrogen": 220.0,
    "soil_phosphorus": 16.0,
    "soil_potassium": 190.0,
    "soil_phosphorus_method": "Olsen",
    "farm_area": 2.5,
    "farm_area_unit": "acre",
    "previous_crop": "Blackgram",
    "fym_applied_t_per_ha": 5.0
}


async def _send_request(client: httpx.AsyncClient, base_url: str, endpoint: str, payload: Dict[str, Any] = None) -> float:
    t0 = time.perf_counter()
    if payload:
        resp = await client.post(f"{base_url}{endpoint}", json=payload)
    else:
        resp = await client.get(f"{base_url}{endpoint}")
    lat_ms = (time.perf_counter() - t0) * 1000.0
    if resp.status_code != 200:
        raise RuntimeError(f"Request failed with status {resp.status_code}: {resp.text[:100]}")
    return lat_ms


async def run_benchmark(base_url: str, concurrency: int, total_requests: int):
    print(f"\n=============================================================")
    print(f" AgroWise AI Concurrency & Load Benchmark")
    print(f" Target: {base_url}")
    print(f" Concurrency: {concurrency} workers | Total Requests: {total_requests}")
    print(f"=============================================================\n")

    # If testing against in-process app
    app = None
    transport = None
    if base_url.startswith("asgi://"):
        from phase3_soil.main import app as fastapi_app
        transport = httpx.ASGITransport(app=fastapi_app)
        base_url = "http://testserver"

    async with httpx.AsyncClient(transport=transport, timeout=30.0) as client:
        # Warmup request
        print("Warming up API pipeline and ML/optimization caches...")
        try:
            await _send_request(client, base_url, "/api/full-recommendation", SAMPLE_PAYLOAD)
            await _send_request(client, base_url, "/api/weather/guidance?district=Thanjavur")
            print("Warmup successful.\n")
        except Exception as e:
            print(f"Warmup warning: {e}\n")

        print(f"Running {total_requests} full pipeline requests across {concurrency} parallel workers...")
        latencies: List[float] = []
        errors = 0

        semaphore = asyncio.Semaphore(concurrency)

        async def worker(idx: int):
            nonlocal errors
            async with semaphore:
                # Alternate between full recommendation and weather guidance
                endpoint = "/api/full-recommendation" if idx % 2 == 0 else "/api/weather/guidance?district=Thanjavur"
                p = SAMPLE_PAYLOAD if idx % 2 == 0 else None
                try:
                    lat = await _send_request(client, base_url, endpoint, p)
                    latencies.append(lat)
                except Exception as ex:
                    errors += 1

        t_start = time.perf_counter()
        tasks = [worker(i) for i in range(total_requests)]
        await asyncio.gather(*tasks)
        total_time_sec = time.perf_counter() - t_start

    successful = len(latencies)
    throughput = successful / total_time_sec if total_time_sec > 0 else 0

    print("\n---------------- Benchmark Results ----------------")
    print(f"Total Completed:   {successful}/{total_requests} ({errors} errors)")
    print(f"Total Time Taken:  {total_time_sec:.2f} s")
    print(f"Throughput:        {throughput:.1f} requests/second")

    if latencies:
        p50 = float(np.percentile(latencies, 50))
        p90 = float(np.percentile(latencies, 90))
        p95 = float(np.percentile(latencies, 95))
        p99 = float(np.percentile(latencies, 99))
        print(f"Latency Mean:      {np.mean(latencies):.2f} ms")
        print(f"Latency P50:       {p50:.2f} ms")
        print(f"Latency P90:       {p90:.2f} ms")
        print(f"Latency P95:       {p95:.2f} ms")
        print(f"Latency P99:       {p99:.2f} ms")
    print("---------------------------------------------------\n")


def main():
    parser = argparse.ArgumentParser(description="AgroWise AI Load Testing Benchmark")
    parser.add_argument("--url", default="asgi://local", help="Base URL to test or asgi://local for in-process")
    parser.add_argument("--concurrency", type=int, default=10, help="Number of concurrent workers")
    parser.add_argument("--requests", type=int, default=30, help="Total requests to execute")
    args = parser.parse_args()

    asyncio.run(run_benchmark(args.url, args.concurrency, args.requests))


if __name__ == "__main__":
    main()
