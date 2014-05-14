donations
=========

### Getting Started

Start by copying the `application.cfg.example` file:

```
cp application.cfg.example application.cfg
```

Change each value to the correct value for your environment

### Prepare the DB
Enter the python shell and run the following to load the db configuration

```
from app import db
db.create_all()
```

### Transaction
 x success    : boolean
 - status     : string (success or one of the error messages below)
 - message    : string (success or one of the error messages descriptions)
 x amount     : integer
 x stripe_id  : integer
 x donor_name : string (allow nil (anonymous))

#### Errors:
##Handled by Stripe

- incorrect_number:     The card number is incorrect.
- invalid_number:       The card number is not a valid credit card number.
- invalid_expiry_month: The card's expiration month is invalid.
- invalid_expiry_year:  The card's expiration year is invalid.
- invalid_cvc:          The card's security code is invalid.
- expired_card:         The card has expired.
- incorrect_cvc:        The card's security code is incorrect.
- incorrect_zip:        The card's zip code failed validation.
- card_declined:        The card was declined.
- missing:              There is no card on a customer that is being charged.
- processing_error:     An error occurred while processing the card.
- rate_limit:           An error occurred due to requests hitting the API too quickly. Please email support@stripe.com if you're consistently running into this error.
