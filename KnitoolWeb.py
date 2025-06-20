import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")  # .env dosyasından gizli anahtar okunuyor



def get_progress_color(percent):
    if percent == 100:
        return "darkgreen"
    elif percent >= 80:
        return "green"
    elif percent >= 60:
        return "olive"
    elif percent >= 40:
        return "gold"
    elif percent >= 20:
        return "darkorange"
    else:
        return "red"


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/simple_counter', methods=['GET', 'POST'])
def simple_counter():
    if 'count' not in session:
        session['count'] = 0

    if request.method == 'POST':
        if 'increment' in request.form:
            session['count'] += 1
        elif 'decrement' in request.form and session['count'] > 0:
            session['count'] -= 1
        return redirect(url_for('simple_counter'))

    return render_template('simple_counter.html', count=session['count'])


@app.route('/project_counter', methods=['GET', 'POST'])
def project_counter():
    projects = session.get('projects', {})

    if request.method == 'POST':
        if 'increment' in request.form or 'decrement' in request.form:
            pname = session.get('project_name')
            if not pname or pname not in projects:
                return redirect(url_for('project_counter'))

            project = projects[pname]
            count = project.get('count', 0)
            total = project.get('total', 0)
            times = project.get('times', [])

            import time
            now = time.time()

            last_time = session.get('last_time', now)
            elapsed = now - last_time if last_time else 0
            session['last_time'] = now

            if 'increment' in request.form and count < total:
                count += 1
                times.append(elapsed)
            elif 'decrement' in request.form and count > 0:
                count -= 1
                if times:
                    times.pop()

            project['count'] = count
            project['times'] = times
            projects[pname] = project
            session['projects'] = projects
            return redirect(url_for('project_counter'))

        # Yeni proje oluşturma veya seçme
        pname = request.form.get('project_name', '').strip()
        new_pname = request.form.get('new_project_name', '').strip()
        total_str = request.form.get('total')
        start_str = request.form.get('start')

        if new_pname:
            pname = new_pname

        if pname:
            try:
                total = int(total_str)
                start = int(start_str)
                if total <= 0 or start <= 0 or start > total:
                    raise ValueError
            except:
                return render_template('project_counter.html',
                                       show_counter=False,
                                       error="Geçerli ve mantıklı sayılar giriniz.",
                                       project_names=list(projects.keys()),
                                       projects=projects,
                                       selected_project=pname)

            if pname not in projects:
                projects[pname] = {'total': total, 'count': start - 1, 'times': []}
            else:
                projects[pname]['total'] = total
                projects[pname]['count'] = start - 1
                if 'times' not in projects[pname]:
                    projects[pname]['times'] = []

            session['project_name'] = pname
            session['projects'] = projects
            session['last_time'] = None
            return redirect(url_for('project_counter'))

    # GET isteği veya POST sonrası sayfa yükleme
    pname = session.get('project_name')
    projects = session.get('projects', {})
    project_names = list(projects.keys())

    if pname and pname in projects:
        project = projects[pname]
        count = project.get('count', 0)
        total = project.get('total', 0)
        times = project.get('times', [])

        percent = round((count / total) * 100, 1) if total > 0 else 0
        progress_color = get_progress_color(percent)

        last_row_time = None
        total_time = None

        if times:
            last_elapsed = times[-1]
            mins, secs = divmod(int(last_elapsed), 60)
            last_row_time = f"{mins} dk {secs} sn"

            total_sec = int(sum(times))
            h, rem = divmod(total_sec, 3600)
            m, s = divmod(rem, 60)
            total_time = f"{h} saat {m} dk {s} sn"

        if percent == 100:
            projects.pop(pname)
            session['projects'] = projects
            session.pop('project_name', None)
            project_names = list(projects.keys())

        return render_template('project_counter.html',
                               show_counter=True,
                               count=count,
                               total=total,
                               percent=percent,
                               progress_color=progress_color,
                               last_row_time=last_row_time,
                               total_time=total_time,
                               project_names=project_names,
                               projects=projects,
                               selected_project=pname,
                               show_confetti=(percent == 100))

    # Burada kesin return var, fonksiyonun hiç return etmemesi imkansız
    return render_template('project_counter.html',
                           show_counter=False,
                           project_names=project_names,
                           projects=projects,
                           selected_project=pname)

@app.route('/reset_project')
def reset_project():
    session.pop('project_name', None)
    session.pop('last_time', None)
    return redirect(url_for('project_counter'))



if __name__ == '__main__':
    app.run(debug=True)
