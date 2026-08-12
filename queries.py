"""
All Cypher queries used by the app, kept in one place so they're easy to
review and explain. Every query is parameterised - no string concatenation.
"""
from db import run_query


def list_people():
    return run_query("MATCH (p:Person) RETURN p.id AS id, p.name AS name ORDER BY p.name")


def list_skills():
    return run_query("MATCH (s:Skill) RETURN s.name AS name ORDER BY s.name")


def get_person_skills(person_id: str):
    return run_query(
        """
        MATCH (p:Person {id:$pid})-[r:HAS_SKILL]->(s:Skill)
        RETURN s.name AS skill, r.proficiency AS proficiency
        ORDER BY s.name
        """,
        {"pid": person_id},
    )


def recommended_jobs_for_person(person_id: str, limit: int = 10):
    """
    Direct matches: jobs where the person already has >=1 required skill.
    Ranked by number of overlapping skills. Trivial in Cypher, clunky in SQL
    (would need a self-join through a bridge table + GROUP BY + HAVING).
    """
    return run_query(
        """
        MATCH (p:Person {id:$pid})-[:HAS_SKILL]->(s:Skill)<-[:REQUIRES_SKILL]-(j:Job)-[:POSTED_BY]->(c:Company)
        WITH j, c, count(DISTINCT s) AS matchedSkills, collect(DISTINCT s.name) AS matchedSkillNames
        RETURN j.id AS job_id, j.title AS title, j.seniority AS seniority, j.location AS location,
               c.name AS company, matchedSkills, matchedSkillNames
        ORDER BY matchedSkills DESC
        LIMIT $limit
        """,
        {"pid": person_id, "limit": limit},
    )


"""
All Cypher queries used by the app, kept in one place so they're easy to
review and explain. Every query is parameterised - no string concatenation.
"""
from db import run_query


def list_people():
    return run_query("MATCH (p:Person) RETURN p.id AS id, p.name AS name ORDER BY p.name")


def list_skills():
    return run_query("MATCH (s:Skill) RETURN s.name AS name ORDER BY s.name")


def get_person_skills(person_id: str):
    return run_query(
        """
        MATCH (p:Person {id:$pid})-[r:HAS_SKILL]->(s:Skill)
        RETURN s.name AS skill, r.proficiency AS proficiency
        ORDER BY s.name
        """,
        {"pid": person_id},
    )


def recommended_jobs_for_person(person_id: str, limit: int = 10):
    """
    Direct matches: jobs where the person already has >=1 required skill.
    Ranked by number of overlapping skills. Trivial in Cypher, clunky in SQL
    (would need a self-join through a bridge table + GROUP BY + HAVING).
    """
    return run_query(
        """
        MATCH (p:Person {id:$pid})-[:HAS_SKILL]->(s:Skill)<-[:REQUIRES_SKILL]-(j:Job)-[:POSTED_BY]->(c:Company)
        WITH j, c, count(DISTINCT s) AS matchedSkills, collect(DISTINCT s.name) AS matchedSkillNames
        RETURN j.id AS job_id, j.title AS title, j.seniority AS seniority, j.location AS location,
               c.name AS company, matchedSkills, matchedSkillNames
        ORDER BY matchedSkills DESC
        LIMIT $limit
        """,
        {"pid": person_id, "limit": limit},
    )


def skill_gap_jobs(person_id: str, limit: int = 10):
    """
    MULTI-HOP (2+ hops): jobs the person doesn't fully qualify for yet, but is
    reachable from via 1-2 hops through RELATED_TO skill chains. Surfaces the
    'bridge skills' needed. This kind of variable-length adjacency traversal
    is the textbook case where a relational schema gets painful fast
    (recursive CTEs, multiple self-joins) but Cypher handles natively.

    Note: the "person doesn't already have this bridge skill" filter is done
    in Python rather than Cypher (WHERE NOT / OPTIONAL MATCH re-referencing a
    bound variable), because CognoDB's current engine has a known issue where
    OPTIONAL MATCH on an already-bound node variable can corrupt the result
    binding instead of just checking existence.
    """
    known_skills = {
        row["skill"] for row in get_person_skills(person_id)
    }

    candidates = run_query(
        """
        MATCH (p:Person {id:$pid})-[:HAS_SKILL]->(known:Skill)
        MATCH (known)-[:RELATED_TO*1..2]-(bridge:Skill)<-[:REQUIRES_SKILL]-(j:Job)-[:POSTED_BY]->(c:Company)
        RETURN DISTINCT j.id AS job_id, j.title AS title, c.name AS company, bridge.name AS bridge
        """,
        {"pid": person_id},
    )

    jobs = {}
    for row in candidates:
        if row["bridge"] in known_skills:
            continue  # person already has this skill, not a gap
        jid = row["job_id"]
        if jid not in jobs:
            jobs[jid] = {
                "job_id": jid, "title": row["title"], "company": row["company"],
                "bridgeSkills": set(),
            }
        jobs[jid]["bridgeSkills"].add(row["bridge"])

    results = [
        {**j, "bridgeSkills": sorted(j["bridgeSkills"]), "gapCount": len(j["bridgeSkills"])}
        for j in jobs.values()
    ]
    results.sort(key=lambda x: x["gapCount"])
    return results[:limit]


