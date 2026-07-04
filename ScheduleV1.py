#!/usr/bin/env python3
"""
SAS Kendall AA Planner
Builds a personalized semester schedule based on your major, completed courses, AP credits, and available study time.
"""

import math
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

import pulp
import streamlit as st


@dataclass
class Course:
    name: str
    credits: float = 3.0
    workload: float = 6.0
    difficulty: int = 5
    prereqs: List[str] = field(default_factory=list)
    fulfills: List[str] = field(default_factory=list)
    priority: int = 5
    class_count: int = 1
    is_high_school_ap: bool = False
    allowed_terms: Optional[List[str]] = None


# ---------- Course catalog ----------
courses: Dict[str, Course] = {
    # English
    "ENC1101": Course("ENC 1101 - English Composition 1", workload=1.5, difficulty=4, fulfills=["English"]),
    "ENC1102": Course("ENC 1102 - English Composition 2", workload=1.5, difficulty=5, prereqs=["ENC1101"], fulfills=["English"]),
    "ENC2300": Course("ENC 2300 - Advanced Composition and Communication", workload=2, fulfills=["Oral Communication"]),
    "SPC1017": Course("SPC 1017 - Introduction to Communication", workload=1.5, fulfills=["Oral Communication"]),
    "SPC2608": Course("SPC 2608 - Introduction to Public Speaking", workload=2, fulfills=["Oral Communication"]),
    "ENG2012": Course("ENG 2012 - Literary Theory", workload=1.5),
    "CRW2001": Course("CRW 2001 - Creative Writing 1", workload=1.5),

    # Humanities
    "ARH1000": Course("ARH 1000 - Art Appreciation", workload=1, fulfills=["Humanities"]),
    "ARH2051": Course("ARH 2051 - Art History 2", workload=1, fulfills=["Humanities"]),
    "HUM1020": Course("HUM 1020 - Humanities", workload=1.5, fulfills=["Humanities"]),
    "LIT2000": Course("LIT 2000 - Introduction to Literature", workload=2, fulfills=["Humanities"]),
    "MUL1010": Course("MUL 1010 - Music Appreciation", workload=1, fulfills=["Humanities"]),
    "PHI2010": Course("PHI 2010 - Introduction to Philosophy", workload=2, fulfills=["Humanities"]),
    "PHI1100": Course("PHI 1100 - Introduction to Logic", workload=1.5, fulfills=["Humanities"]),
    "THE2000": Course("THE 2000 - Theatre Appreciation", workload=1.5, fulfills=["Humanities"]),

    # Social sciences
    "AMH2010": Course("AMH 2010 - History of the US to 1877", workload=1.5, fulfills=["Social Sciences", "State Core Social Science", "Civic Literacy"]),
    "AMH2020": Course("AMH 2020 - History of the US Since 1877", workload=1.5, fulfills=["Social Sciences", "State Core Social Science", "Civic Literacy"]),
    "POS2041": Course("POS 2041 - American Federal Government", credits=3, workload=1.5, fulfills=["Social Sciences", "State Core Social Science", "Civic Literacy"]),
    "PSY2012": Course("PSY 2012 - Introduction to Psychology", workload=1.5, fulfills=["Social Sciences", "State Core Social Science"]),
    "ANT2000": Course("ANT 2000 - Introduction to Anthropology", workload=1.5, fulfills=["Social Sciences", "State Core Social Science"]),
    "ECO2013": Course("ECO 2013 - Principles of Economics (Macro)", credits=3, workload=2, fulfills=["Social Sciences", "State Core Social Science"]),
    "ECO2023": Course("ECO 2023 - Principles of Economics (Micro)", workload=2, fulfills=["Social Sciences"]),
    "INR2002": Course("INR 2002 - International Relations", workload=2, fulfills=["Social Sciences"]),
    "INR2440": Course("INR 2440 - International Law and Organization", workload=2, prereqs=["INR2002"]),
    "DEP2000": Course("DEP 2000 - Human Growth and Development", workload=1.5, fulfills=["Social Sciences"]),
    "DEP2100": Course("DEP 2100 - Child Growth and Development", workload=1.5, fulfills=["Social Sciences"]),
    "INP2390": Course("INP 2390 - Psychology of Work", workload=1.5, fulfills=["Social Sciences"]),
    "SOP2772": Course("SOP 2772 - Human Sexuality", workload=1.5, fulfills=["Social Sciences"]),
    "ISS1301": Course("ISS 1301 - Introduction to Social Research", workload=1.5, fulfills=["Social Sciences"]),

    # Computer competency & programming
    "CGS1060C": Course("CGS 1060C - Introduction to Computer Technology and Applications", credits=4, workload=1.5, fulfills=["Computer Competency"]),
    "COP1047C": Course("COP 1047C - Introduction to Python Programming", workload=2),
    "COP2270": Course("COP 2270 - C Programming for Engineers", workload=2.5, difficulty=7),
    "COP2800": Course("COP 2800 - Java Programming", workload=2.5, difficulty=7),
    "COP2805C": Course("COP 2805C - Advanced Java Programming", workload=3, difficulty=7, prereqs=["COP2800"]),

    # Business
    "ACG2001": Course("ACG 2001 + L - Principles of Accounting 1 + Lab", credits=4, workload=2.5),
    "ACG2011": Course("ACG 2011 + L - Principles of Accounting 2 + Lab", credits=4, workload=2.5, prereqs=["ACG2001"]),
    "ACG2021": Course("ACG 2021 + L - Financial Accounting + Lab", credits=4, workload=2.5),
    "ACG2071": Course("ACG 2071 + L - Managerial Accounting + Lab", credits=4, workload=2.5, prereqs=["ACG2011"]),
    "BUL2241": Course("BUL 2241 - Business Law I", workload=1.5),
    "GEB1011": Course("GEB 1011 - Principles of Business", workload=1.5),

    # Math
    "MAC1105": Course("MAC 1105 - College Algebra", workload=1.5, fulfills=["Mathematics", "State Core Math"]),
    "MAC1106": Course("MAC 1106 - Integrated Math", workload=2, prereqs=["MAC1105"], fulfills=["Mathematics"]),
    "MAC1114": Course("MAC 1114 - Trigonometry", workload=2, prereqs=["MAC1105"], fulfills=["Mathematics"]),
    "MAC1140": Course("MAC 1140 - Precalculus Algebra", workload=2.5, fulfills=["Mathematics"]),
    "MAC1147": Course("MAC 1147 - Precalculus Algebra and Trigonometry", credits=5, workload=3, fulfills=["Mathematics"]),
    "MAC2233": Course("MAC 2233 - Business Calculus", workload=2.5, fulfills=["Mathematics"]),
    "MAC2311": Course("MAC 2311 - Calculus and Analytical Geometry 1", credits=4, workload=3, prereqs=["MAC1147"], fulfills=["Mathematics", "State Core Math"]),
    "MAC2312": Course("MAC 2312 - Calculus and Analytical Geometry 2", credits=4, workload=3, prereqs=["MAC2311"], fulfills=["Mathematics"]),
    "MAC2313": Course("MAC 2313 - Calculus and Analytical Geometry 3", credits=4, workload=2.5, prereqs=["MAC2312"]),
    "MAP2302": Course("MAP 2302 - Introduction to Differential Equations", workload=2, prereqs=["MAC2312"]),
    "MAS2103": Course("MAS 2103 - Elementary Linear Algebra", workload=2, prereqs=["MAC2311"]),
    "MAD2104": Course("MAD 2104 - Discrete Mathematics", workload=2, prereqs=["MAC2311"]),
    "STA2023": Course("STA 2023 - Statistical Methods", workload=1, fulfills=["Mathematics", "State Core Math"]),
    "MGF1130": Course("MGF 1130 - Mathematical Thinking", workload=1.5, fulfills=["Mathematics", "State Core Math"]),

    # Natural sciences
    "AST1002": Course("AST 1002 - Descriptive Astronomy", workload=1.5, fulfills=["Natural Sciences", "State Core Natural Science"]),
    "BSC1005": Course("BSC 1005 - General Education Biology", workload=1.5, fulfills=["Natural Sciences", "State Core Natural Science"]),
    "BSC2010": Course("BSC 2010 + L - Principles of Biology 1 + Lab", credits=4, workload=2.5, fulfills=["Natural Sciences", "State Core Natural Science"]),
    "BSC2011": Course("BSC 2011 + L - Principles of Biology 2 + Lab", credits=4, workload=2.5, prereqs=["BSC2010"], fulfills=["Natural Sciences"]),
    "BSC2085": Course("BSC 2085 - Human Anatomy and Physiology 1", workload=2, fulfills=["Natural Sciences"]),
    "BSC2086": Course("BSC 2086 - Human Anatomy and Physiology 2", workload=2, prereqs=["BSC2085"], fulfills=["Natural Sciences"]),
    "CHM1025": Course("CHM 1025 - Descriptive Chemistry", workload=1.5, fulfills=["Natural Sciences"]),
    "CHM1033": Course("CHM 1033 - Chemistry for Health Sciences", workload=2, fulfills=["Natural Sciences"]),
    "CHM1045": Course("CHM 1045 + L - General Chemistry and Qualitative Analysis 1 + Lab", credits=4, workload=2.5, fulfills=["Natural Sciences", "State Core Natural Science"]),
    "CHM1046": Course("CHM 1046 + L - General Chemistry and Qualitative Analysis 2 + Lab", credits=4, workload=2.5, prereqs=["CHM1045"], fulfills=["Natural Sciences"]),
    "CHM2210": Course("CHM 2210 - Organic Chemistry 1", workload=2.5, prereqs=["CHM1046"], fulfills=["Natural Sciences"]),
    "CHM2211": Course("CHM 2211 - Organic Chemistry 2", workload=2.5, prereqs=["CHM2210"], fulfills=["Natural Sciences"]),
    "ESC1000": Course("ESC 1000 - General Education Earth Science", workload=1.5, fulfills=["Natural Sciences", "State Core Natural Science"]),
    "HUN1201": Course("HUN 1201 - Human Nutrition", workload=1.5, fulfills=["Natural Sciences"]),
    "MCB2010": Course("MCB 2010 - Microbiology", workload=2, prereqs=["BSC2010"], fulfills=["Natural Sciences"]),
    "PHY2048": Course("PHY 2048 + L - Physics with Calculus 1 + Lab", credits=4, workload=3, prereqs=["MAC2311"], fulfills=["Natural Sciences", "State Core Natural Science"]),
    "PHY2049": Course("PHY 2049 + L - Physics with Calculus 2 + Lab", credits=4, workload=3, prereqs=["PHY2048"], fulfills=["Natural Sciences"]),
    "PHY2053": Course("PHY 2053 - General Physics without Calculus 1", workload=2, prereqs=["MAC1105"], fulfills=["Natural Sciences", "State Core Natural Science"]),
    "PHY2054": Course("PHY 2054 - General Physics without Calculus 2", workload=2, prereqs=["PHY2053"], fulfills=["Natural Sciences"]),

    # Engineering
    "EGN1008C": Course("EGN 1008C - Introduction to Engineering", workload=1.5),
    "EGN2312": Course("EGN 2312 - Engineering Analysis", workload=2, prereqs=["MAC2311"]),
}

