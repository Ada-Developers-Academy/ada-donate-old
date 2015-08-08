var AdaDonations = {
  validateCreditCard: function() {
    $(".card-number").validateCreditCard(function(result) {
      $(".card-type-icon").attr("class", "text-success card-type-icon fa");
      if (result.card_type !== null) {
        var card_type = result.card_type.name
        if (card_type == "diners_club_carte_blanche") { card_type = "diners-club"}
        $(".card-type-icon").addClass("fa fa-cc-" + card_type)
        $(".card-type").val(result.card_type.name)
      }
      result.valid ? $(".submit-donation").removeAttr("disabled") : $(".submit-donation").attr("disabled", "disabled")
    });
  },
  initCloseButtons: function() {
    $(".close").click(function() {
      $("." + $(this).data("dismiss")).slideUp();
      return false;
    });
  },
  onReady: function() {
    AdaDonations.initCloseButtons();
    AdaDonations.validateCreditCard();
  }
}

$(AdaDonations.onReady);
