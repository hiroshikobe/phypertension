from flask import Flask, render_template, request
import os

app = Flask(__name__)

def calculate_pvr(mpap, pawp, co):
    try:
        return round((mpap - pawp) / co, 2)
    except ZeroDivisionError:
        return None

def estimate_rap(ivc_max, ivc_min):
    try:
        ratio = (ivc_max - ivc_min) / ivc_max
        if ratio > 0.5:
            return 5, ratio, "呼吸性変動あり"
        elif ratio > 0.3:
            return 10, ratio, "呼吸性変動境界"
        else:
            return 15, ratio, "呼吸性変動減弱"
    except:
        return None, None, "評価不能"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/result', methods=['POST'])
def result():
    def try_float(value):
        try:
            return float(value)
        except:
            return None

    # Hemodynamics
    mpap = try_float(request.form['mpap'])
    pawp = try_float(request.form['pawp'])
    co = try_float(request.form['co'])
    ci = try_float(request.form['ci'])
    pvr = calculate_pvr(mpap, pawp, co) if all(v is not None for v in [mpap, pawp, co]) else None

    # Pulmonary Function
    fvc = try_float(request.form['fvc'])
    fev1 = try_float(request.form['fev1'])
    fev1p = try_float(request.form['fev1p'])
    dlco = try_float(request.form['dlco'])
    dlco_va = try_float(request.form['dlco_va'])

    # CT findings
    ct_findings = request.form.getlist('ct_findings')

    # Echocardiography inputs
    ivc_max = try_float(request.form.get('ivc_max'))
    ivc_min = try_float(request.form.get('ivc_min'))
    trpg = try_float(request.form.get('trpg'))

    rap = spap = collapsibility_ratio = ivc_collapsibility = None
    if ivc_max and ivc_min:
        rap, collapsibility_ratio, ivc_collapsibility = estimate_rap(ivc_max, ivc_min)
    if trpg is not None and rap is not None:
        spap = round(trpg + rap, 1)

    tapse = try_float(request.form.get('tapse'))

    # Other data
    ntprobnp = try_float(request.form.get('ntprobnp'))
    walk_distance = try_float(request.form.get('walk_distance'))
    spo2_start = try_float(request.form.get('spo2_start'))
    spo2_min = try_float(request.form.get('spo2_min'))
    pao2 = try_float(request.form.get('pao2'))
    o2_flow = try_float(request.form.get('o2_flow'))

    # Comorbidities
    comorbid = request.form.getlist('comorbid')

    # Classification logic
    group = "分類不能"
    reason = "不完全なデータのため分類が困難です。"

    if mpap is not None and mpap > 20:
        if pawp is not None and pawp > 15:
            group = "第2群（左心不全関連）"
            reason = "PAWP > 15 mmHg により左心負荷が示唆されます。"
        elif pvr is not None and pvr >= 3:
            if ('間質性肺炎' in comorbid or 'COPD' in comorbid or (fvc is not None and fvc < 70)):
                group = "第3群（肺疾患関連）"
                reason = "PAWP <= 15 かつ PVR >= 3 に加え、%FVC低下や肺疾患合併あり。"
            elif '膠原病' in comorbid and dlco is not None and dlco < 45:
                group = "第1群（PAH）"
                reason = "膠原病合併かつDLco低下によりPAHが示唆されます。"
            else:
                group = "第1群（PAH）"
                reason = "前毛細血管性PHの基準（PAWP≦15, PVR≧3）を満たしています。"
        else:
            group = "分類不能（PH基準未満）"
            reason = "PVRが3未満であり、前毛細血管性PHの診断基準を満たしません。"
    elif mpap is not None:
        group = "PHなし"
        reason = "mPAPが20 mmHg以下のため、肺高血圧症の基準を満たしません。"

    return render_template('result.html', 
        pvr=pvr, spap=spap, rap=rap,
        collapsibility_ratio=round(collapsibility_ratio, 2) if collapsibility_ratio else None,
        ivc_collapsibility=ivc_collapsibility,
        group=group, reason=reason,
        mpap=mpap, pawp=pawp, co=co, ci=ci,
        fvc=fvc, fev1=fev1, fev1p=fev1p, dlco=dlco, dlco_va=dlco_va,
        ct_findings=ct_findings, comorbid=comorbid,
        tapse=tapse, ntprobnp=ntprobnp,
        walk_distance=walk_distance, spo2_start=spo2_start, spo2_min=spo2_min,
        pao2=pao2, o2_flow=o2_flow
    )

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
