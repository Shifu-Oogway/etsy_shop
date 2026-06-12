"""Detailed template library — 10 niches x 3 product types.

Each template is a complete, sellable structure. The builder agent merges the
LLM-generated spec ON TOP of these, so every product has a guaranteed detail
floor even when the model returns something thin.

Niche keys are matched fuzzily (case-insensitive substring), so
"Finance & Budgeting", "finance", and "budget planner" all hit FINANCE.
"""
from __future__ import annotations

from typing import Any

# ── PDF planner templates (pages -> sections) ─────────────────────────────────

PDF_TEMPLATES: dict[str, list[dict]] = {
    "finance": [
        {"title": "Monthly Budget Overview", "sections": ["Income Sources", "Fixed Expenses", "Variable Expenses", "Savings Allocation", "Net Balance"]},
        {"title": "Expense Tracker",          "sections": ["Date / Description / Category / Amount", "Weekly Subtotals", "Category Totals"]},
        {"title": "Savings Goals",            "sections": ["Goal Name & Target", "Monthly Contribution Plan", "Progress Milestones (25/50/75/100%)"]},
        {"title": "Debt Payoff Plan",         "sections": ["Debt List (Balance / Rate / Minimum)", "Snowball vs Avalanche Order", "Payment Schedule"]},
        {"title": "Bill Calendar",            "sections": ["Due Dates Grid", "Autopay Checklist", "Annual / Irregular Bills"]},
        {"title": "Monthly Review",           "sections": ["What Went Well", "Overspend Analysis", "Adjustments for Next Month"]},
    ],
    "health": [
        {"title": "Weekly Workout Plan",   "sections": ["Mon–Sun Training Split", "Exercise / Sets / Reps / Weight", "Rest Day Activities"]},
        {"title": "Habit Tracker",         "sections": ["Water Intake (8 circles/day)", "Sleep Hours", "Steps / Movement", "30-Day Grid"]},
        {"title": "Meal & Nutrition Log",  "sections": ["Breakfast / Lunch / Dinner / Snacks", "Energy Level Notes", "Grocery List"]},
        {"title": "Measurements & Progress", "sections": ["Weight / Body Measurements", "Progress Photos Checklist", "Monthly Comparison"]},
        {"title": "Wellness Check-in",     "sections": ["Mood Tracker", "Stress Level (1–10)", "Self-care Activities Done"]},
        {"title": "Goals & Rewards",       "sections": ["90-Day Goal", "Weekly Mini-goals", "Reward Milestones"]},
    ],
    "productivity": [
        {"title": "Daily Planner",        "sections": ["Top 3 Priorities", "Time-blocked Schedule (6am–10pm)", "Quick Tasks", "Notes & Ideas"]},
        {"title": "Weekly Overview",      "sections": ["Week's Theme / Focus", "Mon–Sun Key Tasks", "Appointments", "Weekly Wins"]},
        {"title": "Project Tracker",      "sections": ["Project / Deadline / Status", "Next Actions", "Waiting On", "Blocked Items"]},
        {"title": "Goal Breakdown",       "sections": ["Quarterly Goal", "Monthly Milestones", "Weekly Actions", "Daily Habits"]},
        {"title": "Brain Dump",           "sections": ["Everything On My Mind", "Sort: Do / Delegate / Defer / Delete"]},
        {"title": "Weekly Review",        "sections": ["Completed This Week", "Carried Over", "Lessons Learned", "Next Week Setup"]},
    ],
    "business": [
        {"title": "Client Tracker",        "sections": ["Client / Project / Rate / Status", "Onboarding Checklist", "Contact Log"]},
        {"title": "Invoice Log",           "sections": ["Invoice # / Client / Amount / Due / Paid", "Outstanding Balance", "Monthly Revenue Total"]},
        {"title": "Weekly Business Plan",  "sections": ["Revenue Goal", "Client Work Blocks", "Marketing Tasks", "Admin Tasks"]},
        {"title": "Lead Pipeline",         "sections": ["Lead / Source / Stage / Value", "Follow-up Dates", "Conversion Notes"]},
        {"title": "Expense & Tax Tracker", "sections": ["Business Expenses by Category", "Mileage Log", "Quarterly Tax Estimates"]},
        {"title": "Quarterly Review",      "sections": ["Revenue vs Goal", "Best Clients / Projects", "What to Stop / Start / Continue"]},
    ],
    "wedding": [
        {"title": "Master Checklist",      "sections": ["12+ Months Out", "9–6 Months", "3 Months", "Final Month", "Week Of", "Day Of"]},
        {"title": "Budget Tracker",        "sections": ["Category / Budgeted / Actual / Deposit Paid", "Payment Due Dates", "Running Total"]},
        {"title": "Guest List Manager",    "sections": ["Name / Party Size / RSVP / Meal Choice", "Table Assignments", "Thank-you Card Tracker"]},
        {"title": "Vendor Contacts",       "sections": ["Vendor / Service / Contact / Contract Status", "Payment Schedule", "Day-of Phone List"]},
        {"title": "Day-of Timeline",       "sections": ["Hour-by-hour Schedule", "Wedding Party Duties", "Emergency Kit Checklist"]},
        {"title": "Honeymoon Planner",     "sections": ["Destination Shortlist", "Booking Checklist", "Packing List"]},
    ],
    "student": [
        {"title": "Semester Overview",   "sections": ["Course / Professor / Credits / Schedule", "Important Dates", "Grade Goals"]},
        {"title": "Assignment Tracker",  "sections": ["Course / Assignment / Due / Status / Grade", "This Week's Deadlines"]},
        {"title": "Study Planner",       "sections": ["Exam Date & Topics", "Study Session Blocks", "Practice Test Scores"]},
        {"title": "Class Notes Template", "sections": ["Key Concepts", "Definitions", "Questions to Ask", "Summary"]},
        {"title": "GPA Calculator Sheet", "sections": ["Course / Credits / Grade / Points", "Semester GPA", "Cumulative GPA"]},
        {"title": "Weekly Schedule",     "sections": ["Class Blocks", "Study Blocks", "Work / Activities", "Free Time"]},
    ],
    "travel": [
        {"title": "Trip Overview",      "sections": ["Destination / Dates / Travelers", "Budget Summary", "Booking Confirmations"]},
        {"title": "Itinerary Planner",  "sections": ["Day-by-day Schedule", "Must-see List", "Restaurant Reservations", "Backup Rainy-day Plans"]},
        {"title": "Packing Checklist",  "sections": ["Clothing (by day count)", "Toiletries", "Tech & Chargers", "Documents", "Medications"]},
        {"title": "Budget Tracker",     "sections": ["Flights / Lodging / Food / Activities / Transport", "Daily Spending Log", "Currency Notes"]},
        {"title": "Travel Documents",   "sections": ["Passport / Visa Checklist", "Insurance Info", "Emergency Contacts", "Embassy Address"]},
        {"title": "Trip Journal",       "sections": ["Daily Highlights", "Favorite Meals", "People Met", "Photos to Print"]},
    ],
    "meal": [
        {"title": "Weekly Meal Plan",     "sections": ["Mon–Sun: Breakfast / Lunch / Dinner", "Prep-ahead Notes", "Leftover Plan"]},
        {"title": "Grocery List",         "sections": ["Produce", "Protein", "Dairy", "Pantry", "Frozen", "Household"]},
        {"title": "Recipe Cards",         "sections": ["Ingredients", "Steps", "Prep / Cook Time", "Serves / Notes"]},
        {"title": "Pantry Inventory",     "sections": ["Item / Quantity / Expiry", "Running Low List", "Freezer Contents"]},
        {"title": "Meal Prep Sunday",     "sections": ["Batch Cook List", "Container Plan", "Prep Order & Timing"]},
        {"title": "Budget & Waste Log",   "sections": ["Weekly Grocery Spend", "Eating Out Spend", "Food Wasted (reduce next week)"]},
    ],
    "real estate": [
        {"title": "Property Comparison",   "sections": ["Address / Price / Beds / Baths / Sqft", "Pros & Cons", "Score (1–10)"]},
        {"title": "Viewing Checklist",     "sections": ["Roof / Foundation / Plumbing / Electrical", "Neighborhood Notes", "Questions for Agent"]},
        {"title": "Mortgage Calculator",   "sections": ["Price / Down Payment / Rate / Term", "Monthly Payment Breakdown", "Closing Costs Estimate"]},
        {"title": "Moving Planner",        "sections": ["8 Weeks Out", "4 Weeks", "Moving Week", "Utilities Transfer Checklist"]},
        {"title": "Renovation Budget",     "sections": ["Room / Project / Quote / Actual", "Contractor Contacts", "Priority Order"]},
        {"title": "Home Maintenance Log",  "sections": ["Monthly Tasks", "Seasonal Tasks", "Service History / Warranties"]},
    ],
    "content": [
        {"title": "Content Calendar",     "sections": ["Date / Platform / Topic / Status", "Posting Schedule", "Key Dates & Trends"]},
        {"title": "Idea Bank",            "sections": ["Content Ideas List", "Hook Ideas", "Trending Audio / Formats", "Repurposing Map"]},
        {"title": "Video / Post Planner", "sections": ["Hook", "Main Points", "Call-to-action", "Hashtags / SEO Keywords"]},
        {"title": "Analytics Tracker",    "sections": ["Post / Views / Likes / Shares / Saves", "Follower Growth", "Best Performing Content"]},
        {"title": "Brand Collab Tracker", "sections": ["Brand / Contact / Rate / Deliverables / Deadline", "Invoice Status", "Media Kit Checklist"]},
        {"title": "Monthly Review",       "sections": ["Growth Numbers", "What Worked", "Content to Double Down On", "Next Month's Focus"]},
    ],
}

