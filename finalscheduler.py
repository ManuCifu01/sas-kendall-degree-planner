#!/usr/bin/env python3
"""
SAS AA Degree Planner v9 - SAS-focused scheduler.
"""

import math
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

import pulp


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


all_courses: Dict[str, Course] = {
    # English replaces the old "Communications" label.
    "ENC1101": Course("ENC 1101 - English Composition 1", workload=1.5, difficulty=4, fulfills=["English"]),
    "ENC1102": Course("ENC 1102 - English Composition 2", workload=1.5, difficulty=5, prereqs=["ENC1101"], fulfills=["English"]),
    "ENC2300": Course("ENC 2300 - Advanced Composition and Communication", workload=2, fulfills=["Oral Communication"]),
    "SPC1017": Course("SPC 1017 - Introduction to Communication", workload=1.5, fulfills=["Oral Communication"]),
    "SPC2608": Course("SPC 2608 - Introduction to Public Speaking", workload=2, fulfills=["Oral Communication"]),
    "ENG2012": Course("ENG 2012 - Literary Theory", workload=1.5),
    "CRW2001": Course("CRW 2001 - Creative Writing 1", workload=1.5),

    # Humanities.
    "ARH1000": Course("ARH 1000 - Art Appreciation", workload=1, fulfills=["Humanities"]),
    "ARH2051": Course("ARH 2051 - Art History 2", workload=1, fulfills=["Humanities"]),
    "HUM1020": Course("HUM 1020 - Humanities", workload=1.5, fulfills=["Humanities"]),
    "LIT2000": Course("LIT 2000 - Introduction to Literature", workload=2, fulfills=["Humanities"]),
    "MUL1010": Course("MUL 1010 - Music Appreciation", workload=1, fulfills=["Humanities"]),
    "PHI2010": Course("PHI 2010 - Introduction to Philosophy", workload=2, fulfills=["Humanities"]),
    "PHI1100": Course("PHI 1100 - Introduction to Logic", workload=1.5, fulfills=["Humanities"]),
    "THE2000": Course("THE 2000 - Theatre Appreciation", workload=1.5, fulfills=["Humanities"]),

    # Social sciences.
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

    # Computer competency and computing.
    "CGS1060C": Course("CGS 1060C - Introduction to Computer Technology and Applications", credits=4, workload=1.5, fulfills=["Computer Competency"]),
    "COP1047C": Course("COP 1047C - Introduction to Python Programming", workload=2),
    "COP2270": Course("COP 2270 - C Programming for Engineers", workload=2.5, difficulty=7),
    "COP2800": Course("COP 2800 - Java Programming", workload=2.5, difficulty=7),
    "COP2805C": Course("COP 2805C - Advanced Java Programming", workload=3, difficulty=7, prereqs=["COP2800"]),

    # Business.
    "ACG2001": Course("ACG 2001 + L - Principles of Accounting 1 + Lab", credits=4, workload=2.5),
    "ACG2011": Course("ACG 2011 + L - Principles of Accounting 2 + Lab", credits=4, workload=2.5, prereqs=["ACG2001"]),
    "ACG2021": Course("ACG 2021 + L - Financial Accounting + Lab", credits=4, workload=2.5),
    "ACG2071": Course("ACG 2071 + L - Managerial Accounting + Lab", credits=4, workload=2.5, prereqs=["ACG2011"]),
    "BUL2241": Course("BUL 2241 - Business Law I", workload=1.5),
    "GEB1011": Course("GEB 1011 - Principles of Business", workload=1.5),

    # Mathematics.
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

    # Natural sciences.
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

    # Engineering.
    "EGN1008C": Course("EGN 1008C - Introduction to Engineering", workload=1.5),
    "EGN2312": Course("EGN 2312 - Engineering Analysis", workload=2, prereqs=["MAC2311"]),
}

# SWIPE_PC_ADDED_RULES_START
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
    all_courses[code].prereqs = prereqs
# SWIPE_PC_ADDED_RULES_END


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
    for code, course in all_courses.items():
        if course.workload <= 0:
            continue
        # Base scaling: multiply by 1.5 to get more realistic numbers
        base = course.workload * 1.5
        # Add extra weight for hard courses
        if code in HARD_WORKLOAD_COURSES:
            base *= 1.5
        elif code in MEDIUM_HARD_WORKLOAD_COURSES:
            base *= 1.2
        # Cap at 8 to avoid extreme values
        course.workload = min(round(base, 1), 8.0)


recalibrate_course_workloads()

GENERAL_REQUIREMENTS = {
    "English": {"courses": ["ENC1101", "ENC1102"], "prompt": "English composition credits still needed? (0, 3, or 6): ", "allowed": {0, 3, 6}},
    "Oral Communication": {"courses": ["SPC1017", "SPC2608"], "prompt": "Do you still need Oral Communication? (yes/no): ", "yes_no": True},
    "Mathematics": {"courses": ["STA2023", "MGF1130", "MAC2233"], "prompt": "Math credits still needed? (0, 3, or 6): ", "allowed": {0, 3, 6}},
    "Humanities": {"courses": ["ARH1000", "HUM1020", "LIT2000", "MUL1010", "PHI2010", "THE2000"], "prompt": "Humanities credits still needed? (0, 3, or 6): ", "allowed": {0, 3, 6}},
    "Social Sciences": {"courses": ["PSY2012", "ANT2000", "ECO2023"], "prompt": "Social Sciences credits still needed? (0, 3, or 6): ", "allowed": {0, 3, 6}},
    "Natural Sciences": {"courses": ["AST1002", "BSC1005", "BSC2010", "BSC2011", "BSC2085", "CHM1025", "CHM1045", "CHM1046", "ESC1000", "PHY2048", "PHY2049", "PHY2053", "PHY2054"], "prompt": "Natural Science credits still needed? (0, 3, 4, 6, or 8): ", "allowed": {0, 3, 4, 6, 8}},
    "Computer Competency": {"courses": ["CGS1060C"], "prompt": "Do you still need Computer Competency? (yes/no): ", "yes_no": True},
}

