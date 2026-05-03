from flask import Flask, render_template, request, redirect
from db import init_db, get_connection
from datetime import datetime, timedelta

app = Flask(__name__)
init_db()


@app.route("/")
def home():
    conn = get_connection()
    today = datetime.now().date().isoformat()
    habits = conn.execute("SELECT * FROM habits").fetchall()
    today_values = {}
    for h in habits:
        result = conn.execute(
            "SELECT COALESCE(SUM(value), 0), COUNT(*) FROM habit_logs WHERE habit_id=? AND DATE(logged_at)=?",
            (h[0], today)
        ).fetchone()
        today_values[h[0]] = {'sum': result[0], 'count': result[1]}
    # pass today_values=today_values to render_template (remove today_counts)
    conn.close()
    return render_template("index.html", habits=habits, today_values=today_values)


@app.route("/add", methods=['POST'])
def add_habit():
    habit_name = request.form['habit_name']
    habit_type = request.form.get('habit_type', 'good')
    habit_icon = request.form.get('habit_icon', '⭐')
    conn = get_connection()
    cursor = conn.cursor()
    log_type = request.form.get('log_type', 'boolean')
    # and add it to the INSERT:
    cursor.execute(
        "INSERT INTO habits (name, created_at, type, icon, log_type) VALUES (?, ?, ?, ?, ?)",
        (habit_name, datetime.now().isoformat(), habit_type, habit_icon, log_type)
    )
    conn.commit()
    conn.close()
    return redirect("/")


@app.route("/delete/<int:habit_id>", methods=['POST'])
def delete_habit(habit_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM habit_logs WHERE habit_id = ?", (habit_id,))
    cursor.execute("DELETE FROM habits WHERE id=?", (habit_id,))
    conn.commit()
    conn.close()
    return redirect("/habits")


@app.route("/profile")
def profile():
    conn = get_connection()
    cursor = conn.cursor()

    habit_count = cursor.execute("SELECT COUNT(*) FROM habits").fetchone()[0]
    total_logs_ever = cursor.execute("SELECT COUNT(*) FROM habit_logs").fetchone()[0]
    earliest_row = cursor.execute("SELECT MIN(created_at) FROM habits").fetchone()[0]
    earliest_date = earliest_row[:10] if earliest_row else "—"

    consistent_habit = cursor.execute(
        "SELECT name FROM habits JOIN habit_logs ON habits.id = habit_logs.habit_id "
        "GROUP BY habit_id ORDER BY COUNT(*) DESC LIMIT 1"
    ).fetchone()

    good_count = cursor.execute("SELECT COUNT(*) FROM habits WHERE type='good'").fetchone()[0]
    bad_count  = cursor.execute("SELECT COUNT(*) FROM habits WHERE type='bad'").fetchone()[0]

    prof = cursor.execute("SELECT * FROM profile WHERE id=1").fetchone()
    conn.close()

    return render_template("profile.html",
                           habit_count=habit_count,
                           total_logs_ever=total_logs_ever,
                           earliest_date=earliest_date,
                           consistent_habit=consistent_habit,
                           good_count=good_count,
                           bad_count=bad_count,
                           prof=prof)


@app.route("/update_profile", methods=['POST'])
def update_profile():
    name = request.form.get('name', 'Habit Hero').strip() or 'Habit Hero'
    pic  = request.form.get('pic', '')
    conn = get_connection()
    conn.execute("UPDATE profile SET name=?, pic=? WHERE id=1", (name, pic))
    conn.commit()
    conn.close()
    return redirect("/profile")


@app.route("/log/<int:habit_id>", methods=['POST'])
def log_habit(habit_id):
    value = float(request.form.get('value', 1))
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO habit_logs (logged_at, habit_id, value) VALUES (?, ?, ?)",
        (datetime.now().isoformat(), habit_id, value)
    )
    conn.commit()
    conn.close()
    return redirect("/")


@app.route("/edit/<int:habit_id>", methods=['POST'])
def edit_habit(habit_id):
    new_name   = request.form['new_name']
    habit_type = request.form.get('habit_type', 'good')
    habit_icon = request.form.get('habit_icon', '⭐')
    conn = get_connection()
    cursor = conn.cursor()
    log_type = request.form.get('log_type', 'boolean')
    cursor.execute(
        "UPDATE habits SET name=?, type=?, icon=?, log_type=? WHERE id=?",
        (new_name, habit_type, habit_icon, log_type, habit_id)
    )

    old_habit = conn.execute("SELECT log_type FROM habits WHERE id=?", (habit_id,)).fetchone()
    old_log_type = old_habit[0] if old_habit else 'boolean'

    cursor.execute(
        "UPDATE habits SET name=?, type=?, icon=?, log_type=? WHERE id=?",
        (new_name, habit_type, habit_icon, log_type, habit_id)
    )

    # If switching TO boolean, normalize all existing log values to 1
    if log_type == 'boolean' and old_log_type != 'boolean':
        cursor.execute("UPDATE habit_logs SET value=1 WHERE habit_id=?", (habit_id,))

    conn.commit()
    conn.close()
    return redirect("/habits")


