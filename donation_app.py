import os
from flask import Flask, render_template, request, g, redirect, url_for, abort, render_template, flash
from flask.ext.sqlalchemy import SQLAlchemy
import stripe

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["SQLALCHEMY_DATABASE_URI"] 
    
db = SQLAlchemy(app)

class Donor(db.Model):
    id        = db.Column(db.Integer, primary_key=True)
    name      = db.Column(db.String(80))
    email     = db.Column(db.String(120))
    success   = db.Column(db.Boolean)
    stripe_id = db.Column(db.String(80))
    status    = db.Column(db.String(80))
    message   = db.Column(db.String(255))
    amount    = db.Column(db.Integer)
    
    def __init__(self, **attrs):
        self.name      = attrs["name"]
        self.email     = attrs["email"]
        self.success   = attrs["success"]
        self.stripe_id = attrs["stripe_id"]
        self.status    = attrs["status"]
        self.message   = attrs["message"]
        self.amount    = attrs["amount"]

    def __repr__(self):
        return '<Donor %r>' % self.name

# STRIPE ...
stripe_keys = {
    'secret_key': os.environ['SECRET_KEY'],
    'publishable_key': os.environ['PUBLISHABLE_KEY']
}

stripe.api_key = stripe_keys['secret_key']
# ... STRIPE

# ROUTES ...

@app.route('/')
def index():
    return render_template('index.html', key=stripe_keys['publishable_key'])

@app.route("/thank-you")
def thank_you():
  donor = Donor.query.get(request.args.get('donor'))
  return render_template('thank_you.html', donor=donor)
  
@app.route('/charge', methods=['POST'])
def charge():
    # Amount in cents
    amount = int(float(request.form['customer_amount']) * 100)
    dollar_amount = format((float(amount)/ 100), '.2f')
    description = "Charitable contribution to Ada Developers Academy under the 501c3 Technology Alliance. Tax ID: da8au3b3k"
    customer = stripe.Customer.create(
        email='customer@example.com',
        card=request.form['stripeToken']
    )
    
    charge = stripe.Charge.create(
        customer=customer.id,
        amount=amount,
        currency='usd',
        description=description
    )

    if not charge['failure_code']:
        charge['failure_code']    = 'success'
        charge['failure_message'] = 'success'
    
    donor = Donor(
        name=request.form['customer_name'],
        email=request.form['customer_email'],
        success=charge['captured'],
        stripe_id=charge['id'],
        status=charge['failure_code'],
        message=charge['failure_message'],
        amount=amount
    )

    if charge['failure_code'] == 'success':
        db.session.add(donor)
        db.session.commit()
    
    return redirect(url_for('thank_you', donor=donor.id))
    

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
    donors = Donor.query.all()
    return render_template('donors.html', donors=donors)

# ... ROUTES

if __name__ == '__main__':
    app.run(debug=True)