# Prerequisite overrides from MDC's official list
PDF_PREREQ_RULES = {
    "MAC1106": ["MAC1105"],
    "MAC1114": ["MAC1105"],
    "MAC2311": ["MAC1147"],
    "MAC2312": ["MAC2311"],
    "MAC2313": ["MAC2312"],
    "MAP2302": ["MAC2312"],
    "MAS2103": ["MAC2311"],
    "CHM1046": ["CHM1045"],
    "PHY2048": ["MAC2311"],
    "PHY2049": ["PHY2048"],
}
for code, prereqs in PDF_PREREQ_RULES.items():
    courses[code].prereqs = prereqs


# ---------- Workload calibration ----------
HARD_WORKLOAD_COURSES = {
    "MAC2312", "MAC2313", "MAP2302", "PHY2048", "PHY2049",
    "CHM1046", "CHM2210", "CHM2211", "COP2805C",
}
MEDIUM_HARD_WORKLOAD_COURSES = {
    "MAC1147", "MAC2311", "MAS2103", "MAD2104", "CHM1045",
    "BSC2010", "BSC2011", "MCB2010", "COP2270", "COP2800",
    "ACG2001", "ACG2011", "ACG2021", "ACG2071",
}
MODERATE_WORKLOAD_PREFIXES = ("MAC", "STA", "BSC", "CHM", "PHY", "COP", "ACG", "ECO")


def recalibrate_course_workloads():
    """Scale workloads so that harder courses carry more weight."""
    for code, course in courses.items():
        if course.workload <= 0:
            continue
        base = course.workload * 1.5
        if code in HARD_WORKLOAD_COURSES:
            base *= 1.5
        elif code in MEDIUM_HARD_WORKLOAD_COURSES:
            base *= 1.2
        course.workload = min(round(base, 1), 8.0)


recalibrate_course_workloads()


