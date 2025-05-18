from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/result', methods=['POST'])
def result():
    fvc = float(request.form['fvc'])
    dlco = float(request.form['dlco'])
    mpap = float(request.form['mpap'])
    pawp = float(request.form['pawp'])
    co = float(request.form['co'])
    pvr = (mpap - pawp) / co

    if mpap >= 25 and pawp <= 15 and pvr >= 3:
        classification = "前毛細血管性肺高血圧症"
        treatment = "肺血管拡張薬の適応を検討"
    else:
        classification = "診断基準未満"
        treatment = "経過観察"

    return render_template('result.html', classification=classification, treatment=treatment, pvr=round(pvr, 2))

if __name__ == '__main__':
    app.run()