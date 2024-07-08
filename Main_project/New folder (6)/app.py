from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from datetime import datetime

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
now=datetime.now();
with app.app_context():
    Drowsy = drowsy(driver_id=1, driver_name="truckdriver", v_start=now,v_stop=now,time=now,d_type="eyes",d_total_time=10,location="sangamner")
    #Create an instance of the Drowsy model
    db.session.add(Drowsy)
    db.session.commit()
    
    """Drowsy=drowsy.query.filter_by(driver_id=1).first()
    db.session.delete(Drowsy)
    db.session.commit()
    """
    


if __name__ == "__main__":
    app.run(debug=True, port=3000)