# ---------- Requirement definitions ----------
GEN_EDS = {
    "English": {"courses": ["ENC1101", "ENC1102"], "allowed": {0, 3, 6}},
    "Oral Communication": {"courses": ["SPC1017", "SPC2608"], "yes_no": True},
    "Mathematics": {"courses": ["STA2023", "MGF1130", "MAC2233"], "allowed": {0, 3, 6}},
    "Humanities": {"courses": ["ARH1000", "HUM1020", "LIT2000", "MUL1010", "PHI2010", "THE2000"], "allowed": {0, 3, 6}},
    "Social Sciences": {"courses": ["PSY2012", "ANT2000", "ECO2023"], "allowed": {0, 3, 6}},
    "Natural Sciences": {"courses": ["AST1002", "BSC1005", "BSC2010", "BSC2011", "BSC2085", "CHM1025", "CHM1045", "CHM1046", "ESC1000", "PHY2048", "PHY2049", "PHY2053", "PHY2054"], "allowed": {0, 3, 4, 6, 8}},
    "Computer Competency": {"courses": ["CGS1060C"], "yes_no": True},
}

MAJOR_REQS = {
    "engineering": {"groups": [["MAC2312"], ["MAC2313"], ["MAP2302"], ["CHM1045"], ["PHY2048"], ["PHY2049"]], "additional": [["EGN1008C"], ["COP2270"], ["STA2023"]]},
    "nursing": {"groups": [["BSC2085"], ["BSC2086"], ["MCB2010"], ["CHM1033"], ["HUN1201"], ["DEP2000"], ["PSY2012"], ["STA2023"]], "additional": []},
    "chemistry": {"groups": [["MAC2312"], ["CHM1045"], ["CHM1046"], ["CHM2210"], ["CHM2211"], ["PHY2048"], ["PHY2049"]], "additional": [["MAC2313"], ["MAP2302"], ["COP2270"]]},
    "biology": {"groups": [["MAC2312"], ["BSC2010"], ["BSC2011"], ["CHM1045"], ["CHM1046"], ["CHM2210"], ["CHM2211"], ["PHY2048"], ["PHY2049"]], "additional": []},
    "physics": {"groups": [["MAC2312"], ["MAC2313"], ["PHY2048"], ["PHY2054"]], "additional": [["CHM1045"], ["CHM1046"], ["MAP2302"]]},
    "business administration": {"groups": [["STA2023"], ["ECO2023"], ["ACG2001"], ["ACG2011", "ACG2021"], ["ACG2071"]], "additional": [["GEB1011"]]},
    "computer science": {"groups": [["MAC2312"], ["COP2800"], ["BSC2010", "CHM1045", "PHY2048", "ESC1000"], ["BSC2011", "CHM1046", "PHY2049"]], "additional": [["COP2805C"], ["MAD2104"]]},
    "political science": {"groups": [["INR2002"]], "additional": [["INR2440"], ["PHI1100"]]},
    "psychology": {"groups": [["PSY2012"], ["STA2023"], ["BSC1005", "BSC2010", "BSC2085"], ["DEP2000", "DEP2100", "INP2390", "SOP2772"]], "additional": [["ISS1301"]]},
    "english": {"groups": [["LIT2000"], ["PHI2010"], ["ENC2300"]], "additional": [["ENG2012"], ["CRW2001"], ["ENC2030"]]},
    "economics": {"groups": [["ECO2013"], ["ECO2023"], ["STA2023"]], "additional": []},
    "undecided": {"groups": [], "additional": []},
}

SUBJECT_FOCUS = {
    "math": ["STA2023", "MAC2312", "MAC2313", "MAS2103", "MAD2104"],
    "biology": ["BSC2010", "BSC2011", "BSC2085", "BSC2086", "MCB2010"],
    "business": ["GEB1011", "ECO2013", "ECO2023", "STA2023", "BUL2241"],
    "law": ["INR2002", "INR2440", "PHI1100"],
    "history": ["LIT2000", "PHI2010"],
    "health": ["BSC2085", "BSC2086", "MCB2010", "HUN1201", "DEP2000", "PSY2012"],
    "speech": ["ENC2300", "SPC1017", "SPC2608"],
    "humanities": ["HUM1020", "LIT2000", "PHI2010", "ARH1000"],
    "social science": ["PSY2012", "ANT2000", "ECO2013"],
}

SUMMER_BLOCKED_PREFIXES = ("MAC", "MAD", "MGF", "BSC", "BOT", "CHM", "PHY", "MCB", "AST", "ESC")


# ---------- Helper functions ----------
def classes_needed_from_credits(credits: int) -> int:
    return 0 if credits <= 0 else max(1, math.ceil(credits / 3))


def is_summer_blocked(code: str) -> bool:
    course = courses[code]
    return code.startswith(SUMMER_BLOCKED_PREFIXES) or any(area in course.fulfills for area in ["Mathematics", "Natural Sciences"])


def group_satisfied(group: List[str], completed: Set[str]) -> bool:
    return any(code in completed for code in group)


def pick_group_course(group: List[str], completed: Set[str], locked: Set[str]) -> Optional[str]:
    if group_satisfied(group, completed):
        return None
    for code in group:
        if code in courses and code not in completed and code not in locked:
            return code
    return None


def add_candidate(candidates: Set[str], code: str, priority: int):
    if code in courses:
        candidates.add(code)
        courses[code].priority = max(courses[code].priority, priority)


def related_major_courses(major: str, focus_courses: List[str]) -> Set[str]:
    related = set(focus_courses)
    info = MAJOR_REQS.get(major, {"groups": [], "additional": []})
    for group in info["groups"] + info["additional"]:
        related.update(group)
    return related


def build_candidates(major: str, completed: Set[str], locked: Set[str], gen_needed: Dict[str, int],
                     required_by_ap: Set[str], focus_courses: List[str],
                     required_by_policy: Optional[Set[str]] = None) -> Tuple[List[str], List[List[str]], List[Tuple[List[str], int]], bool]:
    candidates: Set[str] = set()
    required_groups: List[List[str]] = []
    capped_groups: List[Tuple[List[str], int]] = []
    required_by_policy = required_by_policy or set()
    major_related = related_major_courses(major, focus_courses)

    def add_prereqs_recursively(code: str, priority: int, depth: int = 0):
        if depth > 10 or code in completed or code in locked or code not in courses:
            return
        for prereq in courses[code].prereqs:
            add_prereqs_recursively(prereq, 600, depth + 1)
        add_candidate(candidates, code, priority)

    # 1. AP‑required courses (high priority)
    for code in required_by_ap:
        if code not in completed and code not in locked:
            add_candidate(candidates, code, 10000)
            required_groups.append([code])

    for code in required_by_policy:
        if code not in completed and code not in locked:
            add_candidate(candidates, code, 9500)
            required_groups.append([code])

    # 2. General education requirements
    for area, credits in gen_needed.items():
        if credits <= 0:
            continue
        needed_classes = classes_needed_from_credits(credits)
        area_courses = [code for code in GEN_EDS[area]["courses"] if code in courses and code not in completed and code not in locked]
        for code in area_courses:
            if area == "English":
                priority = 9000   # make sure English gets scheduled
            else:
                priority = 800 if code in major_related else 700
            add_candidate(candidates, code, priority)
        if area == "English":
            for code in area_courses[:needed_classes]:
                required_groups.append([code])
        else:
            for _ in range(needed_classes):
                if area_courses:
                    required_groups.append(area_courses)
        general_only = [code for code in area_courses if code not in major_related]
        if general_only:
            capped_groups.append((general_only, needed_classes))

    # 3. Major requirements
    major_info = MAJOR_REQS[major]
    for group in major_info["groups"]:
        if group_satisfied(group, completed):
            continue
        available = [code for code in group if code in courses and code not in locked and code not in completed]
        if not available:
            continue
        required_groups.append(group)
        for code in available:
            add_prereqs_recursively(code, 600)

    for group in major_info["additional"]:
        if group_satisfied(group, completed):
            continue
        available = [code for code in group if code in courses and code not in locked and code not in completed]
        if not available:
            continue
        required_groups.append(group)
        for code in available:
            add_prereqs_recursively(code, 350)

    # 4. Undecided focus courses (only if undecided)
    if major == "undecided":
        for code in focus_courses:
            if code in courses and code not in completed and code not in locked:
                add_candidate(candidates, code, 180)

    return sorted(candidates), required_groups, capped_groups, not candidates


