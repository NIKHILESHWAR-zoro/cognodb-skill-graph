from db import run_query

skills = run_query("MATCH (s:Skill) RETURN s.name AS name, s.category AS category ORDER BY s.category, s.name")
current_category = None
for s in skills:
    if s["category"] != current_category:
        current_category = s["category"]
        print(f"\n-- {current_category} --")
    print(f"  {s['name']}")