def courses_to_bridge_gap(person_id: str, job_id: str):
    """For a specific job, find courses that teach the skills the person is missing."""
    return run_query(
        """
        MATCH (j:Job {id:$jid})-[:REQUIRES_SKILL]->(missing:Skill)
        WHERE NOT (:Person {id:$pid})-[:HAS_SKILL]->(missing)
        MATCH (co:Course)-[:TEACHES]->(missing)
        RETURN DISTINCT co.name AS course, co.provider AS provider, missing.name AS skill
        """,
        {"pid": person_id, "jid": job_id},
    )


def skill_shortest_path(skill_a: str, skill_b: str):
    """
    Shortest path between two skills through the RELATED_TO graph.
    Classic graph-native operation with no clean relational equivalent.
    """
    return run_query(
        """
        MATCH path = shortestPath(
            (a:Skill {name:$a})-[:RELATED_TO*..6]-(b:Skill {name:$b})
        )
        RETURN [n IN nodes(path) | n.name] AS pathNodes, length(path) AS hops
        """,
        {"a": skill_a, "b": skill_b},
    )


def jobs_for_skill(skill_name: str):
    return run_query(
        """
        MATCH (j:Job)-[:REQUIRES_SKILL]->(s:Skill {name:$name})
        MATCH (j)-[:POSTED_BY]->(c:Company)
        RETURN j.title AS title, c.name AS company, j.seniority AS seniority, j.location AS location
        ORDER BY j.title
        """,
        {"name": skill_name},
    )


def related_skills(skill_name: str):
    return run_query(
        """
        MATCH (s:Skill {name:$name})-[:RELATED_TO]-(other:Skill)
        RETURN other.name AS skill, other.category AS category
        ORDER BY other.name
        """,
        {"name": skill_name},
    )


def graph_stats():
    return run_query(
        """
        RETURN
          count { (:Person) } AS people,
          count { (:Skill) } AS skills,
          count { (:Job) } AS jobs,
          count { (:Company) } AS companies,
          count { (:Course) } AS courses
        """
    )


def courses_to_bridge_gap(person_id: str, job_id: str):
    """For a specific job, find courses that teach the skills the person is missing."""
    return run_query(
        """
        MATCH (j:Job {id:$jid})-[:REQUIRES_SKILL]->(missing:Skill)
        WHERE NOT (:Person {id:$pid})-[:HAS_SKILL]->(missing)
        MATCH (co:Course)-[:TEACHES]->(missing)
        RETURN DISTINCT co.name AS course, co.provider AS provider, missing.name AS skill
        """,
        {"pid": person_id, "jid": job_id},
    )


def skill_shortest_path(skill_a: str, skill_b: str):
    """
    Shortest path between two skills through the RELATED_TO graph.
    Classic graph-native operation with no clean relational equivalent.
    """
    return run_query(
        """
        MATCH path = shortestPath(
            (a:Skill {name:$a})-[:RELATED_TO*..6]-(b:Skill {name:$b})
        )
        RETURN [n IN nodes(path) | n.name] AS pathNodes, length(path) AS hops
        """,
        {"a": skill_a, "b": skill_b},
    )


def jobs_for_skill(skill_name: str):
    return run_query(
        """
        MATCH (j:Job)-[:REQUIRES_SKILL]->(s:Skill {name:$name})
        MATCH (j)-[:POSTED_BY]->(c:Company)
        RETURN j.title AS title, c.name AS company, j.seniority AS seniority, j.location AS location
        ORDER BY j.title
        """,
        {"name": skill_name},
    )


def related_skills(skill_name: str):
    return run_query(
        """
        MATCH (s:Skill {name:$name})-[:RELATED_TO]-(other:Skill)
        RETURN other.name AS skill, other.category AS category
        ORDER BY other.name
        """,
        {"name": skill_name},
    )


def graph_stats():
    return run_query(
        """
        RETURN
          count { (:Person) } AS people,
          count { (:Skill) } AS skills,
          count { (:Job) } AS jobs,
          count { (:Company) } AS companies,
          count { (:Course) } AS courses
        """
    )
