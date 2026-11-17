import json,pymysql,time
from flask import Flask
from flask import request,redirect
import datetime
import yaml

app = Flask(__name__)

db_config = None
with open("config.yml", "r") as file:
    config = yaml.safe_load(file)
    db_config = config['mysql']

def auth(token):
    if token != '123':
        return False
    conn = pymysql.connect(**db_config) #setup our credentials
    cur = conn.cursor(pymysql.cursors.DictCursor)
    sql ='SELECT * FROM bumhirf_adsb_auth WHERE `token` = %s;'
    cur.execute(sql,(token))
    results = cur.fetchall()
    if len(results) == 1:
        return True
    else:
        return False

def log(token,endpoint,response):
    conn = pymysql.connect(**db_config) #setup our credentials
    cur = conn.cursor(pymysql.cursors.DictCursor)
    sql = 'INSERT INTO `bumhirf_adsb_logs` (`endpoint`,`token`,`response`,`dt`) VALUES (%s,%s,%s,%s)'
    dt = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cur.execute(sql,(endpoint,token,response,dt))
    conn.commit()

@app.route("/getData", methods=['GET'])
def getData():
    res = {}
    res['req'] = 'getData'
    res['sqltime'] = 0
    res['data'] = []
    token = request.args.get('key')

    if not auth(token):
        res['code'] = 0
        res['msg'] = 'Invalid or missing key'
        log(token,res['req'],'401')
        return json.dumps(res,indent=4), 401, {'Content-Type': 'application/json'}

    start = request.args.get('start')
    end = request.args.get('end')

    if not start or not end:
        res['code'] = 0
        res['msg'] = 'start and end are mandatory'
        log(token,res['req'],'400')
        return json.dumps(res,indent=4), 400, {'Content-Type': 'application/json'}

    try:
        start_date = datetime.datetime.strptime(start, '%Y-%m-%d %H:%M:%S')
        end_date = datetime.datetime.strptime(end, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        res['code'] = 0
        res['msg'] = 'Use YYYY-MM-DD HH:MM:SS for start and end'
        log(token,res['req'],'400')
        return json.dumps(res,indent=4), 400, {'Content-Type': 'application/json'}

    if start_date > end_date:
        res['code'] = 0
        res['msg'] = 'start must be before or equal to end'
        log(token,res['req'],'400')
        return json.dumps(res,indent=4), 400, {'Content-Type': 'application/json'}

    conn = pymysql.connect(**db_config) #setup our credentials
    cur = conn.cursor(pymysql.cursors.DictCursor)
    sql = """
        SELECT dpid, date_time, `hex`, flight_num, squawk, lat, lon,
               ST_AsText(geo_point) AS geo_point, fid, gs, alt_gps,
               alt_baro, cat, track, nav_heading
        FROM class_datapoints
        WHERE date_time BETWEEN %s AND %s
        ORDER BY date_time
        LIMIT 500
    """
    started = time.time()
    cur.execute(sql,(start_date,end_date))
    res['sqltime'] = time.time() - started

    res['code'] = 1
    res['msg'] = 'ok'
    items = []
    for row in cur:
        items.append(row)

    cur.close()
    conn.close()
    res['data'] = items
    log(token,res['req'],'200')
    return json.dumps(res,indent=4,default=str), 200, {'Content-Type': 'application/json'}

@app.route("/countInPolygon", methods=['GET'])
def countInPolygon():
    res = {}
    res['req'] = 'countInPolygon'
    res['sqltime'] = 0
    res['data'] = None
    token = request.args.get('key')

    if not auth(token):
        res['code'] = 0
        res['msg'] = 'Invalid or missing key'
        log(token,res['req'],'401')
        return json.dumps(res,indent=4), 401, {'Content-Type': 'application/json'}

    polygon = request.args.get('polygon','')

    try:
        points = []
        for point in polygon.split(','):
            x, y = point.split()
            x = float(x)
            y = float(y)
            if not (-180 <= x <= 180 and -90 <= y <= 90):
                raise ValueError
            points.append((x,y))

        if len(points) < 4 or points[0] != points[-1] or len(set(points)) < 3:
            raise ValueError
    except ValueError:
        res['code'] = 0
        res['msg'] = 'Provide at least three longitude latitude pairs and repeat the first pair at the end'
        log(token,res['req'],'400')
        return json.dumps(res,indent=4), 400, {'Content-Type': 'application/json'}

    polygon_text = 'POLYGON((' + ','.join(f'{x} {y}' for x, y in points) + '))'

    conn = pymysql.connect(**db_config)
    cur = conn.cursor(pymysql.cursors.DictCursor)
    sql = """
        SELECT COUNT(*) AS `count`
        FROM class_datapoints
        WHERE ST_Within(geo_point, ST_GeomFromText(%s, 0))
    """

    started = time.time()
    cur.execute(sql,(polygon_text,))
    result = cur.fetchone()
    res['sqltime'] = time.time() - started

    cur.close()
    conn.close()

    res['data'] = {'count': result['count']}
    res['code'] = 1
    res['msg'] = 'ok'
    log(token,res['req'],'200')
    return json.dumps(res,indent=4), 200, {'Content-Type': 'application/json'}

@app.route("/getAvgSpeedByFlight", methods=['GET'])
def getAvgSpeedByFlight():
    res = {}
    res['req'] = 'getAvgSpeedByFlight'
    res['sqltime'] = 0
    res['data'] = []
    token = request.args.get('key')

    if not auth(token):
        res['code'] = 0
        res['msg'] = 'Invalid or missing key'
        log(token,res['req'],'401')
        return json.dumps(res,indent=4), 401, {'Content-Type': 'application/json'}

    start = request.args.get('start')
    end = request.args.get('end')
    start_date = None
    end_date = None

    try:
        if start is not None:
            start_date = datetime.datetime.strptime(start, '%Y-%m-%d %H:%M:%S')
        if end is not None:
            end_date = datetime.datetime.strptime(end, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        res['code'] = 0
        res['msg'] = 'Use YYYY-MM-DD HH:MM:SS for start and end'
        log(token,res['req'],'400')
        return json.dumps(res,indent=4), 400, {'Content-Type': 'application/json'}

    if start_date is not None and end_date is not None and start_date > end_date:
        res['code'] = 0
        res['msg'] = 'start must be before or equal to end'
        log(token,res['req'],'400')
        return json.dumps(res,indent=4), 400, {'Content-Type': 'application/json'}

    sql = "SELECT AVG(gs) AS avg_speed, flight_num FROM class_datapoints"
    conditions = []
    values = []

    if start_date is not None:
        conditions.append("date_time >= %s")
        values.append(start_date)
    if end_date is not None:
        conditions.append("date_time <= %s")
        values.append(end_date)
    if conditions:
        sql += " WHERE " + " AND ".join(conditions)

    sql += " GROUP BY flight_num ORDER BY flight_num LIMIT 500"

    conn = pymysql.connect(**db_config)
    cur = conn.cursor(pymysql.cursors.DictCursor)

    started = time.time()
    cur.execute(sql,tuple(values))
    res['sqltime'] = time.time() - started

    items = []
    for row in cur:
        item = {}
        item['flight_num'] = row['flight_num']
        item['avg_speed'] = row['avg_speed']
        if item['avg_speed'] is not None:
            item['avg_speed'] = float(item['avg_speed'])
        items.append(item)

    cur.close()
    conn.close()

    res['data'] = items
    res['code'] = 1
    res['msg'] = 'ok'
    log(token,res['req'],'200')
    return json.dumps(res,indent=4), 200, {'Content-Type': 'application/json'}

if __name__ == "__main__":
    app.run(host='0.0.0.0',debug=True)