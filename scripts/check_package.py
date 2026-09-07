#!/usr/bin/env python3
"""Check release hashes, constrained skill metadata, links, and case contracts."""

import ast
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT))
import install  # noqa: E402


def require(condition, message):
    if not condition:
        raise install.BundleError(message)


def check():
    manifest, packages = install.load_packages(ROOT)
    for name in packages:
        path = ROOT / "skills" / name / "SKILL.md"
        text = path.read_text(encoding="utf-8")
        match = re.match(r"\A---\n(.*?)\n---\n", text, re.S)
        require(match, "Missing frontmatter: " + name)
        fields = {}
        for line in match.group(1).splitlines():
            key, separator, value = line.partition(":")
            require(separator and key not in fields, "Unsupported metadata: " + name)
            fields[key] = value.strip()
        require(set(fields) == {"name", "description"}, "Unexpected metadata keys: " + name)
        require(fields["name"] == name, "Skill name mismatch: " + name)
        require(0 < len(fields["description"]) <= 1024, "Invalid description length: " + name)
        require(len(text.splitlines()) < 500, "Skill body needs splitting: " + name)
        if name != install.NAME:
            for relative in ("reference/principles.md", "reference/kb/INDEX.md"):
                require((path.parent / relative).is_file() and relative in text, "Missing reference route: " + name)
            for topic in (path.parent / "reference/kb").glob("*.md"):
                if topic.name == "INDEX.md":
                    continue
                content = topic.read_text(encoding="utf-8")
                for key in ("title:", "source:", "last_fetched:", "skills:", "## 리뷰 훅"):
                    require(key in content, "Missing KB metadata/hook in " + str(topic))
                index = (topic.parent / "INDEX.md").read_text(encoding="utf-8")
                require(topic.name in index, "Unindexed topic: " + str(topic))
    for name in manifest["files"]:
        if not name.endswith(".md"):
            continue
        path = ROOT / name
        for raw in re.findall(r"\[[^\]]*\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
            link = raw.strip().strip("<>")
            parsed = urlsplit(link)
            if parsed.scheme or not parsed.path:
                continue
            target = (path.parent / unquote(parsed.path)).resolve()
            require(target.is_relative_to(ROOT) and target.is_file(), "Broken local link: " + name + " -> " + link)
            require(target.relative_to(ROOT).as_posix() in manifest["files"], "Link absent from export: " + link)
            if name.startswith("skills/"):
                source_skill = Path(name).parts[1]
                relative = target.relative_to(ROOT).parts
                allowed = install.dependency_order(manifest["skills"], [source_skill])
                require(len(relative) >= 3 and relative[0] == "skills" and relative[1] in allowed, "Undeclared installed link dependency: " + name + " -> " + link)
    cases = install.read_json(ROOT / "evals/skill-cases.json")
    require(cases.get("schema") == 1 and isinstance(cases.get("cases"), list) and cases["cases"], "Invalid case catalog")
    identifiers = set()
    for case in cases["cases"]:
        require(set(case) == {"id", "prompt", "expected_skills", "assertions", "forbidden"}, "Invalid case fields")
        for key in ("id", "prompt"):
            require(isinstance(case[key], str) and case[key].strip(), "Empty case field: " + key)
        require(case["id"] not in identifiers, "Duplicate case: " + case["id"])
        identifiers.add(case["id"])
        for key in ("expected_skills", "assertions", "forbidden"):
            require(isinstance(case[key], list) and case[key] and all(isinstance(v, str) and v.strip() for v in case[key]), "Invalid case expectations: " + case["id"])
        require(set(case["expected_skills"]).issubset(packages), "Unknown skill in case: " + case["id"])
    for directory in (ROOT / "scripts", ROOT / "tests"):
        for path in directory.glob("*.py"):
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    ast.parse((ROOT / "install.py").read_text(encoding="utf-8"))
    print("Validated {} skills, release links/dependencies, {} case contracts, and Python syntax.".format(len(packages), len(identifiers)))
    print("Case contracts are static checks, not executed agent trials.")


def main():
    try:
        check()
    except (install.BundleError, OSError, SyntaxError, ValueError) as exc:
        print("Error: " + str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
