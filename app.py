import os
import sqlite3
from flask import Flask, render_template, request, g, redirect, url_for, abort, \
     render_template, flash
import stripe

app = Flask(__name__)
app.config.from_pyfile('application.cfg', silent=False)

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'donations.db'),
    DEBUG=True,
#    SECRET_KEY='development key',
    USERNAME='admin',
#    PASSWORD='default'
))

def connect_db():
    """Connects to the specific database."""
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
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db

@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

stripe_keys = {
    'secret_key': app.config['SECRET_KEY'],
    'publishable_key': app.config['PUBLISHABLE_KEY']
}

stripe.api_key = stripe_keys['secret_key']

@app.route('/')
def index():
    return render_template('index.html', key=stripe_keys['publishable_key'])

@app.route('/charge', methods=['POST'])
def charge():
    # Amount in cents
    amount = request.form['customer_amount']
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

    print charge

    db = get_db()
    db.execute('insert into donors (name, amount) values (?, ?)',
                 [request.form['customer_name'], request.form['customer_amount']])
    db.commit()

    return render_template('charge.html', amount=amount, dollar_amount=dollar_amount)

@app.route('/donors')
def show_donors():
    db = get_db()
    cur = db.execute('select name, amount from donors order by id desc')
    donors = cur.fetchall()
    return render_template('donors.html', donors=donors)

if __name__ == '__main__':
    #Remember to set to false before making this live code.
    app.run(debug=True)