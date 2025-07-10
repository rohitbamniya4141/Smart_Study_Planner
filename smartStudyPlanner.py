import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Smart Study Planner", layout="centered")
st.title("📘 Smart Study Planner")
st.subheader("🎓 Plan Smarter, Study Sharper")

# ----- Session Storage -----
if 'subjects' not in st.session_state:
    st.session_state.subjects = []
if 'daily_plan' not in st.session_state:
    st.session_state.daily_plan = {}
if 'progress_data' not in st.session_state:
    st.session_state.progress_data = {}

# ----- Input Form -----
with st.form("subject_form", clear_on_submit=True):
    st.markdown("### 📋 Add Subject Details")
    subject = st.text_input("Subject Name")
    hours = st.number_input("Total Study Hours", min_value=0.0)
    importance = st.slider("Importance (1–5)", 1, 5, 3)
    difficulty = st.slider("Difficulty (1–5)", 1, 5, 3)
    deadline = st.number_input("Deadline (in Days)", min_value=1)
    notes = st.text_area("Additional Notes", height=100)
    submitted = st.form_submit_button("➕ Add Subject")

    if submitted:
        st.session_state.subjects.append({
            'Subject': subject,
            'Total_Hours': hours,
            'Importance': importance,
            'Difficulty': difficulty,
            'Deadline': deadline,
            'Notes': notes
        })
        st.success(f"✅ Added subject: {subject}")

# ----- Display Added Subjects -----
if st.session_state.subjects:
    st.markdown("### 📂 Current Subjects")
    st.dataframe(pd.DataFrame(st.session_state.subjects))

# ----- Generate Plan -----
st.markdown("### 🧠 Generate Study Plan")
study_hours = st.number_input("Available Study Hours per Day", min_value=0.5, value=3.0)
generate_btn = st.button("🚀 Generate Plan")

if generate_btn:
    df = pd.DataFrame(st.session_state.subjects)
    max_day = df['Deadline'].max()
    df['Weight'] = df['Importance'] * 2 + df['Difficulty'] * 1.5 + (max_day - df['Deadline'])
    df['Total_Minutes'] = (df['Total_Hours'] * 60).astype(int)

    remaining = df.set_index('Subject')['Total_Minutes'].to_dict()
    deadlines = df.set_index('Subject')['Deadline'].to_dict()
    weight_map = df.set_index('Subject')['Weight'].to_dict()

    st.session_state.daily_plan = {f'Day {i+1}': [] for i in range(max_day)}
    st.session_state.progress_data = {sub: [] for sub in df['Subject']}
    total_minutes = int(study_hours * 60)

    for day in range(1, max_day+1):
        eligible = df[(df['Deadline'] >= day) & (df['Subject'].map(remaining) > 0)].copy()
        if eligible.empty: continue
        eligible['Days_Left'] = eligible['Subject'].map(deadlines) - (day - 1)
        eligible['Adj_Weight'] = eligible.apply(lambda r: weight_map[r['Subject']] / r['Days_Left'], axis=1)
        total_weight = eligible['Adj_Weight'].sum()

        plan = []
        for _, row in eligible.iterrows():
            sub = row['Subject']
            share = row['Adj_Weight'] / total_weight if total_weight else 0
            allocated = min(int(share * total_minutes), remaining[sub])
            if allocated > 0:
                plan.append((sub, allocated))
                remaining[sub] -= allocated

        for sub in st.session_state.progress_data:
            prev = st.session_state.progress_data[sub][-1] if st.session_state.progress_data[sub] else 0
            current = next((m for s, m in plan if s == sub), 0)
            st.session_state.progress_data[sub].append(prev + current)

        st.session_state.daily_plan[f'Day {day}'] = plan

    st.success("✅ Study plan generated successfully!")

# ----- Show Plan Output -----
if st.session_state.daily_plan:
    st.markdown("### 📅 Daily Study Schedule")
    for day, tasks in st.session_state.daily_plan.items():
        if tasks:
            st.write(f"**{day}**")
            for sub, mins in tasks:
                hrs, rem = divmod(mins, 60)
                st.write(f"- {sub}: {hrs}h {rem}m" if hrs else f"- {sub}: {rem} min")

# ----- Charts -----
if st.session_state.daily_plan and st.button("📊 Show Charts"):
    # Pie Chart
    st.markdown("#### 🥧 Time Allocation per Subject")
    subject_totals = {}
    for tasks in st.session_state.daily_plan.values():
        for sub, mins in tasks:
            subject_totals[sub] = subject_totals.get(sub, 0) + mins
    fig1, ax1 = plt.subplots()
    ax1.pie(subject_totals.values(), labels=subject_totals.keys(), autopct='%1.1f%%')
    ax1.axis('equal')
    st.pyplot(fig1)

    # Progress Chart
    st.markdown("#### 📈 Progress Chart")
    fig2, ax2 = plt.subplots()
    for sub, data in st.session_state.progress_data.items():
        ax2.plot(range(1, len(data)+1), data, label=sub)
    ax2.set_xlabel("Day")
    ax2.set_ylabel("Cumulative Minutes")
    ax2.set_title("Progress Over Time")
    ax2.legend()
    ax2.grid(True)
    st.pyplot(fig2)

# ----- Export CSV -----
if st.session_state.daily_plan:
    export_df = pd.DataFrame([
        [day, sub, mins]
        for day, tasks in st.session_state.daily_plan.items()
        for sub, mins in tasks
    ], columns=["Day", "Subject", "Minutes"])
    st.download_button("💾 Export Plan CSV", export_df.to_csv(index=False), file_name="study_plan.csv", mime="text/csv")
