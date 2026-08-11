"""
Seeds CognoDB with a realistic Skill/Job/Company/Person/Course graph.
Run: python seed_data.py
"""
import random
from faker import Faker
from db import run_query

fake = Faker()
random.seed(42)

# --- Reference data -----------------------------------------------------

SKILL_CATEGORIES = {
    "Programming": ["Python", "JavaScript", "C++", "Java", "Go", "SQL", "TypeScript"],
    "Data": ["Pandas", "Data Analysis", "Machine Learning", "Deep Learning",
             "TensorFlow", "PyTorch", "Data Visualization", "Statistics"],
    "Backend": ["FastAPI", "Django", "Flask", "Node.js", "REST APIs", "Microservices"],
    "DevOps": ["Docker", "Kubernetes", "CI/CD", "AWS", "Linux", "Git"],
    "Frontend": ["React", "HTML/CSS", "Streamlit", "UI/UX Design"],
    "Databases": ["PostgreSQL", "MongoDB", "Neo4j/Cypher", "Redis"],
}

# Manually curated adjacency: which skills are meaningfully "related"
# (used to build RELATED_TO edges — this is the backbone of the multi-hop queries)
RELATED_PAIRS = [
    ("Python", "Pandas"), ("Python", "FastAPI"), ("Python", "Django"),
    ("Python", "Flask"), ("Python", "Machine Learning"), ("Python", "TensorFlow"),
    ("Pandas", "Data Analysis"), ("Data Analysis", "Statistics"),
    ("Machine Learning", "Deep Learning"), ("Deep Learning", "TensorFlow"),
    ("Deep Learning", "PyTorch"), ("Machine Learning", "Statistics"),
    ("Data Analysis", "Data Visualization"), ("SQL", "PostgreSQL"),
    ("SQL", "Data Analysis"), ("JavaScript", "React"), ("JavaScript", "Node.js"),
    ("JavaScript", "TypeScript"), ("React", "UI/UX Design"), ("FastAPI", "REST APIs"),
    ("Django", "REST APIs"), ("Flask", "REST APIs"), ("REST APIs", "Microservices"),
    ("Microservices", "Docker"), ("Docker", "Kubernetes"), ("Docker", "CI/CD"),
    ("Kubernetes", "AWS"), ("CI/CD", "Git"), ("Linux", "AWS"), ("AWS", "Microservices"),
    ("Neo4j/Cypher", "SQL"), ("PostgreSQL", "MongoDB"), ("MongoDB", "Redis"),
    ("Streamlit", "Python"), ("Streamlit", "Data Visualization"),
    ("C++", "Java"), ("Java", "Microservices"), ("Go", "Microservices"),
]

JOB_TITLES = [
    ("Backend Engineer", ["Python", "FastAPI", "PostgreSQL", "REST APIs"]),
    ("Data Analyst", ["SQL", "Pandas", "Data Visualization", "Statistics"]),
    ("ML Engineer", ["Python", "Machine Learning", "TensorFlow", "Statistics"]),
    ("Frontend Engineer", ["JavaScript", "React", "TypeScript", "UI/UX Design"]),
    ("DevOps Engineer", ["Docker", "Kubernetes", "AWS", "CI/CD"]),
    ("Full Stack Developer", ["JavaScript", "Node.js", "React", "PostgreSQL"]),
    ("Data Engineer", ["Python", "SQL", "PostgreSQL", "AWS"]),
    ("Site Reliability Engineer", ["Linux", "AWS", "Docker", "CI/CD"]),
    ("Data Scientist", ["Python", "Machine Learning", "Deep Learning", "Pandas"]),
    ("Graph/Database Engineer", ["Neo4j/Cypher", "SQL", "MongoDB", "Redis"]),
]

COURSE_CATALOG = [
    ("Complete Python Bootcamp", ["Python"]),
    ("FastAPI for Production APIs", ["FastAPI", "REST APIs"]),
    ("Machine Learning A-Z", ["Machine Learning", "Statistics"]),
    ("Deep Learning Specialization", ["Deep Learning", "TensorFlow", "PyTorch"]),
    ("Docker & Kubernetes Mastery", ["Docker", "Kubernetes"]),
    ("SQL for Data Analysis", ["SQL", "Data Analysis"]),
    ("React - The Complete Guide", ["React", "JavaScript"]),
    ("AWS Cloud Practitioner", ["AWS", "Linux"]),
    ("Graph Databases with Neo4j", ["Neo4j/Cypher"]),
    ("Data Visualization with Python", ["Data Visualization", "Pandas"]),
]


def clear_db():
    run_query("MATCH (n) DETACH DELETE n")


