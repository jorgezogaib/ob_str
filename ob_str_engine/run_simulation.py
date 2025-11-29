#!/usr/bin/env python3
import argparse
from pathlib import Path
from engine.simulator import simulate

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", type=Path, required=True)
    parser.add_argument("--years", type=int, default=30)
    parser.add_argument("--out-prefix", type=str, default="out/OB_STR_V2_3")
    args = parser.parse_args()

    result = simulate(args.engine, years=args.years)
    out = Path(args.out_prefix)
    out.parent.mkdir(parents=True, exist_ok=True)
    result.monthly.to_csv(out.with_name(out.name + "_Monthly.csv"), index=False)
    result.yearly.to_csv(out.with_name(out.name + "_YearOverYear.csv"), index=False)
    print("Done")

if __name__ == "__main__":
    main()