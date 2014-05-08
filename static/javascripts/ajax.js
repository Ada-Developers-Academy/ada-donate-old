$(document).ready(function() {
  $('#payment-form').submit(function(event) {
    var $form = $(this);

    // Prevent the form from submitting with the default action
    event.preventDefault();

    // Disable the submit button to prevent repeated clicks
    $form.find('button').prop('disabled', true);

    Stripe.card.createToken($form, stripeResponseHandler);

  });
  
  $('.alert button.close').click(function (e) {
    $(this).parent().hide()
  })
});

function stripeResponseHandler(status, response) {
    var form$ = $("#payment-form");
    if (response.error) {
        //...
        // show the errors on the form
        $(".payment-errors").show().find("span").text(response.error.message);
        form$.find('button').prop('disabled', false);
    } else {
        // token contains id, last4, and card type
        var token = response['id'];
        // insert the token into the form so it gets submitted to the server
        form$.append("<input type='hidden' name='stripeToken' value='" + token + "'/>");
        // and submit
        form$.get(0).submit();
    }
}