def create_constraints():
    run_query("CREATE CONSTRAINT skill_name IF NOT EXISTS FOR (s:Skill) REQUIRE s.name IS UNIQUE")
    run_query("CREATE CONSTRAINT company_id IF NOT EXISTS FOR (c:Company) REQUIRE c.id IS UNIQUE")
    run_query("CREATE CONSTRAINT job_id IF NOT EXISTS FOR (j:Job) REQUIRE j.id IS UNIQUE")
    run_query("CREATE CONSTRAINT person_id IF NOT EXISTS FOR (p:Person) REQUIRE p.id IS UNIQUE")
    run_query("CREATE CONSTRAINT course_id IF NOT EXISTS FOR (co:Course) REQUIRE co.id IS UNIQUE")


def seed_skills():
    for category, skills in SKILL_CATEGORIES.items():
        for name in skills:
            run_query(
                "MERGE (s:Skill {name: $name}) SET s.category = $category",
                {"name": name, "category": category},
            )
    for a, b in RELATED_PAIRS:
        run_query(
            """
            MATCH (s1:Skill {name:$a}), (s2:Skill {name:$b})
            MERGE (s1)-[:RELATED_TO {weight: 1}]-(s2)
            """,
            {"a": a, "b": b},
        )
    print(f"Seeded {sum(len(v) for v in SKILL_CATEGORIES.values())} skills + {len(RELATED_PAIRS)} relations")


def seed_companies(n=20):
    ids = []
    for i in range(n):
        cid = f"company-{i}"
        run_query(
            "MERGE (c:Company {id:$id}) SET c.name=$name, c.industry=$industry",
            {"id": cid, "name": fake.company(), "industry": random.choice(
                ["Software", "Fintech", "E-commerce", "Healthcare", "AI/ML", "Gaming"]
            )},
        )
        ids.append(cid)
    print(f"Seeded {n} companies")
    return ids


def seed_jobs(company_ids, n=60):
    job_ids = []
    for i in range(n):
        jid = f"job-{i}"
        title, req_skills = random.choice(JOB_TITLES)
        company_id = random.choice(company_ids)
        seniority = random.choice(["Junior", "Mid", "Senior"])
        run_query(
            """
            MATCH (c:Company {id:$company_id})
            MERGE (j:Job {id:$id})
            SET j.title=$title, j.seniority=$seniority, j.location=$location
            MERGE (j)-[:POSTED_BY]->(c)
            """,
            {
                "id": jid, "title": f"{seniority} {title}", "seniority": seniority,
                "location": fake.city(), "company_id": company_id,
            },
        )
        for skill in req_skills:
            run_query(
                """
                MATCH (j:Job {id:$jid}), (s:Skill {name:$skill})
                MERGE (j)-[:REQUIRES_SKILL {importance: $importance}]->(s)
                """,
                {"jid": jid, "skill": skill, "importance": random.choice(["core", "nice-to-have"])},
            )
        job_ids.append(jid)
    print(f"Seeded {n} jobs")
    return job_ids


def seed_courses():
    for i, (name, skills) in enumerate(COURSE_CATALOG):
        cid = f"course-{i}"
        run_query(
            "MERGE (co:Course {id:$id}) SET co.name=$name, co.provider=$provider, co.duration_hours=$hours",
            {"id": cid, "name": name, "provider": random.choice(
                ["Coursera", "Udemy", "freeCodeCamp", "YouTube", "Coding Ninjas"]
            ), "hours": random.choice([10, 20, 30, 40])},
        )
        for skill in skills:
            run_query(
                """
                MATCH (co:Course {id:$cid}), (s:Skill {name:$skill})
                MERGE (co)-[:TEACHES]->(s)
                """,
                {"cid": cid, "skill": skill},
            )
    print(f"Seeded {len(COURSE_CATALOG)} courses")


def seed_people(n=25):
    all_skills = [s for skills in SKILL_CATEGORIES.values() for s in skills]
    for i in range(n):
        pid = f"person-{i}"
        run_query(
            "MERGE (p:Person {id:$id}) SET p.name=$name, p.current_role=$role, p.experience_years=$exp",
            {
                "id": pid, "name": fake.name(),
                "role": random.choice(["Student", "Junior Developer", "Analyst", "Career Switcher"]),
                "exp": random.randint(0, 5),
            },
        )
        my_skills = random.sample(all_skills, k=random.randint(3, 7))
        for skill in my_skills:
            run_query(
                """
                MATCH (p:Person {id:$pid}), (s:Skill {name:$skill})
                MERGE (p)-[:HAS_SKILL {proficiency: $prof}]->(s)
                """,
                {"pid": pid, "skill": skill, "prof": random.choice(["beginner", "intermediate", "advanced"])},
            )
    print(f"Seeded {n} people")


if __name__ == "__main__":
    print("Clearing existing data...")
    clear_db()
    print("Creating constraints...")
    create_constraints()
    print("Seeding graph...")
    seed_skills()
    company_ids = seed_companies()
    seed_jobs(company_ids)
    seed_courses()
    seed_people()
    print("Done. Graph seeded successfully.")
