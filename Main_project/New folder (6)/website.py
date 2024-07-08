from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from datetime import datetime
import matplotlib
matplotlib.use('Agg')  
import matplotlib.pyplot as plt
import io
import base64
import numpy as np

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///drowsy.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class drowsy(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    driver_id = db.Column(db.Integer())
    driver_name = db.Column(db.String(60))
    v_start = db.Column(db.DateTime)
    v_stop = db.Column(db.DateTime)
    time = db.Column(db.DateTime)
    d_type = db.Column(db.String(10))
    d_total_time = db.Column(db.Integer)
    location = db.Column(db.String(100))

with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return render_template('driver.html')

@app.route('/show/<int:driver_id>')
def show(driver_id):
    Drowsy = drowsy.query.filter_by(driver_id=driver_id)
    alldrowsy = Drowsy.all()
    return render_template('show.html', alldrowsy=alldrowsy)

@app.route('/showall')
def showall():
    alldrowsy=drowsy.query.all()
    return render_template('show.html', alldrowsy=alldrowsy)

@app.route('/delete/<int:sno>')
def delete(sno):
    Drowsy = drowsy.query.filter_by(sno=sno).first()
    db.session.delete(Drowsy)
    db.session.commit()
    return redirect("/showall")

@app.route('/graph')
def graph():
    drowsiness_data = drowsy.query.order_by(drowsy.driver_id).all()

    # Process data for graphing
    driver_eyes = {}
    driver_yawn = {}
    driver_info = {}
    for entry in drowsiness_data:
        driver_id = entry.driver_id
        driver_name = entry.driver_name
        d_type = entry.d_type
        driver_info[driver_id] = driver_name  
        if d_type == 'eyes':
            driver_eyes[driver_id] = driver_eyes.get(driver_id, 0) + 1
        elif d_type == 'yawn':
            driver_yawn[driver_id] = driver_yawn.get(driver_id, 0) + 1

    # Creating the bar chart
    fig, ax = plt.subplots()
    driver_ids = list(driver_info.keys())
    bar_width = 0.35  
    index = np.arange(len(driver_ids)) 

    eyes_bars = ax.bar(index - bar_width/2, [driver_eyes.get(id, 0) for id in driver_ids], bar_width, label='Eyes')

    yawn_bars = ax.bar(index + bar_width/2, [driver_yawn.get(id, 0) for id in driver_ids], bar_width, label='Yawn')

    # Add count numbers at the top of each bar
    for bar in eyes_bars + yawn_bars:
        height = bar.get_height()
        ax.annotate('{}'.format(height),
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom')

    # Add labels for driver IDs and names below the bars
    for idx, driver_id in enumerate(driver_ids):
        ax.text(idx, -5, f'{driver_info[driver_id]}', ha='center', va='top', rotation=45)

    # Set the x-axis labels to be the driver names
    ax.set_xlabel('Driver')
    ax.set_ylabel('Count')
    ax.set_title('Eyes and Yawn Detection for Different Drivers')
    ax.set_xticks(index)
    ax.set_xticklabels([driver_info[driver_id] for driver_id in driver_ids])
    ax.legend()

    # Convert the plot to a PNG image
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    img_png = base64.b64encode(buf.getvalue()).decode('utf-8')

    return render_template('graph.html', chart=img_png)

if __name__ == "__main__":
    app.run(debug=True, port=768)
