#!/usr/bin/env python3
"""Command-line entry point for the China A-share Fama-French factors.

Examples
--------
    python run.py                         # standard FF3, value-weighted
    python run.py --lsy                   # drop the smallest 30% of stocks first
    python run.py --lsy --equal-weight    # filtered and equal-weighted
    python run.py --backend sina          # force the Sina price backend
    python run.py --step 2                # stop after downloading prices
    python run.py --plot                  # also save a cumulative-return chart
"""

from __future__ import annotations

import argparse
import sys

from ff3_china import Config, run_pipeline
from ff3_china.report import plot_cumulative


def parse_args(argv=None) -> argparse.Namespace:
    d = Config()   # defaults shown in --help come from the Config class
    p = argparse.ArgumentParser(
        description="Build daily Mkt_RF, SMB and HML factors for China A-shares.")

    p.add_argument("--start-year", type=int, default=d.start_year,
                   help=f"first rebalance year (default {d.start_year})")
    p.add_argument("--end-year", type=int, default=d.end_year,
                   help=f"last rebalance year (default {d.end_year})")
    p.add_argument("--lsy", action="store_true",
                   help="apply the Liu-Stambaugh-Yuan shell-stock filter")
    p.add_argument("--lsy-cutoff", type=float, default=d.lsy_size_cutoff,
                   help=f"share of smallest stocks to drop (default {d.lsy_size_cutoff})")
    p.add_argument("--equal-weight", action="store_true",
                   help="equal-weighted portfolios (default: value-weighted)")
    p.add_argument("--shares-year-offset", type=int, choices=(0, -1),
                   default=d.shares_year_offset,
                   help="0: shares file is dated on rebalance dates (default); "
                        "-1: it holds year-end values")
    p.add_argument("--backend", choices=("auto", "em", "sina"), default=d.backend,
                   help="price source: EastMoney, Sina or auto-detect (default)")
    p.add_argument("--step", type=int, choices=range(1, 7), metavar="1-6",
                   help="stop after this step (1 universe, 2 prices, 3 financials, "
                        "4 risk-free, 5 assignments, 6 factors)")
    p.add_argument("--data-dir", default=str(d.data_dir),
                   help=f"folder with the WIND CSV files (default {d.data_dir})")
    p.add_argument("--cache-dir", default=str(d.cache_dir),
                   help=f"folder for downloaded data (default {d.cache_dir})")
    p.add_argument("--output-dir", default=str(d.output_dir),
                   help=f"folder for results (default {d.output_dir})")
    p.add_argument("--plot", action="store_true",
                   help="save a cumulative-return chart to <output-dir>/figures")
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    cfg = Config(
        start_year=args.start_year,
        end_year=args.end_year,
        # Prices start a year before the first rebalance and run to year end.
        data_start=f"{args.start_year - 1}-07-01",
        data_end=f"{args.end_year}-12-31",
        lsy_filter=args.lsy,
        lsy_size_cutoff=args.lsy_cutoff,
        value_weighted=not args.equal_weight,
        shares_year_offset=args.shares_year_offset,
        backend=args.backend,
        data_dir=args.data_dir,
        cache_dir=args.cache_dir,
        output_dir=args.output_dir,
    )

    try:
        result = run_pipeline(cfg, step=args.step)
    except KeyboardInterrupt:
        print("\nInterrupted. Progress is cached; run again to resume.")
        return 130

    if args.plot and args.step is None:
        path = cfg.output_dir / "figures" / f"cumulative_{cfg.tag}.png"
        plot_cumulative(result, title=f"China A-share factors [{cfg.tag}]", path=path)
        print(f"  Chart saved to {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
