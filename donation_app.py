import os
from flask import Flask, render_template, request, g, redirect, url_for, abort, render_template, flash
from flask.ext.sqlalchemy import SQLAlchemy
from authorize import AuthorizeClient, CreditCard

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["SQLALCHEMY_DATABASE_URI"] 
    
db = SQLAlchemy(app)

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

@app.route('/')
def index():
    return render_template('index.html')

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
    
    client = AuthorizeClient(os.environ["AUTHORIZENET_KEY"], os.environ["AUTHORIZENET_SECRET"])
    cc = CreditCard(request.form["card[number]"], request.form["card[year]"], request.form["card[month]"], request.form["card[cvc]"])
    card = client.card(cc)
    response = card.capture(dollar_amount)
    transaction = Transaction(response.full_response)
    
    donor = Donor(
        name=request.form['customer_name'],
        email=request.form['customer_email'],
        success=transaction.success(),
        stripe_id=transaction.uid,
        status=transaction.message,
        message=transaction.message,
        amount=amount
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
    app.run(debug=True)