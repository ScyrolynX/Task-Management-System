from flask import Flask, render_template as folder , request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone


T_app= Flask(__name__)

T_app.config['SQLALCHEMY_DATABASE_URI']= 'sqlite:///f_tasks.db'   # create a tasks.db file in the current folder
T_app.config['SQLALCHEMY_TRACK_MODIFICATIONS']= False

db= SQLAlchemy(T_app)    # This connect the flask to the database

class Task(db.Model):
	id= db.Column(db.Integer, primary_key=True)  # For each integer in each column
	content= db.Column(db.String(150), nullable=False) # for the content in each column, must be string and not more than 150 words and also cant be empty thats the function of nullable
	completed= db.Column( db.Boolean, default=False)   # True or false if completed andd by default False
	created = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))  # creates a timestamp
	exp_date= db.Column(db.DateTime, nullable=True)
	skipped= db.Column(db.Boolean, default=False)
    

@T_app.route("/")
def  root():
    return redirect(url_for("task_p"))

@T_app.route("/contact")
def  contact():
	return folder("contact.html")
	
@T_app.route("/about")
def  about():
	return folder("about.html")
	
@T_app.route("/tasks",  methods=["POST","GET"])
def task_p():
	if request.method == "POST":
		task_content= request.form.get("task")
		date_str= request.form.get("exp_date")

		if task_content:
			exp_date= datetime.fromisoformat(date_str) if date_str else None
			new_task= Task(content=task_content, exp_date=exp_date)
			db.session.add(new_task)
			db.session.commit()

		return redirect(url_for("task_p"))

	all_task= Task.query.order_by (Task.created.desc()).all() # Newest first
	today = datetime.now(timezone.utc).date()
	
	today_tasks=[]
	upcoming_tasks=[]
	overdue_tasks=[]
	completed_tasks=[]
	skipped_tasks=[]
 
	for t in all_task:
		if t.skipped:
			skipped_tasks.append(t)
		elif t.completed:
			completed_tasks.append(t)
		elif t.exp_date:
			if t.exp_date.date() < today:
				overdue_tasks.append(t)
			elif t.exp_date.date() == today:
				today_tasks.append(t)
			else:
				upcoming_tasks.append(t)
		else:
			today_tasks.append(t)
   
	return folder("tasks.html",  today_tasks=today_tasks,
                  upcoming_tasks=upcoming_tasks,
                  overdue_tasks=overdue_tasks,
                  completed_tasks=completed_tasks,
                  skipped_tasks=skipped_tasks)

@T_app.route("/tasks/<int:task_id>/toggle" , methods=["POST"])
def task_toggle(task_id):
	c_task= Task.query.get_or_404(task_id)
	c_task.completed = not c_task.completed
	db.session.commit()
	return redirect(url_for("task_p"))

@T_app.route("/tasks/<int:task_id>/delete", methods=["POST"])
def task_delete(task_id):
	d_task= Task.query.get_or_404(task_id)
	db.session.delete(d_task)
	db.session.commit()
	return redirect(url_for("task_p"))

@T_app.route("/tasks/<int:task_id>/skip", methods=["POST"])
def task_skip(task_id):
    T_task= Task.query.get_or_404(task_id)
    T_task.skipped= not T_task.skipped
    db.session.commit()
    return redirect(url_for("task_p"))

if __name__== "__main__":
    with T_app.app_context():
       db.create_all()
    T_app.run(debug=True, host="0.0.0.0", port=5000)
