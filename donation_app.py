import os
import re
import logging
from flask import Flask, render_template, request, g, redirect, url_for, abort, render_template, flash
from flask.ext.sqlalchemy import SQLAlchemy
import paypalrestsdk
from flask_sslify import SSLify

app = Flask(__name__)
app.config['DEBUG'] = os.environ.get('DEBUG', False)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["SQLALCHEMY_DATABASE_URI"]
db = SQLAlchemy(app)

# sslify = SSLify(app, permanent=True)

paypalrestsdk.configure({
  "mode":          os.environ["PAYMENT_SANDBOX"], # sandbox or live
  "client_id":     os.environ["PAYPAL_CLIENT_ID"],
  "client_secret": os.environ["PAYPAL_SECRET"]})

class DonationForm:
    def __init__(self, params):
        self.errors = []
        if not params.get("customer_amount") in ["", None]:
            self.amount = params.get("customer_amount")
        else:
            self.errors.append("Please enter a valid amount.")
        if "customer_name" in params:
            self.name = params["customer_name"]
        if "customer_email" in params:
            self.email = params["customer_email"]
        if "card[type]" in params:
            self.card_type = params.get("card[type]")
        if "card[number]" in params:
            self.card_number = params.get("card[number]")
        if "card[cvc]" in params:
            self.cvc = params.get("card[cvc]")
        if "card[month]" in params:
            self.month = params.get("card[month]")
        if "card[year]" in params:
            self.year = params.get("card[year]")

    def cents(self):
        return int(float(self.amount) * 100)

class Transaction:
  def __init__(self, response):
    self.uid           = response["transactions"][0]["related_resources"][0]["sale"]["id"]
    self.type          = response["intent"]
    self.response_code = response["state"]
    self.amount        = response["transactions"][0]["amount"]["total"]
    self.message       = response["state"]

  def success(self):
    return self.response_code == "approved"

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
    if len(form.errors) > 0:
        return render_template('index.html', form=form, error=form.errors[0])

    payment = paypalrestsdk.Payment({
      "intent": "sale",
      "payer": {
        "payer_info": {
            "email": form.email,
        },
        "payment_method": "credit_card",
        "funding_instruments": [{
          "credit_card": {
            "type": form.card_type,
            "number": form.card_number,
            "expire_month": form.month,
            "expire_year": form.year,
            "cvv2": form.cvc}}]},
      "transactions": [{
        "item_list": {
          "items": [{
            "name": "Tax deductable donation to Ada Developers Academy.",
            "sku": "donation",
            "price": form.amount,
            "currency": "USD",
            "quantity": 1 }]},
        "amount": {
          "total": form.amount,
          "currency": "USD" },
        "description": "Tax deductable donation to Ada Developers Academy." }]})


    if not payment.create():
        return render_template('index.html', form=form, error=payment.error["details"][0]["issue"])

    transaction = Transaction(payment)

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
