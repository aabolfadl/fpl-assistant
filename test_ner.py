#!/usr/bin/env python3
"""
Test script for entity extraction improvements
Run this to test NER without running the full pipeline ONLY FOR TESTING PURPOSES!!!
"""


from modules.preprocessing import extract_entities
import json


def test_query(query: str):
    """Test a single query and print results"""
    print(f"\n{'='*60}")
    print(f"QUERY: {query}")
    print(f"{'='*60}")

    entities = extract_entities(query)

    for entity_type, values in entities.items():
        if values:  # Only print non-empty entities
            print(f"\n{entity_type.upper()}:")
            for value in values:
                print(f"  - {value}")

    if not any(entities.values()):
        print("\nNo entities extracted")

    return entities


def run_tests():
    """Run a set of test queries"""

    test_queries = [
        # Player tests
        "How did Salah perform in GW5?",
        "Compare Haaland and Kane goals",
        "Show me Mohamed Salah stats",
        # Team tests
        "Man City clean sheets",
        "Liverpool vs Chelsea",
        "How did MCI do?",
        "Spurs defense",
        # Season tests
        "season 22 stats",
        "2021-22 data",
        "in 21",
        # Statistics tests
        "show me assists",
        "cs and yc",
        "ict index",
        "goals scored",
        # Combined tests
        "Salah goals for Liverpool in season 22",
        "MCI defenders cs in GW10",
        "Show Kane and Son assists for Spurs",
        "players under 6.0 ",
    ]

    print("\n" + "=" * 60)
    print("TESTING ENTITY EXTRACTION")
    print("=" * 60)

    for query in test_queries:
        test_query(query)

    print(f"\n{'='*60}")
    print("TESTING COMPLETE")
    print(f"{'='*60}\n")


def interactive_mode():
    """Interactive mode - test your own queries"""
    print("\n" + "=" * 60)
    print("INTERACTIVE TESTING MODE")
    print("=" * 60)
    print("Enter queries to test (or 'quit' to exit)")
    print()

    while True:
        query = input("Query: ").strip()

        if query.lower() in ["quit", "exit", "q"]:
            break

        if not query:
            continue

        test_query(query)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        # Test a specific query from command line
        query = " ".join(sys.argv[1:])
        test_query(query)
    else:
        # Show menu
        print("\nNER Testing Options:")
        print("1. Run predefined test queries")
        print("2. Interactive mode (test your own queries)")
        print()
        choice = input("Choose option (1 or 2): ").strip()

        if choice == "1":
            run_tests()
        elif choice == "2":
            interactive_mode()
        else:
            print("Invalid choice")
