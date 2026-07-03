SAS AA Degree Planner

A Streamlit‑based interactive scheduling optimizer for students at School for Advanced Studies (SAS) Kendall/South Campus.  
It builds a personalized, semester‑by‑semester course plan that respects your major, completed courses, AP credits, prerequisite restrictions, and available study time.

Purpose

- Personalized - based on your major, progress, and weekly study hours.  
- Requirement‑driven - satisfies AA general education and major requirements.  
- Prerequisite‑aware - never suggests a course before its required previous courses.  
- Workload‑balanced - spreads courses evenly across semesters and avoids overloading you.  
- AP‑friendly - accounts for AP scores and allows flexible math placement.  

Features

- Plan types: Junior or Senior year tracks with flexible start terms (Fall, Spring, Summer).  
- Major selection: Choose from Engineering, Nursing, Biology, Business, Computer Science, Political Science, Psychology, or Undecided (with focus areas).  
- Manual course input: Mark completed courses, AP credits, and future AP plans.  
- Workload cap: Enter your realistic weekly hours – the algorithm adjusts course load accordingly.  
- Automatic electives: Empty slots are filled with elective placeholders (you choose the real class).  
- Clear calendar view: See your schedule semester by semester with color‑coded requirement labels.  

Deployment

The app is live on Streamlit Community Cloud at:  
https://saskendallplanner.streamlit.app/

No installation needed, just open the link and begin your planning.

How It Works (for the curious)

The planner uses a mixed‑integer linear programming (MILP) model built with the `pulp` library.

1. Inputs:
  - Your major and focus (if undecided).
  - Courses already taken (including AP credits).
  - Your average weekly study hours (5–20).
  - Your current/planned math class (AP Precalc, AB, or BC).

2. Candidate generation:
  - Required courses are extracted from your major’s requirement groups.
  - Unfulfilled general education requirements are added.
  - Prerequisite chains are recursively included.

3. Optimization:
  - Each course gets a "priority" score (AP requirements → major core → general ed → electives).
  - The solver distributes courses evenly across semesters while respecting:
  - Prerequisite order (with adjacency for sequential courses like Chem 1 -> Chem 2).
  - Semester class limits (3 or 4 per semester).
  - Workload cap (course weights are calibrated so harder courses consume more “hours”).

4. Output: A semester‑by‑semester schedule with course labels (e.g., “Major Requirement”, “General Requirement: Humanities”).

