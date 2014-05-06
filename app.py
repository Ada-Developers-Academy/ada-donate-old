import os
from flask import Flask, render_template, request
import stripe

app = Flask(__name__)

app.config.from_pyfile('application.cfg', silent=False)

stripe_keys = {
    'secret_key': app.config['SECRET_KEY'],
    'publishable_key': app.config['PUBLISHABLE_KEY']
}

stripe.api_key = stripe_keys['secret_key']

@app.route('/')
def index():
    return "it's working"

if __name__ == '__main__':
    app.run()