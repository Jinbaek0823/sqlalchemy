# Import the dependencies.
import numpy as np
import datetime as dt
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

from flask import Flask, jsonify

#################################################
# Database Setup
#################################################

engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()

# reflect the tables
Base.prepare(autoload_with=engine)

# Save references to each table
Station = Base.classes.station
measurement = Base.classes.measurement

# Create our session (link) from Python to the DB
session = Session(engine)

#################################################
# Flask Setup
#################################################
app = Flask(__name__)



#################################################
# Flask Routes
#################################################

#Start at the homepage.
#List all the available routes
@app.route("/")
def welcome():
    return(
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/start<br/>"
        f"/api/v1.0/start/end<br/>"
        f"start=end=YYYY-MM-DD"
    )

#Convert the query results from your precipitation analysis (i.e. retrieve only the last 12 months of data) to a dictionary using date as the key and prcp as the value.
@app.route("/api/v1.0/precipitation")
def precipitation():
    most_recent_date = session.query(measurement.date).order_by(measurement.date.desc()).first()[0]
    one_year_ago = dt.datetime.strptime(most_recent_date, '%Y-%m-%d') - dt.timedelta(days=365)
    one_year_ago_str = one_year_ago.strftime('%Y-%m-%d')
    precipitation_data = session.query(measurement.station, measurement.date, measurement.prcp)\
    .filter(measurement.date >= one_year_ago_str)\
    .filter(measurement.date <= most_recent_date)\
    .order_by(measurement.date).all()

    #close session
    session.close()

    precip = []
    for name, date, prcp in precipitation_data:
        precipitation_dict = {}
        precipitation_dict["Station Name"] = name
        precipitation_dict["Date"] = date
        precipitation_dict["Precipitation"] = prcp
        precip.append(precipitation_dict)
        
    #Return the JSON representation of your dictionary.
    return jsonify(precip)

#Return a JSON list of stations from the dataset.
@app.route("/api/v1.0/stations")
def station():
    result = session.query(Station.station).all()

    #close session
    session.close()

    station_name = list(np.ravel(result))
    return jsonify(station_name)
    
#Query the dates and temperature observations of the most-active station for the previous year of data.
@app.route("/api/v1.0/tobs")
def tobs():
    most_active_station = session.query(measurement.station,func.count(measurement.id))\
                      .group_by(measurement.station)\
                      .order_by(func.count(measurement.station).desc())\
                      .first()[0]
    most_recent_date = session.query(measurement.date).order_by(measurement.date.desc()).first()[0]
    one_year_ago = dt.datetime.strptime(most_recent_date, '%Y-%m-%d') - dt.timedelta(days=365)
    one_year_ago_str = one_year_ago.strftime('%Y-%m-%d')

    data = session.query(measurement.tobs).\
    filter(measurement.station == most_active_station).\
    filter(measurement.date >= one_year_ago_str).all() 

    #close session
    session.close()

    temps = list(np.ravel(data))

    #Return a JSON list of temperature observations for the previous year.
    return jsonify(temps)

#Return a JSON list of the minimum temperature, the average temperature, and the maximum temperature for a specified start or start-end range.
@app.route("/api/v1.0/<start>")
@app.route("/api/v1.0/<start>/<end>")
def statistics(start=None,end=None):
    #For a specified start, calculate TMIN, TAVG, and TMAX for all the dates greater than or equal to the start date
    stats = [func.min(measurement.tobs),func.max(measurement.tobs),func.avg(measurement.tobs)]
    if not end:
        result = session.query(*stats).filter(measurement.date >= start).all()

        #close session
        session.close()

        data = list(np.ravel(result))
        return jsonify(data)
    #For a specified start date and end date, calculate TMIN, TAVG, and TMAX for the dates from the start date to the end date, inclusive.
    result = session.query(*stats).filter(measurement.date >= start).filter(measurement.date <= end).all()

    #close session
    session.close()
    
    data = list(np.ravel(result))
    return jsonify(data)
    

if __name__ == '__main__':
    app.run(debug=True)
