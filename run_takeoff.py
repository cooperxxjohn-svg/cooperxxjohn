"""
CLI entry point for the construction takeoff pipeline.

Usage:
    python run_takeoff.py --pdf path/to/plans.pdf --project "Office Building"
    python run_takeoff.py --images a1.png a2.png --project "Test"
    python run_takeoff.py --pdf plans.pdf --pages 5 --out ./output
"""

import argparse
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("takeoff.cli")


def main():
    parser = argparse.ArgumentParser(
        description="Construction drawing quantity takeoff using Claude Vision"
    )

    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--pdf",    metavar="FILE",  help="PDF drawing set")
    source.add_argument("--images", metavar="FILE", nargs="+", help="Image files")

    parser.add_argument("--project", default="",  help="Project name")
    parser.add_argument("--out",     default="./takeoff_output", help="Output directory")
    parser.add_argument("--pages",   type=int, default=None, help="Max pages to process (PDF only)")
    parser.add_argument("--model",   default="claude-opus-4-5", help="Claude model ID")
    parser.add_argument("--dpi",     type=int, default=200,  help="PDF render DPI (150-300)")
    parser.add_argument("--json",    action="store_true",    help="Print full JSON to stdout")

    args = parser.parse_args()

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY environment variable not set.", file=sys.stderr)
        sys.exit(1)

    from takeoff_pipeline import TakeoffPipeline

    pipeline = TakeoffPipeline(
        api_key=api_key,
        model=args.model,
        dpi=args.dpi,
    )

    if args.pdf:
        pdf_path = Path(args.pdf)
        if not pdf_path.exists():
            print(f"ERROR: File not found: {pdf_path}", file=sys.stderr)
            sys.exit(1)
        logger.info("Processing PDF: %s", pdf_path)
        result = pipeline.process_pdf(
            pdf_path,
            project_name=args.project or pdf_path.stem,
            page_limit=args.pages,
        )
    else:
        image_paths = [Path(p) for p in args.images]
        missing = [p for p in image_paths if not p.exists()]
        if missing:
            print(f"ERROR: Files not found: {missing}", file=sys.stderr)
            sys.exit(1)
        logger.info("Processing %d image(s)", len(image_paths))
        result = pipeline.process_images(image_paths, project_name=args.project)

    # Print summary to terminal
    pipeline.print_summary(result)

    # Save JSON
    out_path = pipeline.save_result(result, args.out)
    print(f"Full result saved to: {out_path}")

    if args.json:
        import json
        print(json.dumps(result.to_dict(), indent=2, default=str))


if __name__ == "__main__":
    main()
