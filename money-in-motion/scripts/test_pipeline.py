"""Quick smoke test script for individual pipeline steps."""

from __future__ import annotations

import argparse
import logging
import sys

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def test_detect():
    from src.detectors import SecForm4Detector
    detector = SecForm4Detector()
    events = detector.detect(lookback_hours=24)
    print(f"\nFound {len(events)} Form 4 filings\n")
    for i, event in enumerate(events[:5], 1):
        print(f"  [{i}] {event.person_name} @ {event.company_name}")
        print(f"      Filed: {event.filed_at}")
        print(f"      Source ID: {event.source_id}")
        print(f"      URL: {event.url}")
        if event.raw_data.get("xml_enriched"):
            print(f"      Transaction type: {event.raw_data.get('transaction_type')}")
            print(f"      Shares: {event.raw_data.get('shares')}")
            print(f"      Price: ${event.raw_data.get('price_per_share')}")
            print(f"      Total value: ${event.raw_data.get('total_value')}")
            print(f"      Insider title: {event.raw_data.get('insider_title')}")
        print()


def test_enrich():
    from src.enrichment import ApolloProvider
    provider = ApolloProvider()
    result = provider.enrich("Tim Cook", "Apple")
    if result:
        print(f"Email: {result.email}")
        print(f"Phone: {result.phone}")
        print(f"LinkedIn: {result.linkedin_url}")
        print(f"Title: {result.job_title}")
        print(f"Status: {result.status}")
    else:
        print("No enrichment result (check API key)")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--step", choices=["detect", "enrich"], required=True)
    args = parser.parse_args()

    if args.step == "detect":
        test_detect()
    elif args.step == "enrich":
        test_enrich()


if __name__ == "__main__":
    main()
