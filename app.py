import streamlit as st
from db import check_connection
import queries as q

st.set_page_config(page_title="SkillGraph — Job Matching", page_icon="🕸️", layout="wide")

st.title("🕸️ SkillGraph")
st.caption("A graph-powered skill → job matcher, backed by CognoDB")

# --- Connection / empty state -------------------------------------------
if not check_connection():
    st.error(
        "⚠️ Could not connect to CognoDB. Check that COGNODB_URI, COGNODB_USER "
        "and COGNODB_PASSWORD are set correctly and that your instance is running."
    )
    st.stop()

tab1, tab2, tab3 = st.tabs(["👤 Person Explorer", "🔍 Skill Explorer", "🧭 Skill Path Finder"])

# ============================== TAB 1 ====================================
with tab1:
    people = q.list_people()
    if not people:
        st.info("No people in the graph yet. Run `python seed_data.py` first.")
    else:
        names = {p["name"]: p["id"] for p in people}
        selected_name = st.selectbox("Choose a person", list(names.keys()))
        pid = names[selected_name]

        col1, col2 = st.columns([1, 2])

        with col1:
            st.subheader("Current skills")
            skills = q.get_person_skills(pid)
            if skills:
                for s in skills:
                    st.write(f"• **{s['skill']}** ({s['proficiency']})")
            else:
                st.write("_No skills recorded._")

        with col2:
            st.subheader("✅ Jobs you qualify for")
            with st.spinner("Matching jobs..."):
                matches = q.recommended_jobs_for_person(pid)
            if matches:
                for m in matches:
                    with st.expander(f"{m['title']} @ {m['company']} — {m['matchedSkills']} skill(s) match"):
                        st.write(f"📍 {m['location']} · {m['seniority']}")
                        st.write("Matched skills: " + ", ".join(m["matchedSkillNames"]))
            else:
                st.write("_No direct matches yet — check the gap analysis below._")

        st.divider()
        st.subheader("🌉 Jobs within reach (skill-gap analysis, multi-hop)")
        st.caption(
            "Jobs reachable from your current skills through 1–2 hops of related "
            "skills — even if you don't have the exact skill yet."
        )
        with st.spinner("Traversing skill graph..."):
            gap_jobs = q.skill_gap_jobs(pid)
        if gap_jobs:
            for g in gap_jobs:
                with st.expander(f"{g['title']} @ {g['company']} — {g['gapCount']} skill(s) to bridge"):
                    st.write("Bridge skills needed: " + ", ".join(g["bridgeSkills"]))
                    courses = q.courses_to_bridge_gap(pid, g["job_id"])
                    if courses:
                        st.write("**Courses that could help:**")
                        for c in courses:
                            st.write(f"- {c['course']} ({c['provider']}) → teaches *{c['skill']}*")
        else:
            st.write("_No reachable jobs found within 2 hops._")

# ============================== TAB 2 ====================================
with tab2:
    skills = [s["name"] for s in q.list_skills()]
    if not skills:
        st.info("No skills in the graph yet. Run `python seed_data.py` first.")
    else:
        chosen = st.selectbox("Choose a skill", skills)

        col1, col2 = st.columns(2)
        with col1:
            st.subheader(f"Jobs requiring {chosen}")
            jobs = q.jobs_for_skill(chosen)
            if jobs:
                for j in jobs:
                    st.write(f"• **{j['title']}** @ {j['company']} — {j['location']}")
            else:
                st.write("_No jobs require this skill directly._")

        with col2:
            st.subheader(f"Skills related to {chosen}")
            related = q.related_skills(chosen)
            if related:
                for r in related:
                    st.write(f"• {r['skill']} _(​{r['category']})_")
            else:
                st.write("_No related skills recorded._")

# ============================== TAB 3 ====================================
with tab3:
    st.subheader("Shortest path between two skills")
    st.caption("Uses Cypher's shortestPath() over the RELATED_TO graph — no clean SQL equivalent.")
    skills = [s["name"] for s in q.list_skills()]
    if len(skills) < 2:
        st.info("Not enough skills seeded yet.")
    else:
        c1, c2 = st.columns(2)
        with c1:
            skill_a = st.selectbox("From skill", skills, index=0, key="a")
        with c2:
            skill_b = st.selectbox("To skill", skills, index=1, key="b")

        if st.button("Find path"):
            with st.spinner("Searching graph..."):
                result = q.skill_shortest_path(skill_a, skill_b)
            if result and result[0]["pathNodes"]:
                path = result[0]["pathNodes"]
                st.success(f"Found a path with {result[0]['hops']} hop(s):")
                st.write(" → ".join(path))
            else:
                st.warning("No path found between these skills.")

st.divider()
stats = q.graph_stats()[0] if q.graph_stats() else {}
st.caption(
    f"Graph size: {stats.get('people', 0)} people · {stats.get('skills', 0)} skills · "
    f"{stats.get('jobs', 0)} jobs · {stats.get('companies', 0)} companies · "
    f"{stats.get('courses', 0)} courses"
)