def add_electives_to_fill_slots(candidates: List[str], semesters: List[str],
                                class_limits: Dict[str, Tuple[int, int]]) -> Tuple[List[str], bool]:
    """
    Add electives as placeholders to make sure every semester hits its minimum.
    Returns the updated candidate list and a flag telling if any elective was added.
    """
    elective_codes = []
    for sem in semesters:
        min_classes, _ = class_limits[sem]
        for i in range(min_classes):
            code = f"ELECTIVE_{sem.replace(' ', '_').upper()}_{i + 1}"
            if code not in candidates:
                courses[code] = Course("Elective Class*", workload=0, priority=50,
                                       allowed_terms=[sem], fulfills=["Elective"])
                elective_codes.append(code)
    return sorted(set(candidates).union(elective_codes)), len(elective_codes) > 0


def create_schedule(candidates: List[str], required_groups: List[List[str]],
                    capped_groups: List[Tuple[List[str], int]], semesters: List[str],
                    class_limits: Dict[str, Tuple[int, int]], completed: Set[str],
                    term_start_additions: Dict[str, Set[str]], locked: Set[str],
                    max_workload: float):
    if not candidates:
        return {sem: [] for sem in semesters}

    prob = pulp.LpProblem("SAS_schedule", pulp.LpMinimize)
    x = pulp.LpVariable.dicts("take", ((c, s) for c in candidates for s in semesters), cat="Binary")

    # Balancing: try to keep the number of required courses even across semesters
    required_count = len([c for c in candidates if not c.startswith("ELECTIVE_")])
    Y = len(semesters)
    avg = required_count / Y if Y > 0 and required_count > 0 else 0

    dev_pos = pulp.LpVariable.dicts("dev_pos", semesters, lowBound=0, cat='Continuous')
    dev_neg = pulp.LpVariable.dicts("dev_neg", semesters, lowBound=0, cat='Continuous')
    count_s = pulp.LpVariable.dicts("count_s", semesters, lowBound=0, cat='Integer')

    for s in semesters:
        prob += count_s[s] == pulp.lpSum(x[c, s] for c in candidates if not c.startswith("ELECTIVE_"))
        prob += count_s[s] - avg == dev_pos[s] - dev_neg[s]

    balancing_weight = 0.1

    # Objective: minimize priority cost + slight balancing penalty.
    # The multiplier 5 on semester index nudges courses earlier.
    priority_term = pulp.lpSum(x[c, s] * ((10000 - courses[c].priority) + semesters.index(s) * 5)
                               for c in candidates for s in semesters)
    balance_term = pulp.lpSum(dev_pos[s] + dev_neg[s] for s in semesters)
    prob += priority_term + balancing_weight * balance_term

    # Constraints
    for c in candidates:
        prob += pulp.lpSum(x[c, s] for s in semesters) <= 1
        allowed = courses[c].allowed_terms
        if allowed:
            for s in semesters:
                if s not in allowed:
                    prob += x[c, s] == 0

    for s in semesters:
        count = pulp.lpSum(courses[c].class_count * x[c, s] for c in candidates)
        work = pulp.lpSum(courses[c].workload * x[c, s] for c in candidates)
        min_classes, max_classes = class_limits[s]
        prob += count >= min_classes
        prob += count <= max_classes
        prob += work <= max_workload

    for group_key, needed_count in Counter(tuple(group) for group in required_groups).items():
        group_candidates = [c for c in group_key if c in candidates]
        if group_candidates:
            prob += pulp.lpSum(x[c, s] for c in group_candidates for s in semesters) >= needed_count

    for group, max_count in capped_groups:
        group_candidates = [c for c in group if c in candidates]
        if group_candidates:
            prob += pulp.lpSum(x[c, s] for c in group_candidates for s in semesters) <= max_count

    # Adjacency for single‑prereq courses (skip summer)
    academic_prev = {}
    for i, s in enumerate(semesters):
        prev = None
        for j in range(i - 1, -1, -1):
            if "Summer" not in semesters[j]:
                prev = semesters[j]
                break
        academic_prev[s] = prev

    for c in candidates:
        if c.startswith("ELECTIVE_"):
            continue
        prereqs = courses[c].prereqs
        if len(prereqs) == 1:
            p = prereqs[0]
            if p in candidates and p not in completed and p not in locked:
                for t in semesters:
                    if "Summer" not in t:
                        prev_t = academic_prev[t]
                        if prev_t is not None:
                            prob += x[c, t] <= x[p, prev_t]

    # Standard prereq constraints (must be taken earlier)
    for c in candidates:
        for s in semesters:
            if c in locked:
                prob += x[c, s] == 0
            if "Summer" in s and is_summer_blocked(c):
                prob += x[c, s] == 0
            s_index = semesters.index(s)
            available_before = set(completed)
            for sem in semesters[:s_index + 1]:
                available_before.update(term_start_additions.get(sem, set()))
            for prereq in courses[c].prereqs:
                if prereq in available_before:
                    continue
                earlier_terms = semesters[:s_index]
                if prereq in candidates and earlier_terms:
                    prob += x[c, s] <= pulp.lpSum(x[prereq, t] for t in earlier_terms)
                else:
                    prob += x[c, s] == 0

    status_code = prob.solve(pulp.PULP_CBC_CMD(msg=False, timeLimit=30))
    if pulp.LpStatus[status_code] != "Optimal":
        print("Workload/class limits blocked an optimal schedule. Falling back to priority order...")
        return priority_fallback(candidates, capped_groups, semesters, class_limits,
                                 completed, term_start_additions, locked, max_workload)

    schedule = defaultdict(list)
    for c in candidates:
        for s in semesters:
            if pulp.value(x[c, s]) > 0.5:
                schedule[s].append(c)
    return {sem: sorted(schedule[sem], key=lambda code: (-courses[code].priority, courses[code].name)) for sem in semesters}


