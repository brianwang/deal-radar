import argparse
import sys

from . import db
from .proposal import write_proposal
from .scoring import score_demand
from .sources.rss import import_rss


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="deal-radar", description="AI 接单助手")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_add = sub.add_parser("add", help="手动添加一条需求")
    p_add.add_argument("--title", required=True)
    p_add.add_argument("--desc", required=True)
    p_add.add_argument("--budget", default="")
    p_add.add_argument("--url", default="")

    p_rss = sub.add_parser("rss", help="从 RSS 导入")
    p_rss.add_argument("url")
    p_rss.add_argument("--source", default="rss", help="来源标记，默认 rss")
    p_rss.add_argument(
        "--keywords", default="", help="逗号分隔，只保留命中关键词的条目"
    )

    p_score = sub.add_parser("score", help="给需求打分")
    p_score.add_argument("id", type=int)

    p_prop = sub.add_parser("proposal", help="生成投标信")
    p_prop.add_argument("id", type=int)

    sub.add_parser("list", help="列出需求")

    args = parser.parse_args(argv)
    db.init_db()

    if args.cmd == "add":
        new_id = db.add_demand(
            "manual", args.title, args.desc, args.url or None, args.budget or None
        )
        print(new_id if new_id else "重复，未添加")
    elif args.cmd == "rss":
        keywords = [k.strip() for k in args.keywords.split(",") if k.strip()] or None
        print(f"新增 {import_rss(args.url, args.source, keywords)} 条")
    elif args.cmd == "score":
        demand = db.get_demand(args.id)
        if not demand:
            sys.exit("需求不存在")
        result = score_demand(demand)
        db.upsert_score(args.id, result["score"], result["reason"], result["risk"])
        print(f"{result['score']} 分 · {result['reason']} · 风险：{result['risk']}")
    elif args.cmd == "proposal":
        demand = db.get_demand(args.id)
        if not demand:
            sys.exit("需求不存在")
        content = write_proposal(demand)
        db.add_proposal(args.id, content)
        print(content)
    elif args.cmd == "list":
        for d in db.list_demands_with_scores():
            score = d["score"] if d["score"] is not None else "-"
            print(f"[{score}] {d['id']}  {d['title']}")


if __name__ == "__main__":
    main()
