ALIASES = {
    "js": "javascript",
    "nodejs": "node.js",
    "node": "node.js",
    "reactjs": "react",
    "postgres": "postgresql",
    "ml": "machine learning",
    "py": "python",
}


def canon(name: str) -> str:
    key = name.strip().lower()
    return ALIASES.get(key, key)


def compute_match(resume_skills: list, required: list) -> dict:
    have = {canon(s) for s in resume_skills}
    total = 0.0
    got = 0.0
    matched = []
    missing = []

    for item in required:
        name = item.get("name", "")
        weight = float(item.get("importance", 3))
        total += weight
        if canon(name) in have:
            got += weight
            matched.append(name)
        else:
            missing.append({"name": name, "importance": weight})

    missing.sort(key=lambda x: -x["importance"])
    score = round(100 * got / total, 1) if total else 0.0

    return {
        "match_percentage": score,
        "matched_skills": matched,
        "missing_skills": missing,
    }