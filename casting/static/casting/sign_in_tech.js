
$("#tech-interest-buttons>button[type=button]").click(function() {
    $(this).parent().slideUp();
    $(".tech-interest-form").slideDown();
    $(".tech-interest-form").find("textarea").val($(this).text() + " ");
});