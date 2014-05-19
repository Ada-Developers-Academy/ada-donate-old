import os
import re
from flask import Flask, render_template, request, g, redirect, url_for, abort, render_template, flash
from flask.ext.sqlalchemy import SQLAlchemy
from authorize import AuthorizeClient, CreditCard, AuthorizeError, AuthorizeInvalidError, AuthorizeResponseError
from flask_sslify import SSLify

app = Flask(__name__)
sslify = SSLify(app, permanent=True)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["SQLALCHEMY_DATABASE_URI"] 
app.config["PAYMENT_SANDBOX"] = os.environ["PAYMENT_SANDBOX"] == "True"
db = SQLAlchemy(app)

class DonationForm:
  def __init__(self, params):
    if "customer_amount" in params:
        self.amount = params.get("customer_amount")
    if "customer_name" in params:
        self.name = params["customer_name"]
    if "customer_email" in params:
        self.email = params["customer_email"]
    if "card[number]" in params:
        self.card_number       = params.get("card[number]")
    if "card[cvc]" in params:
        self.cvc       = params.get("card[cvc]")
    if "card[month]" in params:
        self.month       = params.get("card[month]")
    if "card[year]" in params:
        self.year       = params.get("card[year]")

  def cents(self):
      return int(float(self.amount) * 100)
        
class Transaction:
  def __init__(self, response):
    self.uid           = response["transaction_id"]
    self.type          = response["transaction_type"]
    self.response_code = response["response_code"]
    self.amount        = response["amount"]
    self.message       = response["response_reason_text"]
    
  def success(self):
    return self.response_code == "1"
    
class Donor(db.Model):
    __tablename__ = 'donors'
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

# ROUTES ...

# @app.before_request
# def check_ssl():
#     print "SSL Check"
#     force_ssl = os.environ["SSL"] == "True"
#     https = re.match(r'https', request.url, re.I)
#     print request
#     if force_ssl and not https:
#         return redirect(url_for('index', _scheme='https', _external=True))
    
@app.route('/')
def index():
    form = DonationForm(request.args)
    return render_template('index.html', form=form)

@app.route("/thank-you")
def thank_you():
  donor = Donor.query.get(request.args.get('donor'))
  return render_template('thank_you.html', donor=donor)
  
@app.route('/charge', methods=['POST'])
def charge():
    form = DonationForm(request.form)
    # Amount in cents
    client = AuthorizeClient(os.environ["AUTHORIZENET_KEY"], os.environ["AUTHORIZENET_SECRET"], app.config["PAYMENT_SANDBOX"])
    
    try:
      cc = CreditCard(form.card_number, form.year, form.month, form.cvc)
      card = client.card(cc, None, form.email, "Tax deductable donation to Ada Developers Academy")
      response = card.capture(form.amount)
    except ValueError, ex:
      return render_template('index.html', form=form, error="Please fill in the required fields")
    except AuthorizeInvalidError, message:
      return render_template('index.html', form=form, error=message)
    except AuthorizeResponseError, response:
      return render_template('index.html', form=form, error=response.full_response["response_reason_text"])
      
    transaction = Transaction(response.full_response)
    
    donor = Donor(
        name=form.name,
        email=form.email,
        success=transaction.success(),
        stripe_id=transaction.uid,
        status=transaction.message,
        message=transaction.message,
        amount=form.cents()
    )
    
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
    app.run(debug="DEBUG" in os.environ)