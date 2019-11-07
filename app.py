import datetime
from db import get_db
from flask import Flask, render_template, g, request, redirect, url_for

app = Flask(__name__)
app.config['SECRET_KEY'] = 'Secret'


@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'sqlite3_db'):
        g.sqlite3_db.close()


@app.route('/', methods=['GET', 'POST'])
def index():
    db = get_db()

    if request.method == 'POST' and request.form['new-day']:
        referrer = request.headers.get("Referer")
        got_date = request.form['new-day']  # 2019-10-28

        if not got_date == '':
            date = datetime.datetime.strptime(got_date, '%Y-%m-%d')
            pretty_date = datetime.datetime.strftime(date, '%B %d, %Y')
            db_date = datetime.datetime.strftime(date, '%Y%m%d')
            cur = db.execute('SELECT entry_data, pretty_format FROM log_date WHERE entry_data = ?', [db_date])
            all_dates = cur.fetchall()

            # Duplicates protection
            result = []
            columns = [column[0] for column in cur.description]
            for row in all_dates:
                result.append(dict(zip(columns, row)))
            if len(result) == 0:
                db.execute('INSERT INTO log_date (entry_data, pretty_format) VALUES (?, ?)', [db_date, pretty_date])
                db.commit()

            # Prevent resubmit
            return redirect(referrer)

    # Totals for days
    log_food_cur = db.execute(
        '''
    SELECT log_date.entry_data, log_date.pretty_format, 
    sum(food.protein) as protein, sum(food.carbohydrates) as carbohydrates, 
    sum(food.fat) as fat, sum(food.calories) as calories
    FROM log_date 
    LEFT JOIN food_date ON log_date.entry_data = food_date.log_date 
    LEFT JOIN food on food.id = food_date.food_id
    GROUP by log_date.entry_data
    ORDER by log_date.entry_data DESC;
        ''')
    all_dates = log_food_cur.fetchall()
    request.form = None
    db.close()

    return render_template('index.html', all_dates=all_dates)


@app.route('/view_day/<date>', methods=['GET', 'POST'])
def view_day(date):
    db = get_db()

    if request.method == 'POST':
        referrer = request.headers.get("Referer")
        db.execute('INSERT INTO food_date (food_id, log_date) VALUES (?, ?)',
                   [request.form['food-select'], date])
        db.commit()
        # Prevent resubmit
        return redirect(referrer)

    cur = db.execute('SELECT pretty_format FROM log_date WHERE entry_data = ?', [date])
    date_data = cur.fetchone()

    try:
        date_data['pretty_format']
    except TypeError:
        return render_template('404.html', message='No date: {} found!'.format(date))

    # Products dropdown list
    food_cur = db.execute('select id, name from food')
    food_results = food_cur.fetchall()

    # Products consumed during the day
    log_food_cur = db.execute(
        '''
        SELECT food_date.id AS id, food.name, food.protein, food.carbohydrates, food.fat, food.calories 
        FROM food JOIN food_date ON food_date.food_id = food.id WHERE log_date = ?
        ''', [date])
    food_for_day = log_food_cur.fetchall()

    totals = {}
    totals['protein'] = 0
    totals['carbohydrates'] = 0
    totals['fat'] = 0
    totals['calories'] = 0
    for food in food_for_day:
        if __name__ == '__main__':
            totals['protein'] += food['protein']
            totals['carbohydrates'] += food['carbohydrates']
            totals['fat'] += food['fat']
            totals['calories'] += food['calories']

    db.close()
    return render_template('view_day.html',
                           pretty_format=date_data['pretty_format'],
                           date=date,
                           totals=totals,
                           food_for_day=food_for_day,
                           food_results=food_results)


@app.route('/add_food', methods=['GET', 'POST'])
def add_food():
    db = get_db()

    if request.method == 'POST':
        food_name = request.form['food-name']

        protein = int(request.form['protein'])
        fat = int(request.form['fat'])
        carbohydrates = int(request.form['carbohydrates'])
        calories = protein * 4 + fat * 9 + carbohydrates * 4

        db.execute('INSERT INTO food (name, protein, carbohydrates, fat, calories) VALUES (?, ?, ?, ?, ?)',
                   [food_name, protein, carbohydrates, fat, calories])
        db.commit()

    cur = db.execute('SELECT id, name, protein, carbohydrates, fat, calories FROM food')
    all_food = cur.fetchall()
    db.close()

    return render_template('add_food.html', all_food=all_food)


@app.route('/delete')
def delete():
    referrer = request.headers.get("Referer")

    if referrer is None:
        return redirect(url_for('index'))

    db = get_db()

    if 'add_food' in referrer:
        food_id = request.args.get('food')
        db.execute('DELETE FROM food WHERE id = ?', [food_id])
    elif 'view_day' in referrer:
        record_id = request.args.get('id')
        log_date = request.args.get('date')
        db.execute('DELETE FROM food_date WHERE log_date = ? AND id = ?', [log_date, record_id])
    else:
        day = request.args.get('day')
        db.execute('DELETE FROM log_date WHERE entry_data = ?', [day])
    db.commit()
    db.close()

    return redirect(referrer)


if __name__ == '__main__':
    app.run(debug=True)
