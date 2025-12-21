from flask import Flask, request, render_template_string, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_apscheduler import APScheduler
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///health_tracker.db'
app.config['SECRET_KEY'] = 'secret-key-123'
db = SQLAlchemy(app)
scheduler = APScheduler()



class Record(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(20)) 
    name = db.Column(db.String(100), nullable=False)
    scheduled_time = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='Pending') 



HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Health Reminder System</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
    <style>
        body { background-color: #f8f9fa; padding: 20px; }
        .container { max-width: 800px; background: white; padding: 30px; border-radius: 15px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
        .badge-vaccine { background-color: #0d6efd; }
        .badge-medicine { background-color: #198754; }
    </style>
</head>
<body>
    <div class="container">
        <h2 class="text-center mb-4"> Health & Vaccination Tracker</h2>
        
        <div class="card mb-4">
            <div class="card-body">
                <form method="POST" action="/add">
                    <div class="row g-3">
                        <div class="col-md-3">
                            <select name="category" class="form-select" required>
                                <option value="Vaccination">Vaccination</option>
                                <option value="Medicine">Medicine</option>
                            </select>
                        </div>
                        <div class="col-md-4">
                            <input type="text" name="name" class="form-control" placeholder="Name (e.g. Flu Shot, Aspirin)" required>
                        </div>
                        <div class="col-md-3">
                            <input type="datetime-local" name="time" class="form-control" required>
                        </div>
                        <div class="col-md-2">
                            <button type="submit" class="btn btn-primary w-100">Add</button>
                        </div>
                    </div>
                </form>
            </div>
        </div>

        <table class="table table-hover">
            <thead class="table-light">
                <tr>
                    <th>Type</th>
                    <th>Name</th>
                    <th>Scheduled Time</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                {% for record in records %}
                <tr>
                    <td><span class="badge {{ 'badge-vaccine' if record.category == 'Vaccination' else 'badge-medicine' }}">{{ record.category }}</span></td>
                    <td>{{ record.name }}</td>
                    <td>{{ record.scheduled_time.strftime('%Y-%m-%d %H:%M') }}</td>
                    <td>
                        {% if record.status == 'Reminded' %}
                            <span class="text-danger fw-bold">⏰ Reminder Sent!</span>
                        {% else %}
                            <span class="text-muted">{{ record.status }}</span>
                        {% endif %}
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</body>
</html>
"""



@app.route('/')
def index():
    records = Record.query.order_by(Record.scheduled_time.asc()).all()
    return render_template_string(HTML_TEMPLATE, records=records)

@app.route('/add', methods=['POST'])
def add_record():
    category = request.form.get('category')
    name = request.form.get('name')
    time_str = request.form.get('time')
    
    
    scheduled_time = datetime.strptime(time_str, '%Y-%m-%dT%H:%M')
    
    new_record = Record(category=category, name=name, scheduled_time=scheduled_time)
    db.session.add(new_record)
    db.session.commit()
    return redirect(url_for('index'))



def check_reminders():
    with app.app_context():
        now = datetime.now()
       
        due_tasks = Record.query.filter(Record.scheduled_time <= now, Record.status == 'Pending').all()
        
        for task in due_tasks:
            print(f"NOTIFICATION: Time for your {task.category}: {task.name}!")
            task.status = 'Reminded'
            db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        db.create_all() 
        
    scheduler.add_job(id='reminder_job', func=check_reminders, trigger='interval', seconds=10)
    scheduler.start()
    
    app.run(debug=True)


