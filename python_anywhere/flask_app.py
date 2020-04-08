from flask import Flask,render_template,request,Response
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from io import BytesIO

import weather

spots = {
        'NRG': {
                'coords':'38.072, -81.081',
                'name':'New River Gorge',
                'weblink':'https://www.mountainproject.com/area/105855991/the-new-river-gorge'},
        'SNCA' : {
                'coords':'38.834, -79.366',
                'name':'Seneca Rocks',
                'weblink':'https://www.mountainproject.com/area/105861910/seneca-rocks'},
        'GF': {
                'coords':'38.992, -77.249',
                'name':'Great Falls',
                'weblink':'https://www.mountainproject.com/area/106163226/great-falls'},
        'SMC' : {
                'coords':'38.814, -79.282',
                'name': 'Smoke Hole Canyon',
                'weblink':'https://www.mountainproject.com/area/109582872/smoke-hole-canyon'},
        'SH':{
                'coords':'39.935, -76.385',
                'name':'Safe Harbor',
                'weblink':'https://www.mountainproject.com/area/107374703/safe-harbor'},
        'EF':{
                'coords':'38.947, -78.302',
                'name':'Elizabeth Furnace',
                'weblink':'https://www.mountainproject.com/area/106067125/elizabeth-furnace'},
        'AR': {
                'coords':'39.558, -77.599',
                'name':'Annapolis Rock',
                'weblink':'https://www.mountainproject.com/area/106734666/annapolis-rock'},
        'GH' :{
                'coords':'36.612, -81.491',
                'name': 'Grayson Highlands',
                'weblink':'https://www.mountainproject.com/area/106477419/grayson-highlands-state-park'},
        'GNK':{
                'coords':'41.682, -74.221',
                'name':'The Gunks',
                'weblink':'https://www.mountainproject.com/area/105798167/the-gunks'},
        'YOS': {
                'coords':'37.74, -119.573',
                'name':'Yosemite',
                'weblink':'https://www.mountainproject.com/area/105833381/yosemite-national-park'},
        }

app = Flask(__name__,static_url_path='/static')

@app.route('/')
def hello_world():
    return render_template('weather_app.html',spot_dict=spots)


@app.route('/plot.png',methods = ['POST','GET'])
def makePlot():
        if request.method == 'POST':
                rslts = weather.threeDaySummary(spots[request.form['place']],request.form['day'])
                fig = weather.plot3Day(rslts)
                output = BytesIO()
                FigureCanvas(fig).print_png(output)
                return Response(output.getvalue(), mimetype='image/png') # https://stackoverflow.com/questions/50728328/python-how-to-show-matplotlib-in-flask
        else:
                return render_template('weather_app.html')