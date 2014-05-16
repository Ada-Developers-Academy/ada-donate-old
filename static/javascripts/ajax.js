$(document).ready(function() {
  
  $('.alert button.close').click(function (e) {
    $(this).parent().hide()
  })
  
  $("#payment-form").validateForm()
});

$.fn.validateForm = function() {
  var form = $(this)
  var inputs = form.find("[data-validate]")
  form.click(function (e) {
    // e.preventDefault()
  })
}

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