# ── Excel templates (sheets -> headers) ───────────────────────────────────────

EXCEL_TEMPLATES: dict[str, list[dict]] = {
    "finance": [
        {"name": "Dashboard",      "headers": ["Month", "Income", "Expenses", "Savings", "Net", "Savings Rate %"]},
        {"name": "Income",         "headers": ["Date", "Source", "Category", "Amount", "Recurring?", "Notes"]},
        {"name": "Expenses",       "headers": ["Date", "Description", "Category", "Amount", "Payment Method", "Essential?"]},
        {"name": "Savings Goals",  "headers": ["Goal", "Target Amount", "Saved So Far", "Monthly Contribution", "Target Date", "% Complete"]},
        {"name": "Debt Tracker",   "headers": ["Debt Name", "Balance", "Interest Rate", "Minimum Payment", "Extra Payment", "Payoff Date"]},
    ],
    "health": [
        {"name": "Workout Log",    "headers": ["Date", "Exercise", "Sets", "Reps", "Weight", "RPE", "Notes"]},
        {"name": "Habit Tracker",  "headers": ["Date", "Water (glasses)", "Sleep (hrs)", "Steps", "Workout Done?", "Mood (1-10)"]},
        {"name": "Nutrition",      "headers": ["Date", "Meal", "Food", "Calories", "Protein (g)", "Carbs (g)", "Fat (g)"]},
        {"name": "Measurements",   "headers": ["Date", "Weight", "Chest", "Waist", "Hips", "Arms", "Notes"]},
    ],
    "productivity": [
        {"name": "Task Master",    "headers": ["Task", "Project", "Priority", "Due Date", "Status", "Time Estimate", "Done?"]},
        {"name": "Projects",       "headers": ["Project", "Goal", "Deadline", "Status", "Next Action", "% Complete"]},
        {"name": "Time Log",       "headers": ["Date", "Activity", "Start", "End", "Duration", "Category", "Productive?"]},
        {"name": "Weekly Review",  "headers": ["Week", "Wins", "Challenges", "Carried Over", "Next Week Focus"]},
    ],
    "business": [
        {"name": "Clients",        "headers": ["Client", "Contact", "Email", "Project", "Rate", "Status", "Start Date"]},
        {"name": "Invoices",       "headers": ["Invoice #", "Client", "Issue Date", "Due Date", "Amount", "Status", "Paid Date"]},
        {"name": "Leads",          "headers": ["Lead", "Source", "Stage", "Est. Value", "Last Contact", "Next Follow-up"]},
        {"name": "Expenses",       "headers": ["Date", "Vendor", "Category", "Amount", "Tax Deductible?", "Receipt?"]},
        {"name": "P&L",            "headers": ["Month", "Revenue", "Expenses", "Profit", "Margin %"]},
    ],
    "wedding": [
        {"name": "Budget",         "headers": ["Category", "Item", "Budgeted", "Actual", "Deposit Paid", "Balance Due", "Due Date"]},
        {"name": "Guest List",     "headers": ["Name", "Party Size", "Invite Sent?", "RSVP", "Meal Choice", "Table #", "Thank You Sent?"]},
        {"name": "Vendors",        "headers": ["Vendor", "Service", "Contact", "Quote", "Contract Signed?", "Final Payment Due"]},
        {"name": "Timeline",       "headers": ["Time", "Event", "Location", "Who's Responsible", "Notes"]},
    ],
    "student": [
        {"name": "Assignments",    "headers": ["Course", "Assignment", "Due Date", "Status", "Grade", "Weight %"]},
        {"name": "Grade Calculator","headers": ["Course", "Credits", "Current Grade", "Grade Points", "Target Grade"]},
        {"name": "Study Schedule", "headers": ["Date", "Course", "Topic", "Duration", "Method", "Done?"]},
        {"name": "Exam Prep",      "headers": ["Exam", "Date", "Topics", "Practice Score 1", "Practice Score 2", "Confidence (1-10)"]},
    ],
    "travel": [
        {"name": "Itinerary",      "headers": ["Day", "Date", "Morning", "Afternoon", "Evening", "Reservations"]},
        {"name": "Budget",         "headers": ["Category", "Budgeted", "Spent", "Remaining", "Currency", "Notes"]},
        {"name": "Bookings",       "headers": ["Type", "Provider", "Confirmation #", "Date", "Cost", "Cancellation Policy"]},
        {"name": "Packing List",   "headers": ["Item", "Category", "Quantity", "Packed?", "Notes"]},
    ],
    "meal": [
        {"name": "Meal Plan",      "headers": ["Day", "Breakfast", "Lunch", "Dinner", "Snacks", "Prep Notes"]},
        {"name": "Grocery List",   "headers": ["Item", "Category", "Quantity", "Est. Cost", "Store", "Bought?"]},
        {"name": "Recipes",        "headers": ["Recipe", "Cuisine", "Prep Time", "Cook Time", "Servings", "Rating", "Link/Page"]},
        {"name": "Pantry",         "headers": ["Item", "Location", "Quantity", "Expiry Date", "Running Low?"]},
    ],
    "real estate": [
        {"name": "Properties",     "headers": ["Address", "Price", "Beds", "Baths", "Sqft", "$/Sqft", "Score", "Status"]},
        {"name": "Mortgage Calc",  "headers": ["Scenario", "Price", "Down %", "Rate", "Term", "Monthly Payment", "Total Interest"]},
        {"name": "Viewing Notes",  "headers": ["Address", "Date Viewed", "Condition", "Pros", "Cons", "Follow Up?"]},
        {"name": "Moving Tasks",   "headers": ["Task", "Category", "Deadline", "Assigned To", "Done?"]},
    ],
    "content": [
        {"name": "Content Calendar","headers": ["Date", "Platform", "Topic", "Format", "Status", "Link", "Pillar"]},
        {"name": "Ideas",          "headers": ["Idea", "Platform", "Hook", "Effort (1-5)", "Potential (1-5)", "Used?"]},
        {"name": "Analytics",      "headers": ["Date", "Post", "Platform", "Views", "Likes", "Comments", "Shares", "Saves"]},
        {"name": "Collabs",        "headers": ["Brand", "Contact", "Rate", "Deliverables", "Deadline", "Invoice Sent?", "Paid?"]},
    ],
}

