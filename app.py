import os
import sqlite3
from flask import Flask, render_template, request, g, redirect, url_for, abort, \
     render_template, flash
import stripe

app = Flask(__name__)
app.config.from_pyfile('application.cfg', silent=False)

# Load default config and override config from an environment variable
app.config.update(dict(DATABASE=os.path.join(app.root_path, 'donations.db')))

# DATABASE ...
def connect_db():
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

def get_db():
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db

@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

# ... DATABASE

# STRIPE ...
stripe_keys = {
    'secret_key': app.config['SECRET_KEY'],
    'publishable_key': app.config['PUBLISHABLE_KEY']
}

stripe.api_key = stripe_keys['secret_key']

# ... STRIPE

# ROUTES ...

@app.route('/')
def index():
    return render_template('index.html', key=stripe_keys['publishable_key'])

@app.route('/charge', methods=['POST'])
def charge():
    # Amount in cents
    amount = int(float(request.form['customer_amount']) * 100)
    dollar_amount = format((float(amount)/ 100), '.2f')

    customer = stripe.Customer.create(
        email='customer@example.com',
        card=request.form['stripeToken']
    )

    charge = stripe.Charge.create(
        customer=customer.id,
        amount=amount,
        currency='usd',
        description='Flask Charge'
    )

    if not charge['failure_code']:
        charge['failure_code'] = 'success'
    if not charge['failure_message']:
        charge['failure_message'] = 'success'
    print charge

    if charge['failure_code'] == 'success':
        db = get_db()
        db.execute('insert into donors (name, email, success, stripe_id, status, message, amount) values (?, ?, ?, ?, ?, ?, ?)',
                     [request.form['customer_name'], request.form['customer_email'], charge['captured'], charge['id'], charge['failure_code'], charge['failure_message'], amount])
        db.commit()

    return render_template('charge.html', amount=amount, dollar_amount=dollar_amount)

@app.template_filter('formatmoney')
def formatmoney(amount, cents=100):
    return format((float(amount) / cents), '.2f')
@app.template_filter('check_anonymous')
def check_anonymous(name):
    if len(name) == 0:
        return "Anonymous"
    else:
        return name
@app.route('/donors')
def show_donors():
    db = get_db()
    cur = db.execute('select * from donors order by id desc')
    donors = cur.fetchall()
    return render_template('donors.html', donors=donors)

# ... ROUTES

if __name__ == '__main__':
    app.run(debug=app.config['DEBUG'])