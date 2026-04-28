from flask import Flask,render_template,request, redirect
from db import init_db,get_connection
from datetime import datetime,timedelta


app=Flask(__name__)

@app.route("/")
def home():
    conn=get_connection()
    habits=conn.execute("SELECT * FROM habits").fetchall()
    conn.close()
    return render_template("index.html",habits=habits)

@app.route("/add",methods=['POST'])
def add_habit():
    habit_name=request.form['habit_name']
    conn=get_connection()
    cursor=conn.cursor()

    cursor.execute("INSERT INTO habits (name,created_at) VALUES (?, ?)", (habit_name, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return redirect("/")

@app.route("/delete/<int:habit_id>",methods=['POST'])
def delete_habit(habit_id):
    conn=get_connection()
    cursor=conn.cursor()
    cursor.execute("DELETE FROM habit_logs WHERE habit_id = ?", (habit_id,))
    cursor.execute("DELETE FROM habits where id=?",(habit_id,))
    conn.commit()
    conn.close()
    return redirect("/")

@app.route("/log/<int:habit_id>", methods=['POST'])
def log_habit(habit_id):
    conn=get_connection()
    cursor=conn.cursor()
    cursor.execute("INSERT INTO habit_logs (logged_at,habit_id) VALUES (?, ?)", (datetime.now().isoformat(), habit_id))
    conn.commit()
    conn.close()
    return redirect("/")

@app.route("/stats/<int:habit_id>")
def stats(habit_id):
    conn=get_connection()
    cursor = conn.cursor()


    #COUNT NUMBER OF TIMES HABIT WAS DONE
    all_time_count=cursor.execute("SELECT COUNT(*) FROM habit_logs where habit_id=?",(habit_id,)).fetchone()
    monthly_count=cursor.execute("SELECT COUNT(*) FROM habit_logs where habit_id=? AND DATE(logged_at)>=?",(habit_id,(datetime.now().date()-timedelta(days=30)).isoformat())).fetchone()
    weekly_count=cursor.execute("SELECT COUNT(*) FROM habit_logs where habit_id=? AND DATE(logged_at)>=?",(habit_id,(datetime.now().date()-timedelta(days=7)).isoformat())).fetchone()
    daily_count=cursor.execute("SELECT COUNT(*) FROM habit_logs where habit_id=? AND DATE(logged_at)>=?",(habit_id,(datetime.now().date()-timedelta(days=1)).isoformat())).fetchone()


    #GET HABIT STREAKS
    
    dates = cursor.execute("SELECT DISTINCT DATE(logged_at) FROM habit_logs WHERE habit_id=? ORDER BY logged_at DESC", (habit_id,)).fetchall()
    today = datetime.now().date()
    cur_streak=0
    for i in dates:
        cur_date = datetime.strptime(i[0], "%Y-%m-%d").date()
        if cur_date == today:
            cur_streak += 1
            today -= timedelta(days=1)
        else:
            break

    
    var2=cursor.execute("SELECT DISTINCT DATE(logged_at) FROM habit_logs where habit_id=? ORDER BY logged_at ASC",(habit_id,)).fetchall()
    longest_streak=0
    var_streak=0
    last_date=None
    for i in var2:
        current_date=datetime.strptime(i[0],"%Y-%m-%d").date()
        if last_date==None or current_date==last_date:
            var_streak+=1
        elif current_date==last_date+timedelta(days=1):
            var_streak+=1
        else:
            longest_streak=max(longest_streak,var_streak)
            var_streak=1
        last_date=current_date
    longest_streak=max(longest_streak,var_streak)


    habit_name=cursor.execute("SELECT * FROM habits WHERE id=?",(habit_id,)).fetchone()
    

    labels=[]
    values=[]
    for i in range (0,14):
        date=(datetime.now().date()-timedelta(days=i)).isoformat()
        labels.append(datetime.strptime(date, "%Y-%m-%d").strftime("%b %d"))
        yesorno=cursor.execute("SELECT COUNT(*) FROM habit_logs where habit_id=? AND DATE (logged_at)=?",(habit_id,date)).fetchone()
        values.append(yesorno[0])

    labels=labels[::-1]
    values=values[::-1]


    all_habits=cursor.execute("SELECT * FROM habits").fetchall()

    
    conn.close()

    return render_template("stats.html",
    all_habits=all_habits,
    labels=labels,
    values=values,
    habit_name=habit_name[1],
    habit_id=habit_id,
    all_time_count=all_time_count[0],
    monthly_count=monthly_count[0],
    weekly_count=weekly_count[0],
    daily_count=daily_count[0],
    cur_streak=cur_streak,
    longest_streak=longest_streak
    )



if __name__=="__main__":
    init_db()
    app.run(debug=True)