# ── Notion templates (blocks -> heading + content) ────────────────────────────

NOTION_TEMPLATES: dict[str, list[dict]] = {
    "finance": [
        {"heading": "💰 Money Dashboard",   "content": "Track your complete financial picture: monthly income, expenses by category, and savings rate at a glance."},
        {"heading": "📊 Budget Tracker",    "content": "Log every expense with date, category, and amount. Linked database rolls up to monthly category totals."},
        {"heading": "🎯 Savings Goals",     "content": "Track each goal with target amount, deadline, and progress bar. Celebrate milestones at 25/50/75/100%."},
        {"heading": "💳 Debt Payoff",       "content": "List all debts with balance, rate, and minimum payment. Track payoff order and record extra payments."},
        {"heading": "📅 Bill Calendar",     "content": "Recurring bills database with due dates, autopay status, and amount. Calendar view shows what's due this week."},
        {"heading": "📈 Monthly Review",    "content": "Reflect: what went well, where you overspent, and one change for next month."},
    ],
    "health": [
        {"heading": "🏋️ Workout Library",  "content": "Database of exercises with muscle group, equipment, and video links. Build workouts by linking exercises."},
        {"heading": "📆 Training Log",      "content": "Track each session: exercises, sets, reps, weight, and how it felt. Weekly gallery view shows consistency."},
        {"heading": "✅ Habit Tracker",     "content": "Daily habits with checkbox properties: water, sleep, steps, workout, vitamins. Weekly progress rollup."},
        {"heading": "🍎 Meal Log",          "content": "Log meals with photos, energy ratings, and notes. Spot patterns between food and how you feel."},
        {"heading": "📏 Progress Tracker",  "content": "Weight, measurements, and progress photos in a timeline. Monthly comparison table."},
        {"heading": "🧘 Wellness Check-in", "content": "Weekly reflection: mood trends, stress level, self-care done, and one thing to improve."},
    ],
    "productivity": [
        {"heading": "🎯 Goal Hub",          "content": "Yearly goals broken into quarterly milestones, monthly targets, and weekly actions — all linked."},
        {"heading": "📋 Task Manager",      "content": "GTD-style task database: inbox, next actions, waiting-on, and someday/maybe. Filter by context and energy."},
        {"heading": "📅 Weekly Planner",    "content": "Time-blocked week template with top 3 priorities, scheduled deep work, and buffer time."},
        {"heading": "📁 Project Tracker",   "content": "Each project gets a page: goal, deadline, next action, linked tasks, and status."},
        {"heading": "🧠 Second Brain",      "content": "Capture notes, ideas, and resources. Tag by topic and link to related projects."},
        {"heading": "🔄 Weekly Review",     "content": "Template: review completed tasks, process inbox to zero, plan next week's priorities."},
    ],
    "business": [
        {"heading": "🏢 Business HQ",       "content": "Central dashboard linking clients, projects, invoices, and this month's revenue."},
        {"heading": "👥 Client CRM",        "content": "Client database: contact info, project history, rates, communication log, and status."},
        {"heading": "💵 Invoice Tracker",   "content": "Track every invoice: amount, due date, status. Overdue view chases late payments."},
        {"heading": "🚀 Lead Pipeline",     "content": "Kanban board: New → Contacted → Proposal → Won/Lost. Track value and follow-up dates."},
        {"heading": "🧾 Expense Log",       "content": "Business expenses with category, receipt photo, and tax-deductible flag. Quarterly rollup for taxes."},
        {"heading": "📊 Quarterly Review",  "content": "Revenue vs goal, best clients, time analysis, and strategic decisions: stop / start / continue."},
    ],
    "wedding": [
        {"heading": "💍 Wedding HQ",        "content": "Master dashboard: countdown, budget status, RSVP count, and next 5 tasks across all checklists."},
        {"heading": "✅ Master Checklist",  "content": "Timeline-based tasks from 12 months out to the day of. Check off as you go; progress bar per phase."},
        {"heading": "💰 Budget Tracker",    "content": "Every category: budgeted vs actual, deposits paid, balances due with dates. Total tracker at top."},
        {"heading": "👥 Guest Manager",     "content": "Guest database: party size, RSVP status, meal choice, table assignment, and thank-you card tracking."},
        {"heading": "📇 Vendor Directory",  "content": "Each vendor: contact, contract status, payment schedule, and day-of contact sheet."},
        {"heading": "⏰ Day-of Timeline",   "content": "Hour-by-hour schedule from hair & makeup to last dance. Share view with wedding party."},
    ],
    "student": [
        {"heading": "🎓 Semester Hub",      "content": "Dashboard: all courses, this week's deadlines, upcoming exams, and current GPA."},
        {"heading": "📚 Course Pages",      "content": "Each course: syllabus, schedule, professor contact, linked assignments and notes."},
        {"heading": "📝 Assignment Tracker", "content": "All assignments: course, due date, status, grade. Calendar view prevents deadline surprises."},
        {"heading": "🧠 Smart Notes",       "content": "Cornell-style note template with cue column, summary, and tags. Linked to courses and exams."},
        {"heading": "📖 Exam Prep",         "content": "Per exam: topic checklist, study sessions scheduled, practice scores, and confidence rating."},
        {"heading": "📊 Grade Calculator",  "content": "Track grades by weight; calculates current standing and what you need on the final."},
    ],
    "travel": [
        {"heading": "✈️ Trip Dashboard",    "content": "Overview: destination, dates, countdown, budget status, and booking confirmations in one place."},
        {"heading": "🗓 Itinerary",         "content": "Day-by-day plan: morning / afternoon / evening, with maps links and reservation details."},
        {"heading": "🧳 Packing List",      "content": "Categorized checklist that scales with trip length. Templates for beach, city, and hiking trips."},
        {"heading": "💵 Budget Tracker",    "content": "Planned vs actual by category. Daily spending log with currency conversion notes."},
        {"heading": "📑 Documents Vault",   "content": "Passport details, insurance, embassy contacts, and booking confirmations — accessible offline."},
        {"heading": "📔 Travel Journal",    "content": "Daily template: highlights, meals, people met, and photos to remember."},
    ],
    "meal": [
        {"heading": "🍽 Meal Planning Hub", "content": "Weekly board: drag recipes onto days. Auto-links to grocery list and prep schedule."},
        {"heading": "📖 Recipe Box",        "content": "Recipe database: ingredients, steps, time, rating, and tags (quick / batch / freezer-friendly)."},
        {"heading": "🛒 Smart Grocery List","content": "Generated from the week's meals, organized by store section. Check off while shopping."},
        {"heading": "🥫 Pantry Inventory",  "content": "What you have, where it is, and when it expires. 'Running low' view feeds the grocery list."},
        {"heading": "👨‍🍳 Prep Day Plan",    "content": "Sunday batch-cooking: what to make, container plan, and order of operations."},
        {"heading": "💰 Food Budget",       "content": "Weekly grocery + eating-out spend. Track food waste to cut costs."},
    ],
    "real estate": [
        {"heading": "🏠 House Hunt HQ",     "content": "Dashboard: properties viewed, shortlist, budget range, and next viewings."},
        {"heading": "🔍 Property Database", "content": "Each property: photos, specs, price history, commute times, pros/cons, and score."},
        {"heading": "📋 Viewing Checklist", "content": "Structural, electrical, plumbing, neighborhood checks — fill in during each viewing."},
        {"heading": "🧮 Mortgage Scenarios","content": "Compare loan scenarios: down payment, rate, term, monthly payment, total interest."},
        {"heading": "📦 Moving Planner",    "content": "8-week countdown: utilities, address changes, packing by room, moving day logistics."},
        {"heading": "🔧 Home Maintenance",  "content": "Post-move: seasonal maintenance calendar, service history, warranty tracker."},
    ],
    "content": [
        {"heading": "🎬 Creator Studio",    "content": "Dashboard: content calendar, ideas pipeline, this week's posts, and growth stats."},
        {"heading": "📅 Content Calendar",  "content": "Plan posts across platforms: topic, format, status (idea → drafted → scheduled → posted)."},
        {"heading": "💡 Idea Bank",         "content": "Capture every idea with hook, platform fit, and effort/potential scores. Never run dry."},
        {"heading": "✍️ Post Templates",    "content": "Proven structures: hook formulas, story arcs, CTA endings, and hashtag sets per platform."},
        {"heading": "📊 Analytics Tracker", "content": "Weekly numbers: views, engagement, follower growth. Identify your top 20% content."},
        {"heading": "🤝 Brand Collabs",     "content": "Pipeline: pitched → negotiating → contracted → delivered → paid. Media kit checklist included."},
    ],
}

