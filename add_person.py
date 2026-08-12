"""
Adds ONE new person to the graph without touching existing data.
Edit the values below, then run: python add_person.py
"""
from db import run_query

# ---- EDIT THESE VALUES ----
PERSON_ID = "person-nikhil"          # must be unique - no spaces
PERSON_NAME = "Nikhileshwar"
CURRENT_ROLE = "Student"             # e.g. "Student", "Junior Developer"
EXPERIENCE_YEARS = 0

# List the skills this person has, and how proficient they are.
# proficiency must be one of: "beginner", "intermediate", "advanced"
# Skill names must match existing skills exactly (see list below the script).
MY_SKILLS = [
    ("Python", "advanced"),
    ("Machine Learning", "intermediate"),
    ("SQL", "intermediate"),
    ("Git", "intermediate"),
]
# ----------------------------


def add_person():
    run_query(
        """
        MERGE (p:Person {id:$id})
        SET p.name=$name, p.current_role=$role, p.experience_years=$exp
        """,
        {"id": PERSON_ID, "name": PERSON_NAME, "role": CURRENT_ROLE, "exp": EXPERIENCE_YEARS},
    )
    print(f"Created/updated person: {PERSON_NAME}")

    for skill_name, proficiency in MY_SKILLS:
        result = run_query(
            """
            MATCH (s:Skill {name:$skill})
            RETURN s.name AS name
            """,
            {"skill": skill_name},
        )
        if not result:
            print(f"  WARNING: skill '{skill_name}' doesn't exist in the graph yet - skipped. "
                  f"Run 'python list_skills.py' to see valid skill names.")
            continue

        run_query(
            """
            MATCH (p:Person {id:$pid}), (s:Skill {name:$skill})
            MERGE (p)-[r:HAS_SKILL]->(s)
            SET r.proficiency = $prof
            """,
            {"pid": PERSON_ID, "skill": skill_name, "prof": proficiency},
        )
        print(f"  Added skill: {skill_name} ({proficiency})")

    print("Done.")


if __name__ == "__main__":
    add_person()