def priority_fallback(candidates: List[str], capped_groups: List[Tuple[List[str], int]],
                      semesters: List[str], class_limits: Dict[str, Tuple[int, int]],
                      completed: Set[str], term_start_additions: Dict[str, Set[str]],
                      locked: Set[str], max_workload: float):
    schedule = {sem: [] for sem in semesters}
    current_work = {sem: 0.0 for sem in semesters}
    done = set(completed)
    capped_lookup = {code: (set(group), max_count) for group, max_count in capped_groups for code in group}
    sorted_candidates = sorted(candidates, key=lambda code: courses[code].priority, reverse=True)
    for sem in semesters:
        done.update(term_start_additions.get(sem, set()))
        min_classes, max_classes = class_limits[sem]
        for code in sorted_candidates:
            if code in done or code in locked or code in schedule[sem]:
                continue
            course = courses[code]
            if course.allowed_terms and sem not in course.allowed_terms:
                continue
            if "Summer" in sem and is_summer_blocked(code):
                continue
            if len(schedule[sem]) + course.class_count > max_classes:
                continue
            if current_work[sem] + course.workload > max_workload:
                continue
            if code in capped_lookup:
                group, max_count = capped_lookup[code]
                already_taken = sum(1 for classes in schedule.values() for sc in classes if sc in group)
                if already_taken >= max_count:
                    continue
            if all(prereq in done for prereq in course.prereqs):
                schedule[sem].append(code)
                current_work[sem] += course.workload
        done.update(schedule[sem])
        if len(schedule[sem]) < min_classes:
            print(f"Warning: only {len(schedule[sem])} eligible classes for {sem}; needed {min_classes}.")
    return schedule


# ---------- Streamlit UI ----------
FUNCTION_WORDS = {"a", "an", "and", "as", "at", "but", "by", "for", "in", "nor", "of",
                  "on", "or", "per", "the", "to", "with"}


def title_case_label(text: str) -> str:
    words = str(text).replace("_", " ").split()
    fixed = []
    for i, word in enumerate(words):
        lower = word.lower()
        if i > 0 and lower in FUNCTION_WORDS:
            fixed.append(lower)
        else:
            fixed.append(word[:1].upper() + word[1:])
    return " ".join(fixed)


def display_course_name(code: str) -> str:
    name = courses[code].name
    if " - " not in name:
        return title_case_label(name)
    prefix, title = name.split(" - ", 1)
    return f"{prefix} - {title_case_label(title)}"


def major_course_options(major: str) -> List[str]:
    if major == "undecided":
        return []
    seen = set()
    options = []
    info = MAJOR_REQS[major]
    for group in info["groups"] + info["additional"]:
        for code in group:
            if code in courses and code not in seen:
                options.append(code)
                seen.add(code)
    return options


def transform_workload(user_hours: int) -> float:
    # Map 5‑20 hours to a workload cap that grows steeply
    transformed = 4 + (user_hours - 5) * (5 / 3)  # slope ≈ 1.67
    return round(min(transformed, 20), 1)


def get_course_fulfillment_label(code: str, major: str, gen_needed: Dict[str, int],
                                 required_by_ap: Set[str]) -> str:
    course = courses[code]
    if code in required_by_ap:
        return "Required by AP Score"
    major_info = MAJOR_REQS.get(major, {})
    for group in major_info.get("groups", []):
        if code in group:
            return "Major Requirement"
    for group in major_info.get("additional", []):
        if code in group:
            return "Major Requirement"
    for area, credits in gen_needed.items():
        if credits > 0 and code in GEN_EDS[area]["courses"]:
            return f"General Requirement: {area}"
    if "Elective" in course.fulfills:
        return "Elective"
    if course.fulfills:
        return course.fulfills[0]
    return "Additional Course"


AP_SOCIAL_CREDIT_COURSES = {"AMH2010", "AMH2020", "POS2041", "ECO2013"}

AP_CREDIT_MAP = {
    "AP Precalculus": {3: ["MAC1147"], 4: ["MAC1147"], 5: ["MAC1147"]},
    "AP Calculus AB": {3: ["MAC2311"], 4: ["MAC2311"], 5: ["MAC2311"]},
    "AP Calculus BC": {3: ["MAC2311"], 4: ["MAC2311"], 5: ["MAC2311"]},
    "AP English Literature": {3: ["ENC1101"], 4: ["ENC1101", "ENC1102"], 5: ["ENC1101", "ENC1102"]},
    "AP English Language": {3: ["ENC1101"], 4: ["ENC1101", "ENC1102"], 5: ["ENC1101", "ENC1102"]},
    "AP US History": {3: ["AMH2010"], 4: ["AMH2010", "AMH2020"], 5: ["AMH2010", "AMH2020"]},
    "AP Government": {3: ["POS2041"], 4: ["POS2041"], 5: ["POS2041"]},
    "AP Macroeconomics": {3: ["ECO2013"], 4: ["ECO2013"], 5: ["ECO2013"]},
    "AP Biology": {3: ["BSC1005"], 4: ["BSC2010"], 5: ["BSC2010", "BSC2011"]},
    "AP Chemistry": {3: ["CHM1045"], 4: ["CHM1045"], 5: ["CHM1045"]},
    "AP Physics 1": {3: ["PHY2053"], 4: ["PHY2053"], 5: ["PHY2053"]},
    "AP Physics 2": {3: ["PHY2054"], 4: ["PHY2054"], 5: ["PHY2054"]},
    "AP Physics C: Mechanics": {3: ["PHY2053"], 4: ["PHY2048"], 5: ["PHY2048"]},
    "AP Statistics": {3: ["STA2023"], 4: ["STA2023"], 5: ["STA2023"]},
    "AP Psychology": {3: ["PSY2012"], 4: ["PSY2012"], 5: ["PSY2012"]},
    "AP Art History": {3: ["ARH1000"], 4: ["ARH1000", "ARH2051"], 5: ["ARH1000", "ARH2051"]},
}


st.set_page_config(page_title="SAS Kendall AA Planner", layout="wide")

