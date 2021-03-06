from flask import Flask , request, render_template, session, url_for, redirect
import sqlite3
import json
import ssl
from flask_bootstrap import Bootstrap
import urllib.request ,urllib.error
from datetime import datetime

app = Flask(__name__)
Bootstrap(app)

app.config['SECRET_KEY'] = 'secret'

# ignoring ssl error
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

#function for opening url
def open(url):
    fh= urllib.request.urlopen(url , context=ctx)
    # .read() reads whole as a string
    data= fh.read().decode()
    js= json.loads(data)
    return js

@app.route('/' ,methods=["GET","POST"])
def index():

    conn = sqlite3.connect("covid19_state.db")
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS states")
    cur.execute("""CREATE TABLE IF NOT EXISTS states
    (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
    name TEXT UNIQUE, confirmed INTEGER, deaths INTEGER,
    recovered INTEGER  )
    """)

    # Connecting to url
    url = "https://api.rootnet.in/covid19-in/stats/latest"
    js =open(url)

    # Connecting to url of datewise cases
# cases increment
    Totalcases=js["data"]["summary"]["total"]
    session['Totalcases'] = Totalcases
    url2 = "https://api.rootnet.in/covid19-in/stats/history"
    js2 = open(url2)

    # cases incement of last two days in  INDIA
    dict_inc={}
    for i in range(len(js2['data'])):
      #info_datewise = i
      if i >= (len(js2['data'])-2):
          cases_state = [js2['data'][i]['summary']['total'], js2['data'][i]['summary']['deaths'], js2['data'][i]['summary']['discharged']]
          dict_inc[js2['data'][i]['day']] = cases_state
    # finding increase in cases per day
    len_dict = len(list(dict_inc))
    day_before = list(dict_inc)[0]
    last = list(dict_inc)[1]
    #print(day_before)
    #print(last)
    inc = dict_inc[last][0]-dict_inc[day_before][0]

# datetime conversion
    lastRefreshed=js["lastRefreshed"]
    convert = datetime.strptime(lastRefreshed,"%Y-%m-%dT%H:%M:%S.%fZ")
    Date =convert.date()
    Time =convert.time()

###########################
    for i in js["data"]["regional"]:
        state_name = i["loc"]
        confirmed= i["totalConfirmed"]
        deaths = i["deaths"]
        recovered = i["discharged"]
        cur.execute("INSERT OR REPLACE INTO states(name, confirmed, deaths, recovered) VALUES(?, ?, ?, ?)" , (state_name, confirmed, deaths, recovered))
        #cur.execute("UPDATE states SET ")
    conn.commit()
    cur.execute("SELECT * FROM states ORDER BY confirmed DESC ")
    row = cur.fetchall()
###########################################

    return render_template('index.html',states=row ,Totalcases=Totalcases, Date =Date , Time=Time, increment= inc)


#@app.route('/<_stateid>',methods=["GET","POST"])
@app.route('/states')
def states():

    conn1 = sqlite3.connect("covid19_district.db")
    cur1 = conn1.cursor()
    cur1.execute("DROP TABLE IF EXISTS districts")
    cur1.execute("""CREATE TABLE IF NOT EXISTS districts
    (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
    state_name TEXT,city_name TEXT ,confirmed INTEGER, deaths INTEGER,
    active INTEGER , recovered INTEGER )
    """)

    url1 = "https://api.covid19india.org/state_district_wise.json"
    js1 = open(url1) #######calling function

    for state in js1:
        state_name = state
        for cities in js1[state_name]["districtData"]:
            city_name = cities
            confirmed = js1[state_name]["districtData"][city_name]["confirmed"]
            recovered = js1[state_name]["districtData"][city_name]["recovered"]
            active = js1[state_name]["districtData"][city_name]["active"]
            deaths = js1[state_name]["districtData"][city_name]["deceased"]
            cur1.execute("INSERT OR REPLACE INTO districts(state_name, city_name, confirmed, deaths, active, recovered) VALUES(?, ?, ?, ?, ?, ?)" , (state_name, city_name, confirmed, deaths, active, recovered))
            #cur1.execute("UPDATE districts SET  VALUES(?, ?, ?, ?, ?, ?)" , (state_name, city_name, confirmed, deaths, active, recovered))
        #insert or eplace command do both insert and update at the same time
    conn1.commit()
    cur1.execute("SELECT * FROM districts ")
    row1 = cur1.fetchall()

    return render_template('states.html', states=row1 , Totalcases=session['Totalcases'])


@app.route('/search',methods=["GET","POST"])
def search():
    url1 = "https://api.covid19india.org/state_district_wise.json"
    js1 = open(url1)

    lst=[]
    for states in js1:
        for cities in js1[states]["districtData"]:
            lst.append(cities)
    # taking input from html form
    if request.method=="POST":
        state_name = request.form.get("state")
        city_name = request.form.get("city")
        session['search'] =True
        session['state_name'] = state_name
        session['city_name'] = city_name

        return redirect('/show')
    return render_template('search.html', states=js1 , cities=lst)

@app.route('/show')
def show():
    #using session to store in value so it can be accesible in differents routes
    #print(session['state_name'])
    #print(session['city_name'])
    conn1 = sqlite3.connect("covid19_district.db")
    cur1 = conn1.cursor()
    cur1.execute("SELECT * FROM districts WHERE state_name=? AND city_name= ?  ",(session['state_name'], session['city_name']))
    row2 = cur1.fetchone()
    return render_template('show.html' ,i= row2)

@app.route('/about')
def about():
    return render_template("about.html")

@app.errorhandler(404)
def page_not_found(e):
    return "Page not found. Try again or Refresh."

if __name__ == "__main__":
    app.run(debug =True)