@app.route("/habits")
def habits():
    conn = get_connection()
    cursor = conn.cursor()
    habits = cursor.execute("SELECT * FROM habits").fetchall()
    conn.close()
    return render_template("habits.html", habits=habits)


@app.route("/stats")
def stats_redirect():
    conn = get_connection()
    first = conn.execute("SELECT id FROM habits LIMIT 1").fetchone()
    conn.close()
    if first:
        return redirect(f"/stats/{first[0]}")
    return redirect("/")


@app.route("/stats/<int:habit_id>")
def stats(habit_id):
    conn = get_connection()
    cursor = conn.cursor()

    all_time_count = cursor.execute("SELECT COALESCE(SUM(value),0) FROM habit_logs WHERE habit_id=?", (habit_id,)).fetchone()
    monthly_count  = cursor.execute(
        "SELECT COALESCE(SUM(value),0) FROM habit_logs WHERE habit_id=? AND DATE(logged_at)>=?",
        (habit_id, (datetime.now().date() - timedelta(days=30)).isoformat())
    ).fetchone()
    weekly_count = cursor.execute(
        "SELECT COALESCE(SUM(value),0) FROM habit_logs WHERE habit_id=? AND DATE(logged_at)>=?",
        (habit_id, (datetime.now().date() - timedelta(days=7)).isoformat())
    ).fetchone()
    daily_count = cursor.execute(
        "SELECT COALESCE(SUM(value),0) FROM habit_logs WHERE habit_id=? AND DATE(logged_at)>=?",
        (habit_id, (datetime.now().date() - timedelta(days=1)).isoformat())
    ).fetchone()

    # Current streak
    dates = cursor.execute(
        "SELECT DISTINCT DATE(logged_at) FROM habit_logs WHERE habit_id=? ORDER BY logged_at DESC",
        (habit_id,)
    ).fetchall()
    today = datetime.now().date()
    cur_streak = 0
    check = today
    for row in dates:
        d = datetime.strptime(row[0], "%Y-%m-%d").date()
        if d == check:
            cur_streak += 1
            check -= timedelta(days=1)
        else:
            break

    # Longest streak
    asc_dates = cursor.execute(
        "SELECT DISTINCT DATE(logged_at) FROM habit_logs WHERE habit_id=? ORDER BY logged_at ASC",
        (habit_id,)
    ).fetchall()
    longest_streak = 0
    var_streak = 0
    last_date = None
    for row in asc_dates:
        d = datetime.strptime(row[0], "%Y-%m-%d").date()
        if last_date is None or d == last_date + timedelta(days=1):
            var_streak += 1
        else:
            longest_streak = max(longest_streak, var_streak)
            var_streak = 1
        last_date = d
    longest_streak = max(longest_streak, var_streak)

    habit_row = cursor.execute("SELECT * FROM habits WHERE id=?", (habit_id,)).fetchone()

    # Last 30 days bar chart data
    labels = []
    values = []
    for i in range(29, -1, -1):
        d = (datetime.now().date() - timedelta(days=i)).isoformat()
        labels.append(datetime.strptime(d, "%Y-%m-%d").strftime("%b %d"))
        cnt = cursor.execute(
            "SELECT COALESCE(SUM(value),0) FROM habit_logs WHERE habit_id=? AND DATE(logged_at)=?",
            (habit_id, d)
        ).fetchone()[0]
        values.append(cnt)

    # Heatmap: last 12 weeks (84 days)
    heatmap = []
    for i in range(83, -1, -1):
        d = (datetime.now().date() - timedelta(days=i)).isoformat()
        cnt = cursor.execute(
            "SELECT COALESCE(SUM(value),0) FROM habit_logs WHERE habit_id=? AND DATE(logged_at)=?",
            (habit_id, d)
        ).fetchone()[0]
        heatmap.append({"date": d, "count": cnt})

    all_habits = cursor.execute("SELECT * FROM habits").fetchall()
    counts = [
        cursor.execute("SELECT COUNT(*) FROM habit_logs WHERE habit_id=?", (h[0],)).fetchone()[0]
        for h in all_habits
    ]
    radar_labels = [h[1] for h in all_habits]

    log_type = habit_row[5] if len(habit_row) > 5 else 'boolean'

    conn.close()

    return render_template("stats.html",
                           log_type=log_type,
                           radar_labels=radar_labels,
                           counts=counts,
                           all_habits=all_habits,
                           labels=labels,
                           values=values,
                           heatmap=heatmap,
                           habit_name=habit_row[1],
                           habit_icon=habit_row[4] if len(habit_row) > 4 else "⭐",
                           habit_type=habit_row[3] if len(habit_row) > 3 else "good",
                           habit_id=habit_id,
                           all_time_count=all_time_count[0],
                           monthly_count=monthly_count[0],
                           weekly_count=weekly_count[0],
                           daily_count=daily_count[0],
                           cur_streak=cur_streak,
                           longest_streak=longest_streak)


if __name__ == "__main__":
    init_db()
    app.run(debug=True)