# ── Fuzzy niche matching ──────────────────────────────────────────────────────

_NICHE_ALIASES = {
    "finance":      ["finance", "budget", "money", "saving", "debt", "invest"],
    "health":       ["health", "fitness", "workout", "gym", "wellness", "habit"],
    "productivity": ["productivity", "planner", "organization", "time", "goal"],
    "business":     ["business", "freelance", "entrepreneur", "small business", "client"],
    "wedding":      ["wedding", "event", "party", "bride", "engagement"],
    "student":      ["student", "education", "school", "college", "study", "academic"],
    "travel":       ["travel", "trip", "vacation", "itinerary", "adventure"],
    "meal":         ["meal", "food", "recipe", "cooking", "grocery", "kitchen", "nutrition"],
    "real estate":  ["real estate", "home", "house", "property", "moving", "mortgage"],
    "content":      ["content", "creator", "social media", "youtube", "instagram", "tiktok", "influencer"],
}


def match_niche(niche: str | None) -> str:
    """Fuzzy-match a niche string to a template key. Defaults to productivity."""
    if not niche:
        return "productivity"
    n = niche.lower()
    for key, aliases in _NICHE_ALIASES.items():
        if any(a in n for a in aliases):
            return key
    return "productivity"


def get_template(product_type: str, niche: str | None) -> dict[str, Any]:
    """Returns the detailed base template for a product type + niche."""
    key = match_niche(niche)
    if product_type == "pdf_planner":
        return {"pages": [dict(p) for p in PDF_TEMPLATES[key]]}
    if product_type == "excel_template":
        return {"sheets": [dict(s) for s in EXCEL_TEMPLATES[key]]}
    if product_type == "notion_template":
        return {"blocks": [dict(b) for b in NOTION_TEMPLATES[key]]}
    return {}


def merge_spec(product_type: str, niche: str | None,
               llm_spec: dict[str, Any]) -> dict[str, Any]:
    """Merge the LLM spec on top of the library template.

    Rule: if the LLM spec has MORE detail than the library floor, use it;
    otherwise extend it with library items it's missing. The result always
    meets the library's detail floor.
    """
    base = get_template(product_type, niche)
    merged = dict(llm_spec)

    key_map = {"pdf_planner": "pages", "excel_template": "sheets",
               "notion_template": "blocks"}
    items_key = key_map.get(product_type)
    if not items_key:
        return merged

    llm_items  = merged.get(items_key) or []
    base_items = base.get(items_key) or []

    # Titles/names already present in LLM output (case-insensitive)
    def item_name(it: dict) -> str:
        return str(it.get("title") or it.get("name") or it.get("heading") or "").lower()

    have = {item_name(it) for it in llm_items}

    # Append library items the LLM didn't cover, until we reach the floor count
    floor = len(base_items)
    for b in base_items:
        if len(llm_items) >= floor and len(llm_items) >= 4:
            break
        if item_name(b) not in have:
            llm_items.append(b)
            have.add(item_name(b))

    merged[items_key] = llm_items
    return merged
