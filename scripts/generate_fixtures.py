"""Create original English demo data. Never read upstream persona text."""
import argparse
import json
from pathlib import Path

# Evaluation requests are fixed independently of descriptions and sidecar templates.
# These public demonstration cases cannot serve as a blind production evaluation.
TASKS = {
    "engineering": [("compiler", "Explain why this compiler rejects nested expressions"),
                    ("storage", "Diagnose storage stalls during a checkpoint operation"),
                    ("scheduler", "Investigate scheduler starvation under competing batch jobs")],
    "finance": [("ledger", "Find ledger inconsistencies across the closing worksheet"),
                ("invoice", "Investigate invoice discrepancies in the vendor register"),
                ("budget", "Compare budget assumptions against the department forecast")],
    "design": [("typography", "Review typography choices for a dense reading interface"),
               ("navigation", "Explain navigation confusion in the settings screen"),
               ("contrast", "Assess contrast problems across the control states")],
    "marketing": [("newsletter", "Outline newsletter themes for the upcoming release"),
                  ("positioning", "Clarify positioning for a technical buyer audience"),
                  ("campaign", "Evaluate campaign messaging against the launch brief")],
    "testing": [("fuzzing", "Prioritize fuzzing inputs for a structured parser"),
                ("fixture", "Diagnose fixture contamination between independent test cases"),
                ("coverage", "Identify coverage gaps in the validation suite")],
    "game": [("puzzle", "Refine puzzle clues to reduce accidental ambiguity"),
             ("animation", "Review animation timing for the player controls"),
             ("economy", "Evaluate economy balance across the upgrade choices")],
    "support": [("ticket", "Resolve ticket confusion around the account workflow"),
                ("knowledge", "Organize knowledge articles around recurring service questions"),
                ("onboarding", "Diagnose onboarding friction in the activation journey")],
    "product": [("roadmap", "Compare roadmap priorities with current delivery constraints"),
                ("discovery", "Plan discovery interviews about the adoption barriers"),
                ("retention", "Investigate retention changes after the trial redesign")],
}
EXTRAS = {
    "engineering": ("network", "deployment"), "finance": ("cashflow", "valuation"),
    "design": ("iconography", "layout"), "marketing": ("audience", "editorial"),
    "testing": ("mutation", "regression"), "game": ("combat", "narrative"),
    "support": ("documentation", "escalation"), "product": ("feedback", "prioritization"),
}
GARBAGE = ["", "zxvqq jkkzz vvv", "kkkkkkkk", "00000000",
           "Where did my umbrella go", "Sing a tune about clouds",
           "Good evening everyone", "zzqqzzqq jjjjj"]


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=True) + "\n")


def generate(destination):
    root = Path(destination)
    root.mkdir(parents=True, exist_ok=True)
    categories, utterances, keywords, cases = {}, {}, {}, []
    twin_categories = list(TASKS)[:3]
    for category, tasks in TASKS.items():
        roles = [role for role, _ in tasks] + list(EXTRAS[category])
        if category in twin_categories:
            roles[-1] = roles[0] + "-twin"
        personas = []
        for role in roles:
            topic = role.removesuffix("-twin")
            name = f"demo-{category}-{role}"
            title = role.replace("-", " ").title() + " Specialist"
            description = f"Review {topic} work, explain tradeoffs, and propose checkable deliverables."
            relative = f"{category}/{role}.md"
            (root / category).mkdir(exist_ok=True)
            (root / relative).write_text(f"# {title}\n\n{description}\n\nSynthetic demonstration persona.\n")
            p = dict(name=name, title=title, description=description, category=category,
                     path=relative, tags=[category], keywords=[topic], capabilities=[category])
            if role.endswith("-twin"):
                p["twin_of"] = f"demo-{category}-{topic}"
                p["representation"] = "English alias for translated-twin accept-set mechanics"
            personas.append(p)
            utterances[name] = [f"Inspect the {topic} proposal", f"Explain this {topic} failure",
                                f"Review a {topic} change", f"Draft a {topic} checklist",
                                f"Improve the {topic} workflow"]
        categories[category] = dict(count=len(personas), personas=personas)
        for role, prompt in tasks:
            case = dict(prompt=prompt, expect=f"demo-{category}-{role}")
            if category in twin_categories and role == tasks[0][0]:
                case["accept"] = [case["expect"] + "-twin"]
            cases.append(case)
    keywords["demo-finance-ledger"] = ["reconciliation"]
    index = dict(synthetic=True, total_personas=sum(c["count"] for c in categories.values()),
                 categories=categories)
    write_json(root / "INDEX.json", index)
    write_json(root / "UTTERANCES.json", utterances)
    write_json(root / "KEYWORDS_EXTRA.json", keywords)
    write_json(root / "EVAL_SET.json", dict(synthetic=True, in_domain=cases, garbage=GARBAGE))
    return index


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="fixtures/pool")
    args = parser.parse_args()
    generate(args.out)
    print("Synthetic fixtures written.")
