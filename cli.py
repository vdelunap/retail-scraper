import argparse

def main():
    parser = argparse.ArgumentParser(description="Invero data-mining CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("score", help="compute StreetScore table")
    vac_parser = sub.add_parser("vacancy", help="detect / flag empty units")
    vac_parser.add_argument(
        "--persist", action="store_true",
        help="write the detected vacancies back to the DB",
    )
    sub.add_parser("heatmap", help="build StreetScore heat-map")

    args = parser.parse_args()

    if args.cmd == "score":
        from mining.kpi_score import main as m
        m()
    elif args.cmd == "vacancy":
        from mining.vacancy_finder import run
        run(persist=args.persist)
    elif args.cmd == "heatmap":
        from mining.heatmap import build
        path = build()
        print(f"Open {path} in your browser")
    else:
        parser.print_help()


if __name__ == "__main__":
	main()
