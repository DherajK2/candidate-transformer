#!/usr/bin/env python3
"""
Main entry point and CLI wrapper for the Multi-Source Candidate Data Transformer.
Provides a terminal-styled interface with colorful status logs and helper tips.
"""

import argparse
import json
import logging
from pathlib import Path
import sys
from typing import List

from src.pipeline import CandidatePipeline
from src.utils.logger import configure_logging, get_logger

logger = get_logger("cli.main")

BANNER = r"""\033[36m
  ____ ___  _   _ ____ ___ ____   ___ _____ _____ 
 / ___/ _ \| \ | |  _ \_ _|  _ \ / _ \_   _| ____|
| |  | | | |  \| | | | | || | | | | | || | |  _|  
| |__| |_| | |\  | |_| | || |_| | |_| || | | |___ 
 \____\___/|_| \_|____/___|____/ \___/ |_| |_____|
                                  
   CANDIDATE DATA TRANSFORMER v1.0.0
\033[0m"""

TIPS = """\033[90mTips for getting started:
1. Pass structured sources (CSV/JSON) and unstructured sources (PDF/TXT) together.
2. Provide a projection config (e.g. config/custom_projection.json) to custom-shape the output.
3. Check debug logs by running with --debug.
\033[0m"""


def print_cli_header(debug: bool) -> None:
    """Prints a beautiful styled CLI header in the terminal."""
    print(BANNER)
    print(TIPS)
    mode_str = "\033[35mdebug-mode\033[0m" if debug else "\033[32mproduction-mode\033[0m"
    print(f"\033[90mSystem Status: {mode_str} | Sandbox: active | Engine: pipeline-v1\033[0m")
    print("-" * 70)


def main() -> None:
    """Parses command-line arguments and executes the pipeline."""
    parser = argparse.ArgumentParser(
        description="Transform heterogeneous candidate inputs into a canonical schema."
    )
    # File flags
    parser.add_argument("--csv", type=str, help="Path to structured recruiter CSV file")
    parser.add_argument("--json", type=str, help="Path to structured ATS JSON file")
    parser.add_argument("--resume", type=str, help="Path to unstructured Resume (PDF or TXT)")
    
    # Generic positional list (accepts any other files)
    parser.add_argument("files", nargs="*", help="Optional positional input files of any format (CSV/JSON/PDF/TXT)")
    
    # Config/Output flags
    parser.add_argument("--config", type=str, help="Path to JSON projection config file")
    parser.add_argument("--output", type=str, help="Path to write the resulting JSON profile")
    
    # Logging flag
    parser.add_argument("--debug", action="store_true", help="Enable verbose debug logging")

    args = parser.parse_args()

    # Configure logging level
    log_level = logging.DEBUG if args.debug else logging.INFO
    configure_logging(log_level)

    print_cli_header(args.debug)

    # Consolidate input file paths
    input_paths: List[Path] = []
    
    if args.csv:
        input_paths.append(Path(args.csv))
    if args.json:
        input_paths.append(Path(args.json))
    if args.resume:
        input_paths.append(Path(args.resume))

    # Add any positional files
    for f in args.files:
        input_paths.append(Path(f))

    # Remove duplicates preserving order
    unique_paths = []
    for p in input_paths:
        if p not in unique_paths:
            unique_paths.append(p)
    input_paths = unique_paths

    if not input_paths:
        logger.error("No input files provided! You must specify at least one file.")
        parser.print_help()
        sys.exit(1)

    logger.info(f"Loaded {len(input_paths)} source file paths.")
    for p in input_paths:
        if not p.exists():
            logger.critical(f"Input file not found: {p}")
            sys.exit(1)
        logger.debug(f"Input source validated: {p.name} ({p.suffix})")

    config_path = Path(args.config) if args.config else None
    output_path = Path(args.output) if args.output else None

    # Execute Transformation pipeline
    try:
        pipeline = CandidatePipeline()
        output_data = pipeline.run(
            source_paths=input_paths,
            config_path=config_path
        )
        
        # Output handling
        json_output = json.dumps(output_data, indent=2)
        if output_path:
            # Ensure parent directories exist
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(json_output)
            logger.info(f"\033[32mSUCCESS\033[0m | Canonical profile written to: {output_path}")
        else:
            print("\n" + "="*30 + " TRANSFORMED CANONICAL OUTPUT " + "="*30)
            print(json_output)
            print("="*88)

    except Exception as e:
        logger.critical(f"\033[31mPIPELINE FAILED\033[0m | {str(e)}")
        if args.debug:
            raise e
        sys.exit(1)


if __name__ == "__main__":
    main()