MAJOR_REQUIREMENTS = {
    "engineering": {"groups": [["MAC2312"], ["MAC2313"], ["MAP2302"], ["CHM1045"], ["PHY2048"], ["PHY2049"]], "additional": [["EGN1008C"], ["COP2270"], ["STA2023"]]},
    "nursing": {"groups": [["BSC2085"], ["BSC2086"], ["MCB2010"], ["CHM1033"], ["HUN1201"], ["DEP2000"], ["PSY2012"], ["STA2023"]], "additional": []},
    "chemistry": {"groups": [["MAC2312"], ["CHM1045"], ["CHM1046"], ["CHM2210"], ["CHM2211"], ["PHY2048"], ["PHY2049"]], "additional": [["MAC2313"], ["MAP2302"], ["COP2270"]]},
    "biology": {"groups": [["MAC2312"], ["BSC2010"], ["BSC2011"], ["CHM1045"], ["CHM1046"], ["CHM2210"], ["CHM2211"], ["PHY2048"], ["PHY2049"]], "additional": []},
    "physics": {"groups": [["MAC2312"], ["MAC2313"], ["PHY2048"], ["PHY2054"]], "additional": [["CHM1045"], ["CHM1046"], ["MAP2312"]]}, #chemistry is not lower division, but it is kept as lower division to prioritize physics, since after all, it is a physics major
    "business administration": {"groups": [["STA2023"], ["ECO2023"], ["ACG2001"], ["ACG2011", "ACG2021"], ["ACG2071"]], "additional": [["GEB1011"]]},
    "computer science": {"groups": [["MAC2312"], ["COP2800"], ["BSC2010", "CHM1045", "PHY2048", "ESC1000"], ["BSC2011", "CHM1046", "PHY2049"]], "additional": [["COP2805C"], ["MAD2104"]]},
    "political science": {"groups": [["INR2002"]], "additional": [["INR2440"], ["PHI1100"]]},
    "psychology": {"groups": [["PSY2012"], ["STA2023"], ["BSC1005", "BSC2010", "BSC2085"], ["DEP2000", "DEP2100", "INP2390", "SOP2772"]], "additional": [["ISS1301"]]},
    "english": {"groups": [["LIT2000"], ["PHI2010"], ["ENC2300"]], "additional": [["ENG2012"], ["CRW2001"], ["ENC2030"]]},
    "economics": {"groups": [["ECO2013"], ["ECO2023"], ["STA2023"]]},
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


def ask_choice(prompt: str, choices: List[str]) -> str:
    normalized = [choice.lower() for choice in choices]
    answer = input(prompt).strip().lower()
    while answer not in normalized:
        answer = input(f"Please choose one of: {', '.join(choices)}: ").strip().lower()
    return answer


def ask_yes_no(prompt: str) -> bool:
    answer = input(prompt).strip().lower()
    while answer not in ["yes", "y", "no", "n"]:
        answer = input("Please type yes or no: ").strip().lower()
    return answer in ["yes", "y"]


def ask_int(prompt: str, default: int = 0, allowed: Optional[Set[int]] = None) -> int:
    while True:
        raw = input(prompt).strip()
        try:
            value = int(raw)
        except ValueError:
            value = default
        if allowed is None or value in allowed:
            return value
        print(f"Please enter one of: {', '.join(str(v) for v in sorted(allowed))}")


def classes_needed_from_credits(credits: int) -> int:
    return 0 if credits <= 0 else max(1, math.ceil(credits / 3))


def is_summer_blocked(code: str) -> bool:
    course = all_courses[code]
    return code.startswith(SUMMER_BLOCKED_PREFIXES) or any(area in course.fulfills for area in ["Mathematics", "Natural Sciences"])


def group_satisfied(group: List[str], completed: Set[str]) -> bool:
    return any(code in completed for code in group)


def pick_group_course(group: List[str], completed: Set[str], locked: Set[str]) -> Optional[str]:
    if group_satisfied(group, completed):
        return None
    for code in group:
        if code in all_courses and code not in completed and code not in locked:
            return code
    return None


def ask_completed_courses(course_codes: List[str], heading: str, completed: Set[str]):
    available = []
    seen = set()
    for code in course_codes:
        if code in all_courses and code not in seen:
            available.append(code)
            seen.add(code)
    if not available:
        return
    print(f"\n--- {heading} ---")
    print("Type any course codes you have already completed, separated by commas.")
    for code in available:
        print(f"  {code}: {all_courses[code].name}")
    raw = input("Completed course codes (or none): ").strip().upper()
    if raw in ["", "NONE", "NO"]:
        return
    for code in [part.strip() for part in raw.split(",")]:
        if code in available:
            completed.add(code)
            print(f"  -> Marked {code} complete")
        elif code:
            print(f"  -> Skipped unknown/non-listed course code: {code}")


def apply_ap_math_credit(math_answer: str, completed: Set[str], locked: Set[str], senior_requires_bc_for_calc2: bool):
    if math_answer == "ap precalc":
        completed.update(["MAC1147"])
    elif math_answer == "ap calc ab":
        completed.update(["MAC1147", "MAC2311"])
        if senior_requires_bc_for_calc2:
            locked.add("MAC2312")
    elif math_answer == "ap calc bc":
        completed.update(["MAC1147", "MAC2311"])


def term_start_completed_for(semesters: List[str], junior_math: str) -> Dict[str, Set[str]]:
    # Legacy - we will override with more specific logic in the junior section
    return {sem: set() for sem in semesters}


def collect_general_requirements(status: str) -> Dict[str, int]:
    print("\n--- Remaining General AA Requirements ---")
    if status == "junior":
        print("Junior warning: leave English credits needed as 0 for now. Do not worry about English until your AP English score comes out.")
    print("Answer each area using the exact options shown. Oral Communication and Computer Competency are yes/no because they are one-course requirements.")
    needed: Dict[str, int] = {}
    for area, meta in GENERAL_REQUIREMENTS.items():
        if meta.get("yes_no"):
            needed[area] = 3 if ask_yes_no(meta["prompt"]) else 0
        else:
            needed[area] = ask_int(meta["prompt"], default=0, allowed=meta["allowed"])
    return needed


def add_candidate(candidates: Set[str], code: str, priority: int):
    if code in all_courses:
        candidates.add(code)
        all_courses[code].priority = max(all_courses[code].priority, priority)


def related_major_courses(major: str, focus_courses: List[str]) -> Set[str]:
    related = set(focus_courses)
    info = MAJOR_REQUIREMENTS.get(major, {"groups": [], "additional": []})
    for group in info["groups"] + info["additional"]:
        related.update(group)
    return related


def build_candidates(major: str, completed: Set[str], locked: Set[str], general_needed: Dict[str, int], required_by_ap: Set[str], focus_courses: List[str], required_by_policy: Optional[Set[str]] = None) -> Tuple[List[str], List[List[str]], List[Tuple[List[str], int]], bool]:
    candidates: Set[str] = set()
    required_groups: List[List[str]] = []
    capped_groups: List[Tuple[List[str], int]] = []
    required_by_policy = required_by_policy or set()
    major_related = related_major_courses(major, focus_courses)

    def add_prereqs_recursively(code: str, priority: int, depth: int = 0):
        if depth > 10 or code in completed or code in locked or code not in all_courses:
            return
        for prereq in all_courses[code].prereqs:
            add_prereqs_recursively(prereq, 600, depth + 1)
        add_candidate(candidates, code, priority)

    # 1. PRIORITY 10000: AP-required courses
    for code in required_by_ap:
        if code not in completed and code not in locked:
            add_candidate(candidates, code, 10000)
            required_groups.append([code])

    for code in required_by_policy:
        if code not in completed and code not in locked:
            add_candidate(candidates, code, 9500)
            required_groups.append([code])

    # 2. PRIORITY 700: Unfulfilled general requirements
    for area, credits in general_needed.items():
        if credits <= 0:
            continue
        needed_classes = classes_needed_from_credits(credits)
        area_courses = [code for code in GENERAL_REQUIREMENTS[area]["courses"] if code in all_courses and code not in completed and code not in locked]
        # Boost priority for English to ensure it gets scheduled even if it means dropping less important courses
        for code in area_courses:
            if area == "English":
                priority = 9000   # very high priority for English
            else:
                priority = 800 if code in major_related else 700
            add_candidate(candidates, code, priority)
        if area == "English":
            # For English, we need to enforce the exact number of courses needed (1 for 3 credits, 2 for 6)
            # We'll add each required course as a separate required group
            courses_to_take = area_courses[:needed_classes]
            for code in courses_to_take:
                required_groups.append([code])
        else:
            for _ in range(needed_classes):
                if area_courses:
                    required_groups.append(area_courses)
        general_only_courses = [code for code in area_courses if code not in major_related]
        if general_only_courses:
            capped_groups.append((general_only_courses, needed_classes))

    # 3. MAJOR REQUIREMENTS (core and additional)
    major_info = MAJOR_REQUIREMENTS[major]

    for group in major_info["groups"]:
        if group_satisfied(group, completed):
            continue
        available = [code for code in group if code in all_courses and code not in locked and code not in completed]
        if not available:
            continue
        required_groups.append(group)
        for code in available:
            add_prereqs_recursively(code, 600)

    for group in major_info["additional"]:
        if group_satisfied(group, completed):
            continue
        available = [code for code in group if code in all_courses and code not in locked and code not in completed]
        if not available:
            continue
        required_groups.append(group)
        for code in available:
            add_prereqs_recursively(code, 350)

    # 4. PRIORITY 180: Undecided focus courses ONLY
    if major == "undecided":
        for code in focus_courses:
            if code in all_courses and code not in completed and code not in locked:
                add_candidate(candidates, code, 180)

    return sorted(candidates), required_groups, capped_groups, not candidates


# ==================== NEW FUNCTION: Always add electives to fill minimum slots ====================
def add_electives_to_fill_slots(candidates: List[str], semesters: List[str], class_limits: Dict[str, Tuple[int, int]]) -> Tuple[List[str], bool]:
    """
    Add elective placeholders to ensure every semester meets its minimum class count.
    Returns updated candidate list and a flag indicating if any elective was added.
    """
    elective_codes = []
    for sem in semesters:
        min_classes, max_classes = class_limits[sem]
        # Add exactly min_classes electives per semester (they will only be used if needed)
        for i in range(min_classes):
            code = f"ELECTIVE_{sem.replace(' ', '_').upper()}_{i + 1}"
            if code not in candidates:
                all_courses[code] = Course("Elective Class*", workload=0, priority=50, allowed_terms=[sem], fulfills=["Elective"])
                elective_codes.append(code)
    # Combine with existing candidates
    updated_candidates = sorted(set(candidates).union(elective_codes))
    # Return True if any elective was added (so we can show the description later)
    return updated_candidates, len(elective_codes) > 0
# =================================================================================================


def create_schedule(candidates: List[str], required_groups: List[List[str]], capped_groups: List[Tuple[List[str], int]], semesters: List[str], class_limits: Dict[str, Tuple[int, int]], completed: Set[str], term_start_additions: Dict[str, Set[str]], locked: Set[str], max_workload: float):
    if not candidates:
        return {sem: [] for sem in semesters}

    prob = pulp.LpProblem("SAS_v9_schedule", pulp.LpMinimize)

    x = pulp.LpVariable.dicts("take", ((c, s) for c in candidates for s in semesters), cat="Binary")

    # Balancing variables
    required_count = len([c for c in candidates if not c.startswith("ELECTIVE_")])
    Y = len(semesters)
    if Y > 0 and required_count > 0:
        avg = required_count / Y
    else:
        avg = 0

    dev_pos = pulp.LpVariable.dicts("dev_pos", semesters, lowBound=0, cat='Continuous')
    dev_neg = pulp.LpVariable.dicts("dev_neg", semesters, lowBound=0, cat='Continuous')
    count_s = pulp.LpVariable.dicts("count_s", semesters, lowBound=0, cat='Integer')

    for s in semesters:
        prob += count_s[s] == pulp.lpSum(x[c, s] for c in candidates if not c.startswith("ELECTIVE_"))
        prob += count_s[s] - avg == dev_pos[s] - dev_neg[s]

    balancing_weight = 0.1

    # Increased multiplier (5 instead of 2) to favor earlier semesters for prerequisites
    priority_term = pulp.lpSum(x[c, s] * ((10000 - all_courses[c].priority) + semesters.index(s) * 5)
                               for c in candidates for s in semesters)
    balance_term = pulp.lpSum(dev_pos[s] + dev_neg[s] for s in semesters)
    prob += priority_term + balancing_weight * balance_term

    # Constraints
    for c in candidates:
        prob += pulp.lpSum(x[c, s] for s in semesters) <= 1
        allowed = all_courses[c].allowed_terms
        if allowed:
            for s in semesters:
                if s not in allowed:
                    prob += x[c, s] == 0

    for s in semesters:
        count = pulp.lpSum(all_courses[c].class_count * x[c, s] for c in candidates)
        work = pulp.lpSum(all_courses[c].workload * x[c, s] for c in candidates)
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

    # Adjacency for single-prerequisite courses
    academic_prev = {}
    for i, s in enumerate(semesters):
        prev = None
        for j in range(i-1, -1, -1):
            if "Summer" not in semesters[j]:
                prev = semesters[j]
                break
        academic_prev[s] = prev

    for c in candidates:
        if c.startswith("ELECTIVE_"):
            continue
        prereqs = all_courses[c].prereqs
        if len(prereqs) == 1:
            p = prereqs[0]
            if p in candidates and p not in completed and p not in locked:
                for t in semesters:
                    if "Summer" not in t:
                        prev_t = academic_prev[t]
                        if prev_t is not None:
                            prob += x[c, t] <= x[p, prev_t]

    # Existing prerequisite constraints
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
            for prereq in all_courses[c].prereqs:
                if prereq in available_before:
                    continue
                earlier_terms = semesters[:s_index]
                if prereq in candidates and earlier_terms:
                    prob += x[c, s] <= pulp.lpSum(x[prereq, t] for t in earlier_terms)
                else:
                    prob += x[c, s] == 0

    status_code = prob.solve(pulp.PULP_CBC_CMD(msg=False, timeLimit=30))
    if pulp.LpStatus[status_code] != "Optimal":
        print("Workload, class-count, or prerequisite limits blocked an optimal schedule. Using priority fallback...")
        return priority_fallback(candidates, capped_groups, semesters, class_limits, completed, term_start_additions, locked, max_workload)

    schedule = defaultdict(list)
    for c in candidates:
        for s in semesters:
            value = pulp.value(x[c, s])
            if value is not None and value > 0.5:
                schedule[s].append(c)
    return {sem: sorted(schedule[sem], key=lambda code: (-all_courses[code].priority, all_courses[code].name)) for sem in semesters}


def priority_fallback(candidates: List[str], capped_groups: List[Tuple[List[str], int]], semesters: List[str], class_limits: Dict[str, Tuple[int, int]], completed: Set[str], term_start_additions: Dict[str, Set[str]], locked: Set[str], max_workload: float):
    schedule = {sem: [] for sem in semesters}
    current_work = {sem: 0.0 for sem in semesters}
    done = set(completed)
    capped_lookup = {code: (set(group), max_count) for group, max_count in capped_groups for code in group}
    sorted_candidates = sorted(candidates, key=lambda code: all_courses[code].priority, reverse=True)
    for sem in semesters:
        done.update(term_start_additions.get(sem, set()))
        min_classes, max_classes = class_limits[sem]
        for code in sorted_candidates:
            if code in done or code in locked or code in schedule[sem]:
                continue
            course = all_courses[code]
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
                already_taken = sum(1 for classes in schedule.values() for scheduled_code in classes if scheduled_code in group)
                if already_taken >= max_count:
                    continue
            if all(prereq in done for prereq in course.prereqs):
                schedule[sem].append(code)
                current_work[sem] += course.workload
        done.update(schedule[sem])
        if len(schedule[sem]) < min_classes:
            print(f"Warning: only found {len(schedule[sem])} eligible classes for {sem}; requested at least {min_classes}.")
    return schedule


def print_schedule(schedule, major, status, max_workload, elective_note_needed):
    print("\n" + "=" * 75)
    print(f"YOUR PERSONALIZED SAS SCHEDULE ({major.upper()})")
    print(f"Max College Workload: {max_workload} hrs/week | Schedule for: {status.title()} Year")
    print("=" * 75)
    for sem, classes in schedule.items():
        print(f"\n{sem}")
        if not classes:
            print("  - No eligible classes found with the current constraints.")
        for code in classes:
            print(f"  - {all_courses[code].name}")
    print("\n" + "=" * 75)
    print("English replaces the old Communications label to avoid confusion.")
    print("Labs are bundled with their lecture and do not count as a separate class slot.")
    print("OR requirements only prioritize one option so the planner does not schedule duplicate equivalents.")
    print("AP Calc AB/BC can satisfy Calc 1 for majors that list MAC2311; senior Calc 2 still requires BC or completed Calc 1 progression.")
    if elective_note_needed:
        print("*Since you are finished with all of your required courses, you can choose your own elective. This can be either a higher division course for your major, a fun class you want to take to have fun, or a subject that you have interest in! The choice is yours.")
    print("=" * 75)


import streamlit as st
import pandas as pd


FUNCTION_WORDS = {
    "a", "an", "and", "as", "at", "but", "by", "for", "in", "nor", "of",
    "on", "or", "per", "the", "to", "with"
}


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
    course_name = all_courses[code].name
    if " - " not in course_name:
        return title_case_label(course_name)
    prefix, title = course_name.split(" - ", 1)
    return f"{prefix} - {title_case_label(title)}"


def major_course_options(major: str) -> List[str]:
    if major == "undecided":
        return []
    seen = set()
    options = []
    info = MAJOR_REQUIREMENTS[major]
    for group in info["groups"] + info["additional"]:
        for code in group:
            if code in all_courses and code not in seen:
                options.append(code)
                seen.add(code)
    return options


def transform_workload(user_hours):
    transformed = 4 + (user_hours - 5) * (5 / 3)  # slope ≈ 1.0667
    return round(min(transformed, 20), 1)

def get_course_fulfillment_label(code: str, major: str, general_needed: Dict[str, int], required_by_ap: Set[str]) -> str:
    course = all_courses[code]
    if code in required_by_ap:
        return "Required by AP Score"
    major_info = MAJOR_REQUIREMENTS.get(major, {})
    for group in major_info.get("groups", []):
        if code in group:
            return "Major Requirement"
    for group in major_info.get("additional", []):
        if code in group:
            return "Major Requirement"
    for area, credits in general_needed.items():
        if credits > 0 and code in GENERAL_REQUIREMENTS[area]["courses"]:
            return f"General Requirement: {area}"
    if "Elective" in course.fulfills:
        return "Elective"
    if course.fulfills:
        return course.fulfills[0]
    return "Additional Course"


AP_SOCIAL_CREDIT_COURSES = {"AMH2010", "AMH2020", "POS2041", "ECO2013"}


AP_CREDIT_MAP = {
    "AP Precalculus": {
        3: ["MAC1147"],
        4: ["MAC1147"],
        5: ["MAC1147"],
    },
    "AP Calculus AB": {
        3: ["MAC2311"],
        4: ["MAC2311"],
        5: ["MAC2311"],
    },
    "AP Calculus BC": {
        3: ["MAC2311"],
        4: ["MAC2311"],
        5: ["MAC2311"],
    },
    "AP English Literature": {
        3: ["ENC1101"],
        4: ["ENC1101", "ENC1102"],
        5: ["ENC1101", "ENC1102"],
    },
    "AP English Language": {
        3: ["ENC1101"],
        4: ["ENC1101", "ENC1102"],
        5: ["ENC1101", "ENC1102"],
    },
    "AP US History": {
        3: ["AMH2010"],
        4: ["AMH2010", "AMH2020"],
        5: ["AMH2010", "AMH2020"],
    },
    "AP Government": {
        3: ["POS2041"],
        4: ["POS2041"],
        5: ["POS2041"],
    },
    "AP Macroeconomics": {
        3: ["ECO2013"],
        4: ["ECO2013"],
        5: ["ECO2013"],
    },
    "AP Biology": {
        3: ["BSC1005"],
        4: ["BSC2010"],
        5: ["BSC2010", "BSC2011"],
    },
    "AP Chemistry": {
        3: ["CHM1045"],
        4: ["CHM1045"],
        5: ["CHM1045"],
    },
    "AP Physics 1": {
        3: ["PHY2053"],
        4: ["PHY2053"],
        5: ["PHY2053"],
    },
    "AP Physics 2": {
        3: ["PHY2054"],
        4: ["PHY2054"],
        5: ["PHY2054"],
    },
    "AP Physics C: Mechanics": {
        3: ["PHY2053"],
        4: ["PHY2048"],
        5: ["PHY2048"],
    },
    "AP Statistics": {
        3: ["STA2023"],
        4: ["STA2023"],
        5: ["STA2023"],
    },
    "AP Psychology": {
        3: ["PSY2012"],
        4: ["PSY2012"],
        5: ["PSY2012"],
    },
    "AP Art History": {
        3: ["ARH1000"],
        4: ["ARH1000", "ARH2051"],
        5: ["ARH1000", "ARH2051"],
    }
}

st.set_page_config(
    page_title="SAS Kendall AA Planner",
    layout="wide"
)

# --- SAS Official Site Styling ---
st.markdown(
    """
    <style>
    /* Global Reset & Fonts */
    html, body, [class*="css"] {
        font-family: 'Arial', 'Helvetica Neue', sans-serif !important;
        background-color: #f5f5f5;
        color: #333333;
    }
    .stApp {
        background: #f5f5f5;
    }

    /* Header */
    h1, h2, h3, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: #1a3b5c !important;
        font-family: 'Arial', 'Helvetica Neue', sans-serif !important;
        font-weight: 700;
    }

    /* Main Title */
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

    /* Accolades Banner */
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

    /* Card styling */
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

    /* Buttons */
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

    /* Select boxes and inputs */
    .stSelectbox, .stNumberInput, .stMultiSelect {
        background: white;
        border-radius: 8px;
    }
    .stSelectbox > div > div, .stNumberInput > div > div {
        border-radius: 8px !important;
        border-color: #d0d7df !important;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: #f8fafc !important;
        border-right: 1px solid #e8ecf0;
    }
    [data-testid="stSidebar"] .stMarkdown {
        color: #1a3b5c;
    }

    /* Course cards in calendar */
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

    /* Semester header */
    .semester-header {
        font-size: 1.3rem;
        font-weight: 700;
        color: #1a3b5c;
        margin-bottom: 0.75rem;
        padding-bottom: 0.25rem;
        border-bottom: 3px solid #1a3b5c;
        display: inline-block;
    }

    /* Notice box */
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

    /* Footer / Disclaimer */
    .footer-disclaimer {
        font-size: 0.8rem;
        color: #6a7a8a;
        border-top: 1px solid #e0e7ef;
        padding-top: 1.5rem;
        margin-top: 2rem;
        text-align: center;
    }

    /* Responsive tweaks */
    @media (max-width: 768px) {
        .main-title { font-size: 1.8rem; }
        .accolades-banner .badge { font-size: 0.7rem; padding: 0.15rem 0.6rem; }
        .sas-card { padding: 1rem; }
    }

    /* Hide default Streamlit elements we don't need */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Header with SAS Branding ---
st.markdown(
    """
    <div style="text-align: center; padding: 0.5rem 0 0.25rem 0;">
    </div>
    <div class="main-title">SAS Kendall AA Planner</div>
    <div class="sub-title">Interactive scheduling optimizer for School for Advanced Studies</div>
    """,
    unsafe_allow_html=True,
)

# --- Planner Description Box ---
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

# Main App 

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
        status = st.selectbox(
            "Plan Type",
            ["junior", "senior"],
            format_func=title_case_label
        )
    with col2:
        if status == "senior":
            term_choice = st.selectbox(
                "Semester Plan",
                ["fall", "spring", "both"],
                format_func=title_case_label
            )
        else:
            start_term = st.selectbox(
                "Start Plan From",
                ["fall", "spring", "summer"],
                format_func=title_case_label
            )
    st.markdown('</div>', unsafe_allow_html=True)

semesters = []
class_limits = {}

if status == "senior":
    # Build semester list
    if term_choice in ["fall", "both"]:
        semesters.append("Fall Senior")
    if term_choice in ["spring", "both"]:
        semesters.append("Spring Senior")
    # For each senior semester, let the user choose 3 or 4 classes
    for sem in semesters:
        count_choice = st.selectbox(
            f"Number of classes for {title_case_label(sem)}",
            [3, 4],
            key=sem
        )
        class_limits[sem] = (count_choice, count_choice)
else:
    # Junior path
    if start_term == "fall":
        semesters.extend(["Fall Junior", "Spring Junior"])
    elif start_term == "spring":
        semesters.append("Spring Junior")
    summer_amount = st.selectbox(
        "Summer Junior Classes",
        [0, 1, 2, 3, 4],
        help="Choose 0 if you do not want a summer class."
    )
    if start_term == "summer" or summer_amount > 0:
        semesters.append("Summer Junior")
    semesters.extend(["Fall Senior", "Spring Senior"])
    for sem in semesters:
        if sem == "Summer Junior":
            class_limits[sem] = (summer_amount, summer_amount)
        elif sem in ["Fall Junior", "Spring Junior"]:
            class_limits[sem] = (3, 3)
        else:  # senior semesters
            # For juniors, we also let them choose 3 or 4 for senior year
            count_choice = st.selectbox(
                f"Number of classes for {title_case_label(sem)}",
                [3, 4],
                key=sem
            )
            class_limits[sem] = (count_choice, count_choice)

st.subheader("SAS Context")

if any(sem.startswith("Fall") for sem in semesters):
    a_or_b_year = st.selectbox(
        "Upcoming Fall Year",
        ["A Year (APUSH + AP Lang)", "B Year (AP Gov + AP Macro + AP Lit)"]
    )
else:
    a_or_b_year = None



if status == "junior":
    col1, col2 = st.columns(2)
    with col1:
        took_mac1105 = st.selectbox(
            "Did You Already Take MAC1105 Before the Start of Junior Year? (Summer or Before)",
            ["No", "Yes"]
        )
    with col2:
        junior_math = st.selectbox(
            "Current/Planned Junior Math Class",
            ["AP Precalc", "AP Calc AB", "AP Calc BC"]
        )
    
    if took_mac1105 == "Yes":
        completed.add("MAC1105")
    elif "Fall Junior" in semesters:
        required_by_policy.add("MAC1105")
        all_courses["MAC1105"].allowed_terms = ["Fall Junior"]
    
    junior_math_key = junior_math.lower()
    term_start_additions = {sem: set() for sem in semesters}
    senior_sems = [s for s in semesters if "Senior" in s]
    
    if junior_math_key == "ap precalc":
        for sem in senior_sems:
            term_start_additions[sem].add("MAC1147")
        take_ab_next = st.selectbox(
            "Will you be taking AP Calculus AB next year (senior year)?",
            ["No", "Yes"]
        )
        if take_ab_next == "Yes":
            for sem in senior_sems:
                term_start_additions[sem].add("MAC2311")
            st.success("Courses requiring Calculus 1 (e.g., PHY2048) are now available in senior year.")
        locked_courses.add("MAC2312")
        
    elif junior_math_key == "ap calc ab":
        for sem in senior_sems:
            term_start_additions[sem].update(["MAC1147", "MAC2311"])
        take_bc_next = st.selectbox(
            "Will you be taking AP Calculus BC next year (senior year)?",
            ["No", "Yes"]
        )
        if take_bc_next == "Yes":
            calc2_unlocked = True
            all_courses["MAC2312"].allowed_terms = senior_sems
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
        senior_last_math = st.selectbox(
            "Math Class Taken Last Year",
            ["None", "AP Precalc", "AP Calc AB", "AP Calc BC"]
        )
    with col2:
        senior_current_math = st.selectbox(
            "Math Class You Are Taking Now",
            ["None", "AP Precalc", "AP Calc AB", "AP Calc BC"]
        )
    senior_math_values = {senior_last_math.lower(), senior_current_math.lower()}
    if "ap calc bc" in senior_math_values:
        apply_ap_math_credit("ap calc bc", completed, locked_courses, senior_requires_bc_for_calc2=False)
        calc2_unlocked = True
        st.success("AP Calc BC unlocks Calculus 2.")
    elif "ap calc ab" in senior_math_values:
        apply_ap_math_credit("ap calc ab", completed, locked_courses, senior_requires_bc_for_calc2=True)
        st.info("AP Calc AB satisfies Calc 1, but Calculus 2 stays locked unless BC is true.")
    elif "ap precalc" in senior_math_values:
        apply_ap_math_credit("ap precalc", completed, locked_courses, senior_requires_bc_for_calc2=True)
        locked_courses.add("MAC2312")
    else:
        locked_courses.add("MAC2312")

st.markdown('</div>', unsafe_allow_html=True)

# --- Notice Box (restyled) ---
st.markdown(
    """
    <div class="notice-box">
        <strong>Course Availability Notice</strong><br>
        • <strong>MAC 2311 (Calculus 1)</strong> is not available at SAS as it is taken as <strong>AP Calculus AB</strong> and will not appear in any generated schedule.<br>
        • <strong>MAC 2312 (Calculus 2)</strong> can only be scheduled if you are currently taking <strong>AP Calculus BC</strong>.<br>
        • <strong>PHY 2048 + L</strong> can be scheduled if taking <strong>AP Calculus AB</strong> path. Physics 2 still requires Physics 1 first.<br>
        • <strong>AMH2010, AMH2020, ECO2013, and POS2041</strong> are not available at SAS as they are taken as their <strong>AP</strong> equivalent.
    </div>
    """,
    unsafe_allow_html=True,
)

col1, col2 = st.columns(2)
with col1:
    major = st.selectbox(
        "Major",
        list(MAJOR_REQUIREMENTS.keys()),
        format_func=title_case_label
    )
with col2:
    real_hours = st.number_input(
        "How many hours/week do you realistically spend on college coursework?",
        min_value=5,
        max_value=20,
        value=10,
        help="Be honest! This determines how many classes you can handle each semester."
    )
st.markdown('</div>', unsafe_allow_html=True)

focus_courses = []
if major == "undecided":
    focus = st.selectbox(
        "Undecided Focus",
        ["none"] + sorted(SUBJECT_FOCUS.keys()),
        format_func=title_case_label
    )
    if focus != "none":
        focus_courses = SUBJECT_FOCUS[focus]

taking_physics_c = st.checkbox(
    "Are you currently taking AP Physics C: Mechanics at SAS?",
    help="Checking off this class will have 2 hours have been subtracted from your max coursework to account for its extra workload."
)
if taking_physics_c:
    completed.add("PHY2048")
    st.success("Physics with Calculus 1 (PHY2048) credit granted. You can now take PHY2049 without PHY2048.")

max_workload = transform_workload(real_hours)
if taking_physics_c:
    max_workload = max(1.0, max_workload - 2.0)

st.subheader("Completed Courses")

# --- 1. Major-specific completed courses (or focus courses for undecided) ---
if major == "undecided":
    # If a focus is selected, show its courses in a multiselect
    if focus_courses:
        completed_selection = st.multiselect(
            "Select completed courses from your focus area",
            options=focus_courses,
            format_func=display_course_name
        )
        completed.update(completed_selection)
    else:
        st.caption("No focus selected yet.")
else:
    major_completed_options = major_course_options(major)
    if major_completed_options:
        completed_selection = st.multiselect(
            "Select completed classes for your major",
            options=major_completed_options,
            format_func=display_course_name
        )
        completed.update(completed_selection)
    else:
        st.caption("No major-specific completed courses are needed for this major.")




# --- Show current completed list for transparency ---
if completed:
    st.caption(f"**Currently marked as completed:** {', '.join(sorted(completed))}")

# --- AP Scores Section ---
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
                score = st.selectbox(
                    f"{ap_name} Score",
                    [1, 2, 3, 4, 5],
                    key=f"ap_score_{ap_name}"
                )
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
                    # Override manual English input with AP score if applicable
                    if score >= 4:
                        # AP English gives credit for both ENC1101 and ENC1102
                        completed.update(["ENC1101", "ENC1102"])
                        english_credits_needed = 0
                        st.success("AP English covers both ENC1101 and ENC1102.")
                    elif score == 3:
                        # AP gives only ENC1101
                        completed.add("ENC1101")
                        english_credits_needed = 3  # still need ENC1102
                        st.info("AP English gives credit for ENC1101 only; you still need ENC1102.")
                    else:
                        # score 1 or 2, no credit
                        pass
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

# Final enforcement
locked_courses.update(PERMANENTLY_BLOCKED)
if calc2_unlocked:
    locked_courses.discard("MAC2312")
else:
    locked_courses.add("MAC2312")

# --- General Requirements ---
st.subheader("General Requirements")
st.caption("Use Academic Progress in MyMDC to check which general AA requirements you still need.")

general_needed = {}

for area, meta in GENERAL_REQUIREMENTS.items():
    if area == "English":
        if status == "senior":
            # Show a dropdown for seniors
            english_credits_needed = st.selectbox(
                "English credits still needed?",
                [0, 3, 6],
                key="english_credits",
                help="If you got a 3 or less in AP English. 3 means only ENC1102 is needed (score of 3); 6 means ENC1101 and ENC1102 are needed (score of 1 or 2)."
            )
            general_needed[area] = english_credits_needed
        else:
            # Juniors: keep 0 (will be handled via AP later)
            general_needed[area] = 0
        continue  # skip the standard yes/no or credits logic

    if meta.get("yes_no"):
        needed_label = st.selectbox(
            f"Still Need {title_case_label(area)}?",
            ["No", "Yes"],
            key=area
        )
        general_needed[area] = 3 if needed_label == "Yes" else 0
    else:
        general_needed[area] = st.selectbox(
            f"{title_case_label(area)} Credits Remaining",
            sorted(list(meta["allowed"])),
            key=area
        )

# --- Generate Button ---
run = st.button("Generate Schedule", use_container_width=True)

if run:
    for code in AP_SOCIAL_CREDIT_COURSES:
        if code in all_courses and code not in required_by_ap:
            all_courses[code].priority = -1000

    candidates, required_groups, capped_groups, all_done = build_candidates(
        major,
        completed,
        locked_courses,
        general_needed,
        required_by_ap,
        focus_courses,
        required_by_policy
    )

    # Add electives to fill minimum slots for EVERY semester
    candidates, elective_added = add_electives_to_fill_slots(
        candidates,
        semesters,
        class_limits
    )

    if not candidates:
        st.warning("No courses to schedule. Please check your completed courses and requirements.")
    else:
        schedule = create_schedule(
            candidates,
            required_groups,
            capped_groups,
            semesters,
            class_limits,
            completed,
            term_start_additions or {s: set() for s in semesters},
            locked_courses,
            max_workload
        )

# --- Check if workload constraint is binding ---
        workload_warning = False
        for sem, classes in schedule.items():
            total_work = sum(all_courses[code].workload for code in classes)
            if total_work >= 0.9 * max_workload:
                workload_warning = True
                break

        if workload_warning:
            st.warning(
                "**Possible Workload Limit Reached**\n\n"
                "Your schedule currently respects your reported available hours. "
                "It is possible that additional courses (or heavier ones) were not scheduled because they would exceed the workload limit you set. "
                "If you feel you can handle more, increase your weekly hours in the input above."
            )

        st.success("Schedule was created successfully")

        # Check if any elective was actually scheduled
        elective_scheduled = False
        for sem, classes in schedule.items():
            for code in classes:
                if "Elective" in all_courses[code].fulfills:
                    elective_scheduled = True
                    break
            if elective_scheduled:
                break

        if any(schedule.values()):
            st.subheader("Planned Schedule")
            calendar_columns = st.columns(len(schedule))
            for column, (sem, classes) in zip(calendar_columns, schedule.items()):
                with column:
                    st.markdown(f'<div class="semester-header">{title_case_label(sem)}</div>', unsafe_allow_html=True)
                    if not classes:
                        st.caption("No classes scheduled.")
                    for index, code in enumerate(classes, start=1):
                        course = all_courses[code]
                        fulfillment_label = get_course_fulfillment_label(code, major, general_needed, required_by_ap)
                        st.markdown(
                            f"""
                            <div class="course-card">
                                <div class="class-number">Class {index}</div>
                                <div class="course-name">{display_course_name(code)}</div>
                                <div class="course-label"><b>{fulfillment_label}</b></div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
        else:
            st.warning("No schedule found with the current requirements.")

        if elective_scheduled:
            st.info(
                "*All requirements appear complete. Electives were added. "
                "Since you are finished with all of your required courses, you can choose your own elective. "
                "This can be either a higher division course for your major, a fun class you want to take, "
                "or a subject that you have interest in! The choice is yours."
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


#debug stuff below


#coursework
#st.write("**Max workload:**", max_workload)
#for sem, classes in schedule.items():
#    total = sum(all_courses[code].workload for code in classes)
#    st.write(f"{sem} total workload: {total:.1f}  (courses: {[all_courses[c].workload for c in classes]})")