# Styling (kept the same)
st.markdown(
    """
    <style>
    /* Global Reset & Fonts */
    html, body, [class*="css"] {
        font-family: 'Arial', 'Helvetica Neue', sans-serif !important;
        background-color: #f5f5f5;
        color: #333333;
    }
    .stApp { background: #f5f5f5; }
    h1, h2, h3, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: #1a3b5c !important;
        font-family: 'Arial', 'Helvetica Neue', sans-serif !important;
        font-weight: 700;
    }
    .main-title {
        text-align: center;
        font-size: 2.5rem;
        font-weight: 800;
        color: #1a3b5c;
        margin-top: -1rem;
        margin-bottom: 0.25rem;
        letter-spacing: -0.5px;
    }
    .sub-title {
        text-align: center;
        font-size: 1.1rem;
        color: #4a6a8a;
        margin-bottom: 2rem;
        border-bottom: 2px solid #e0e7ef;
        padding-bottom: 1rem;
    }
    .accolades-banner {
        background: linear-gradient(135deg, #1a3b5c 0%, #2a5a7a 100%);
        color: white;
        padding: 1.25rem 1.5rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    .accolades-banner .badge {
        display: inline-block;
        background: rgba(255,255,255,0.15);
        padding: 0.25rem 1rem;
        border-radius: 20px;
        margin: 0.2rem 0.4rem;
        font-size: 0.85rem;
        font-weight: 600;
        letter-spacing: 0.3px;
        border: 1px solid rgba(255,255,255,0.1);
    }
    .accolades-banner .badge-highlight {
        background: #ffd700;
        color: #1a3b5c;
    }
    .sas-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem 1.75rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        border: 1px solid #e8ecf0;
        transition: box-shadow 0.2s ease;
    }
    .sas-card:hover {
        box-shadow: 0 4px 16px rgba(0,0,0,0.10);
    }
    .sas-card h3 {
        margin-top: 0;
        color: #1a3b5c;
        font-size: 1.2rem;
        font-weight: 700;
        border-bottom: 2px solid #eef2f6;
        padding-bottom: 0.5rem;
        margin-bottom: 1rem;
    }
    div[data-testid="stButton"] > button {
        background: #1a3b5c !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
        padding: 0.6rem 2rem !important;
        font-size: 1rem !important;
        transition: background 0.2s ease;
        width: 100%;
    }
    div[data-testid="stButton"] > button:hover {
        background: #2a5a7a !important;
        color: white !important;
        border-color: #2a5a7a !important;
    }
    .stSelectbox, .stNumberInput, .stMultiSelect {
        background: white;
        border-radius: 8px;
    }
    .stSelectbox > div > div, .stNumberInput > div > div {
        border-radius: 8px !important;
        border-color: #d0d7df !important;
    }
    [data-testid="stSidebar"] {
        background: #f8fafc !important;
        border-right: 1px solid #e8ecf0;
    }
    [data-testid="stSidebar"] .stMarkdown {
        color: #1a3b5c;
    }
    .course-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-left: 5px solid #1a3b5c;
        border-radius: 8px;
        padding: 0.75rem 1rem;
        margin-bottom: 0.75rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        transition: transform 0.1s ease;
    }
    .course-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }
    .course-card .class-number {
        font-size: 0.7rem;
        font-weight: 700;
        color: #8a9aa8;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .course-card .course-name {
        font-size: 0.95rem;
        font-weight: 700;
        color: #1a3b5c;
        line-height: 1.3;
    }
    .course-card .course-label {
        font-size: 0.75rem;
        color: #6a7a8a;
        margin-top: 4px;
    }
    .course-card .course-label b {
        color: #1a3b5c;
    }
    .semester-header {
        font-size: 1.3rem;
        font-weight: 700;
        color: #1a3b5c;
        margin-bottom: 0.75rem;
        padding-bottom: 0.25rem;
        border-bottom: 3px solid #1a3b5c;
        display: inline-block;
    }
    .notice-box {
        background: #f0f4f8;
        border-left: 5px solid #1a3b5c;
        border-radius: 8px;
        padding: 1rem 1.25rem;
        margin: 1rem 0;
        font-size: 0.9rem;
        color: #2a3a4a;
    }
    .notice-box strong {
        color: #1a3b5c;
    }
    .footer-disclaimer {
        font-size: 0.8rem;
        color: #6a7a8a;
        border-top: 1px solid #e0e7ef;
        padding-top: 1.5rem;
        margin-top: 2rem;
        text-align: center;
    }
    @media (max-width: 768px) {
        .main-title { font-size: 1.8rem; }
        .accolades-banner .badge { font-size: 0.7rem; padding: 0.15rem 0.6rem; }
        .sas-card { padding: 1rem; }
    }
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)

# Header
st.markdown(
    """
    <div style="text-align: center; padding: 0.5rem 0 0.25rem 0;"></div>
    <div class="main-title">SAS Kendall AA Planner</div>
    <div class="sub-title">Interactive scheduling optimizer for School for Advanced Studies</div>
    """,
    unsafe_allow_html=True,
)

# Planner description
st.markdown(
    """
    <div style="background: #1a3b5c; color: white; padding: 1.25rem 1.75rem; border-radius: 10px; margin-bottom: 1.5rem; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
    <div style="font-size: 1.1rem; font-weight: 700; margin-bottom: 0.5rem;">Personalized SAS Planner</div>
    <ul style="margin: 0; padding-left: 1.2rem; line-height: 1.8;">
        <li>Builds a semester‑by‑semester plan centered around your major and progress.</li>
        <li>Accounts for completed courses, AP credits, and strict prerequisite restrictions.</li>
        <li>Balances your workload across semesters based on your available study hours.</li>
        <li>Ensures all AA general education and major requirements are fulfilled.</li>
        <li>Suggests optimal course sequences while respecting school policies and constraints.</li>
    </ul>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------- User inputs ----------
completed = set()
locked_courses = set()
required_by_ap = set()
required_by_policy = set()
term_start_additions = {}
calc2_unlocked = False

PERMANENTLY_BLOCKED = {"MAC2311", "MAC1106", "MAC1114", "MAC1140", "MAC1147", "MAC2233"}
locked_courses.update(PERMANENTLY_BLOCKED)

with st.container():
    col1, col2 = st.columns(2)
    with col1:
        status = st.selectbox("Plan Type", ["junior", "senior"], format_func=title_case_label)
    with col2:
        if status == "senior":
            term_choice = st.selectbox("Semester Plan", ["fall", "spring", "both"], format_func=title_case_label)
        else:
            start_term = st.selectbox("Start Plan From", ["fall", "spring", "summer"], format_func=title_case_label)

semesters = []
class_limits = {}

if status == "senior":
    if term_choice in ["fall", "both"]:
        semesters.append("Fall Senior")
    if term_choice in ["spring", "both"]:
        semesters.append("Spring Senior")
    for sem in semesters:
        count_choice = st.selectbox(f"Number of classes for {title_case_label(sem)}", [3, 4], key=sem)
        class_limits[sem] = (count_choice, count_choice)
else:
    if start_term == "fall":
        semesters.extend(["Fall Junior", "Spring Junior"])
    elif start_term == "spring":
        semesters.append("Spring Junior")
    summer_amount = st.selectbox("Summer Junior Classes", [0, 1, 2, 3, 4],
                                 help="Choose 0 if you do not want a summer class.")
    if start_term == "summer" or summer_amount > 0:
        semesters.append("Summer Junior")
    semesters.extend(["Fall Senior", "Spring Senior"])
    for sem in semesters:
        if sem == "Summer Junior":
            class_limits[sem] = (summer_amount, summer_amount)
        elif sem in ["Fall Junior", "Spring Junior"]:
            class_limits[sem] = (3, 3)
        else:
            count_choice = st.selectbox(f"Number of classes for {title_case_label(sem)}", [3, 4], key=sem)
            class_limits[sem] = (count_choice, count_choice)

st.subheader("SAS Context")

if any(sem.startswith("Fall") for sem in semesters):
    a_or_b_year = st.selectbox("Upcoming Fall Year",
                               ["A Year (APUSH + AP Lang)", "B Year (AP Gov + AP Macro + AP Lit)"])
else:
    a_or_b_year = None

if status == "junior":
    col1, col2 = st.columns(2)
    with col1:
        took_mac1105 = st.selectbox("Did You Already Take MAC1105 Before Junior Year? (Summer or Before)",
                                    ["No", "Yes"])
    with col2:
        junior_math = st.selectbox("Current/Planned Junior Math Class",
                                   ["AP Precalc", "AP Calc AB", "AP Calc BC"])

    if took_mac1105 == "Yes":
        completed.add("MAC1105")
    elif "Fall Junior" in semesters:
        required_by_policy.add("MAC1105")
        courses["MAC1105"].allowed_terms = ["Fall Junior"]

    junior_math_key = junior_math.lower()
    term_start_additions = {sem: set() for sem in semesters}
    senior_sems = [s for s in semesters if "Senior" in s]

    if junior_math_key == "ap precalc":
        for sem in senior_sems:
            term_start_additions[sem].add("MAC1147")
        take_ab_next = st.selectbox("Will you take AP Calculus AB next year (senior year)?", ["No", "Yes"])
        if take_ab_next == "Yes":
            for sem in senior_sems:
                term_start_additions[sem].add("MAC2311")
            st.success("Courses requiring Calculus 1 (e.g., PHY2048) become available in senior year.")
        locked_courses.add("MAC2312")

    elif junior_math_key == "ap calc ab":
        for sem in senior_sems:
            term_start_additions[sem].update(["MAC1147", "MAC2311"])
        take_bc_next = st.selectbox("Will you take AP Calculus BC next year (senior year)?", ["No", "Yes"])
        if take_bc_next == "Yes":
            calc2_unlocked = True
            courses["MAC2312"].allowed_terms = senior_sems
            st.success("MAC2312 (Calculus 2) will be available for scheduling in your senior year.")
        else:
            locked_courses.add("MAC2312")
            calc2_unlocked = False

    elif junior_math_key == "ap calc bc":
        for sem in senior_sems:
            term_start_additions[sem].update(["MAC1147", "MAC2311", "MAC2312"])
        locked_courses.discard("MAC2312")
        calc2_unlocked = True
        st.success("AP Calculus BC gives you credit for Calculus 1 and 2.")

    if took_mac1105 == "Yes":
        completed.add("MAC1105")
        required_by_policy.discard("MAC1105")

else:  # senior
    col1, col2 = st.columns(2)
    with col1:
        senior_last_math = st.selectbox("Math Class Taken Last Year",
                                        ["None", "AP Precalc", "AP Calc AB", "AP Calc BC"])
    with col2:
        senior_current_math = st.selectbox("Math Class You Are Taking Now",
                                           ["None", "AP Precalc", "AP Calc AB", "AP Calc BC"])
    senior_math_values = {senior_last_math.lower(), senior_current_math.lower()}
    if "ap calc bc" in senior_math_values:
        apply_ap_math_credit("ap calc bc", completed, locked_courses, senior_requires_bc_for_calc2=False)
        calc2_unlocked = True
        st.success("AP Calc BC unlocks Calculus 2.")
    elif "ap calc ab" in senior_math_values:
        apply_ap_math_credit("ap calc ab", completed, locked_courses, senior_requires_bc_for_calc2=True)
        st.info("AP Calc AB satisfies Calc 1, but Calculus 2 stays locked unless BC is also taken.")
    elif "ap precalc" in senior_math_values:
        apply_ap_math_credit("ap precalc", completed, locked_courses, senior_requires_bc_for_calc2=True)
        locked_courses.add("MAC2312")
    else:
        locked_courses.add("MAC2312")

# Notice box
st.markdown(
    """
    <div class="notice-box">
        <strong>Course Availability Notice</strong><br>
        • <strong>MAC 2311 (Calculus 1)</strong> is not available at SAS – it's taken as <strong>AP Calculus AB</strong> and will never appear in the schedule.<br>
        • <strong>MAC 2312 (Calculus 2)</strong> can only be scheduled if you are taking <strong>AP Calculus BC</strong>.<br>
        • <strong>PHY 2048 + L</strong> can be scheduled if you take the <strong>AP Calculus AB</strong> path. Physics 2 still requires Physics 1 first.<br>
        • <strong>AMH2010, AMH2020, ECO2013, and POS2041</strong> are not available at SAS – they are covered by their <strong>AP</strong> equivalents.
    </div>
    """,
    unsafe_allow_html=True,
)

col1, col2 = st.columns(2)
with col1:
    major = st.selectbox("Major", list(MAJOR_REQS.keys()), format_func=title_case_label)
with col2:
    real_hours = st.number_input("How many hours/week do you realistically spend on college coursework?",
                                 min_value=5, max_value=20, value=10,
                                 help="Be honest – this determines how many classes you can handle.")

focus_courses = []
if major == "undecided":
    focus = st.selectbox("Undecided Focus", ["none"] + sorted(SUBJECT_FOCUS.keys()), format_func=title_case_label)
    if focus != "none":
        focus_courses = SUBJECT_FOCUS[focus]

taking_physics_c = st.checkbox(
    "Are you currently taking AP Physics C: Mechanics at SAS?",
    help="Checking this will subtract 2 hours from your workload limit to account for the extra effort."
)
if taking_physics_c:
    completed.add("PHY2048")
    st.success("PHY2048 credit granted – you can now take PHY2049 without it.")

max_workload = transform_workload(real_hours)
if taking_physics_c:
    max_workload = max(1.0, max_workload - 2.0)

st.subheader("Completed Courses")

if major == "undecided":
    if focus_courses:
        completed_selection = st.multiselect("Select completed courses from your focus area",
                                             options=focus_courses, format_func=display_course_name)
        completed.update(completed_selection)
    else:
        st.caption("No focus selected yet.")
else:
    major_completed_options = major_course_options(major)
    if major_completed_options:
        completed_selection = st.multiselect("Select completed classes for your major",
                                             options=major_completed_options, format_func=display_course_name)
        completed.update(completed_selection)
    else:
        st.caption("No major-specific completed courses are needed.")

if completed:
    st.caption(f"**Currently marked as completed:** {', '.join(sorted(completed))}")

st.subheader("AP Scores")
if "show_ap_scores" not in st.session_state:
    st.session_state.show_ap_scores = False

if st.button("Add AP Scores", key="ap_toggle"):
    st.session_state.show_ap_scores = not st.session_state.show_ap_scores

ap_grants = {}
english_message = None

if st.session_state.show_ap_scores:
    left, right = st.columns([2, 1])
    with left:
        st.caption("Check an AP class, then enter the score.")
        for ap_name in AP_CREDIT_MAP:
            selected = st.checkbox(ap_name, key=f"ap_selected_{ap_name}")
            if selected:
                score = st.selectbox(f"{ap_name} Score", [1, 2, 3, 4, 5], key=f"ap_score_{ap_name}")
                granted = AP_CREDIT_MAP[ap_name].get(score, [])
                if granted:
                    completed.update(granted)
                    ap_grants[ap_name] = granted
                if ap_name == "AP Precalculus" and score in [3, 4, 5]:
                    completed.update(["MAC1105", "MAC1147"])
                if ap_name == "AP Calculus AB" and score in [3, 4, 5]:
                    completed.update(["MAC1105", "MAC1147", "MAC2311"])
                    if not calc2_unlocked:
                        locked_courses.add("MAC2312")
                if ap_name == "AP Calculus BC" and score in [3, 4, 5]:
                    completed.update(["MAC1105", "MAC1147", "MAC2311"])
                    calc2_unlocked = True
                    locked_courses.discard("MAC2312")
                if ap_name == "AP Physics C: Mechanics" and score in [3, 4, 5]:
                    completed.add("PHY2048")
                if status == "senior" and ap_name in ["AP English Literature", "AP English Language"]:
                    if score >= 4:
                        completed.update(["ENC1101", "ENC1102"])
                        english_credits_needed = 0
                        st.success("AP English covers both ENC1101 and ENC1102.")
                    elif score == 3:
                        completed.add("ENC1101")
                        english_credits_needed = 3
                        st.info("AP English gives credit for ENC1101 only; you still need ENC1102.")
                if status == "senior" and ap_name == "AP Government" and score in [1, 2]:
                    required_by_ap.add("POS2041")
                if status == "senior" and ap_name == "AP US History" and score in [1, 2]:
                    required_by_ap.add("AMH2020")
                if status == "senior" and ap_name == "AP Macroeconomics" and score in [1, 2]:
                    required_by_ap.add("ECO2013")
    with right:
        if ap_grants:
            st.info("Credit Granted")
            for ap_name, granted in ap_grants.items():
                granted_names = ", ".join(display_course_name(code) for code in granted)
                st.write(f"**{ap_name}:** {granted_names}")
        else:
            st.caption("Credits granted will appear here.")

if english_message:
    st.info(english_message)

locked_courses.update(PERMANENTLY_BLOCKED)
if calc2_unlocked:
    locked_courses.discard("MAC2312")
else:
    locked_courses.add("MAC2312")

st.subheader("General Requirements")
st.caption("Use Academic Progress in MyMDC to check which general AA requirements you still need.")

general_needed = {}

for area, meta in GEN_EDS.items():
    if area == "English":
        if status == "senior":
            english_credits_needed = st.selectbox(
                "English credits still needed?",
                [0, 3, 6],
                key="english_credits",
                help="If you got a 3 or less in AP English: 3 → only ENC1102 needed; 6 → both ENC1101 and ENC1102 needed."
            )
            general_needed[area] = english_credits_needed
        else:
            general_needed[area] = 0
        continue

    if meta.get("yes_no"):
        needed_label = st.selectbox(f"Still Need {title_case_label(area)}?", ["No", "Yes"], key=area)
        general_needed[area] = 3 if needed_label == "Yes" else 0
    else:
        general_needed[area] = st.selectbox(
            f"{title_case_label(area)} Credits Remaining",
            sorted(list(meta["allowed"])),
            key=area
        )

# ---------- Generate Schedule ----------
run = st.button("Generate Schedule", use_container_width=True)

if run:
    for code in AP_SOCIAL_CREDIT_COURSES:
        if code in courses and code not in required_by_ap:
            courses[code].priority = -1000

    candidates, required_groups, capped_groups, all_done = build_candidates(
        major, completed, locked_courses, general_needed, required_by_ap,
        focus_courses, required_by_policy
    )

    candidates, elective_added = add_electives_to_fill_slots(candidates, semesters, class_limits)

    if not candidates:
        st.warning("No courses to schedule. Please check your completed courses and requirements.")
    else:
        schedule = create_schedule(
            candidates, required_groups, capped_groups, semesters, class_limits,
            completed, term_start_additions or {s: set() for s in semesters},
            locked_courses, max_workload
        )

        # Check if workload is near the limit
        workload_warning = False
        for sem, classes in schedule.items():
            total_work = sum(courses[code].workload for code in classes)
            if total_work >= 0.9 * max_workload:
                workload_warning = True
                break

        if workload_warning:
            st.warning(
                "**Possible Workload Limit Reached**\n\n"
                "Your schedule respects your reported available hours. "
                "It's possible that additional courses (or heavier ones) were skipped because they'd exceed your limit. "
                "If you feel you can handle more, increase your weekly hours above."
            )

        st.success("Schedule was created successfully")

        elective_scheduled = any("Elective" in courses[code].fulfills
                                 for sem_classes in schedule.values() for code in sem_classes)

        if any(schedule.values()):
            st.subheader("Planned Schedule")
            calendar_columns = st.columns(len(schedule))
            for column, (sem, classes) in zip(calendar_columns, schedule.items()):
                with column:
                    st.markdown(f'<div class="semester-header">{title_case_label(sem)}</div>', unsafe_allow_html=True)
                    if not classes:
                        st.caption("No classes scheduled.")
                    for index, code in enumerate(classes, start=1):
                        course = courses[code]
                        label = get_course_fulfillment_label(code, major, general_needed, required_by_ap)
                        st.markdown(
                            f"""
                            <div class="course-card">
                                <div class="class-number">Class {index}</div>
                                <div class="course-name">{display_course_name(code)}</div>
                                <div class="course-label"><b>{label}</b></div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
        else:
            st.warning("No schedule found with the current requirements.")

        if elective_scheduled:
            st.info(
                "All requirements appear complete. Electives were added. "
                "You can choose any course – a higher‑division class, a fun elective, or something you're curious about. "
                "The choice is yours!"
            )

    st.markdown(
        """
        <div class="footer-disclaimer">
            <strong>Disclaimer:</strong> This schedule is a layout meant to give you an idea, inspiration, and a basis to begin researching your future schedule. 
            You should always meet with our college advisor and your counselor for further guidance, as despite being a useful tool for efficiency, it is not perfect.
        </div>
        """,
        unsafe_allow_html=True,
    )