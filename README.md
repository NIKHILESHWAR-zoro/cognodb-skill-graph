# SkillGraph — Graph-Powered Job Matching

A small application that models **skills, jobs, companies, and courses** as a
graph and answers questions relational databases handle awkwardly: *"Which
jobs am I close to qualifying for, and what do I need to learn to bridge the
gap?"*

## Why a graph database?

Job matching is fundamentally a connections problem, not a rows-and-columns
problem. The interesting question isn't "does this row's skill column equal
that row's requirement column" — it's "how far, through how many related
skills, am I from qualifying for this job?" That's a variable-length
traversal over a skill-adjacency graph. In a relational schema this needs a
recursive CTE and self-joins that get slower and uglier with every extra hop;
in Cypher it's a single `[:RELATED_TO*1..2]` pattern. Shortest-path between
two skills is the same story — trivial with `shortestPath()`, painful in SQL.
CognoDB (openCypher over Bolt) let us model this directly as nodes and
relationships instead of flattening it into join tables.

## Data model

```
(Person)-[:HAS_SKILL {proficiency}]->(Skill)
(Job)-[:REQUIRES_SKILL {importance}]->(Skill)
(Job)-[:POSTED_BY]->(Company)
(Skill)-[:RELATED_TO {weight}]-(Skill)
(Course)-[:TEACHES]->(Skill)
```

- **Person**: id, name, current_role, experience_years
- **Skill**: name (unique), category
- **Job**: id, title, seniority, location
- **Company**: id, name, industry
- **Course**: id, name, provider, duration_hours

<!-- TODO: paste a simple diagram/screenshot of the model here -->

## Main queries (see `queries.py`)

1. **`recommended_jobs_for_person`** — direct skill-overlap matching, ranked.
2. **`skill_gap_jobs`** — *multi-hop (2 hops)*: jobs reachable through
   `RELATED_TO` chains from skills the person already has, surfacing which
   "bridge skills" are missing.
3. **`courses_to_bridge_gap`** — for a specific job, find courses teaching
   the missing skills.
4. **`skill_shortest_path`** — shortest path between any two skills through
   the skill graph (SQL-awkward: recursive traversal).

All queries are parameterised through the official Neo4j driver — no string
concatenation.

## Setup

### 1. Create a CognoDB instance
1. Sign up at https://console.cognodb.com/signup (free, no credit card).
2. Create a free (c0) instance, pick a region.
3. Copy the `bolt+s://...` URI and the generated password for user `cognodb`
   — shown once.

### 2. Configure environment
```bash
cp .env.example .env
# fill in COGNODB_URI, COGNODB_USER=cognodb, COGNODB_PASSWORD
```

### 3. Install & seed
```bash
python -m venv venv && source venv/bin/activate   # or venv\Scripts\activate on Windows
pip install -r requirements.txt
python seed_data.py
```

### 4. Run
```bash
streamlit run app.py
```

## Deployment

Deployed on Streamlit Community Cloud: **<TODO: paste live demo link>**
(connect this GitHub repo, set the three env vars as secrets, deploy.)

## Screenshots

## Screenshots

### Person Explorer — job matches & skill-gap analysis
![Person Explorer](screenshots/screenshot1.png)

### Skill Explorer — jobs & related skills
![Skill Explorer](screenshots/screenshot2.png)

### Skill Path Finder — shortest path between skills
![Skill Path Finder](screenshots/screenshot3.png)

## Screen recording

<!-- TODO: add link to short screen recording -->

## Project structure

```
.
├── app.py           # Streamlit UI
├── db.py            # Neo4j driver wrapper, error handling
├── queries.py        # All Cypher queries, documented
├── seed_data.py      # Synthetic data generation & loading
├── requirements.txt
├── .env.example
└── README.md
```
