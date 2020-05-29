from flask import Flask , request, render_template, session, url_for,redirect
import sqlite3
import json
import ssl
from flask_bootstrap import Bootstrap
import urllib.request ,urllib.error


app = Flask(__name__)
Bootstrap(app)

app.config['SECRET_KEY'] = 'secret'

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



    # ignoring ssl error
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    # Connecting to url
    url = "https://api.rootnet.in/covid19-in/stats/latest"
    url1 = "https://api.covid19india.org/state_district_wise.json"
    fh = urllib.request.urlopen(url , context=ctx)
    fh1 = urllib.request.urlopen(url1 , context=ctx)
    # .read() reads whole as a string
    data = fh.read().decode()
    data1 = fh1.read().decode()
    js = json.loads(data)
    js1 = json.loads(data1)

    Totalcases=js["data"]["summary"]["total"]
    lastRefreshed=js["lastRefreshed"]

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


    return render_template('index.html',states=row ,Totalcases=Totalcases, refreshed =lastRefreshed)


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

    # ignoring ssl error
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    url1 = "https://api.covid19india.org/state_district_wise.json"
    fh1 = urllib.request.urlopen(url1 , context=ctx)
    # .read() reads whole as a string
    data1 = fh1.read().decode()

    js1 = json.loads(data1)

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

    conn1.commit()
    cur1.execute("SELECT * FROM districts ")
    row1 = cur1.fetchall()

    return render_template('states.html', states=row1)


@app.route('/search',methods=["GET","POST"])
def search():
    def correction(word):
        a=list(word)
        for i in range(len(a)):
            if a[i]==" ":
                print("true")
                s=a[0].upper()
                a[0] = s
                d=a[i+1].upper()
                a[i+1] = d
            else:
                s=a[0].upper()
                a[0]=s
        gg=""
        for j in a:
            gg+=j
        return gg


    if request.method=="POST":
        state_name = request.form.get("State")
        state1 = correction(state_name)
        city_name = request.form.get("City")
        city1 = correction(city_name)
        #print("1:",state_name)
        #print(city1)
        session['search'] =True
        session['state_name'] = state1
        session['city_name'] = city1

        return redirect('/show')
    return render_template('search.html')

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
