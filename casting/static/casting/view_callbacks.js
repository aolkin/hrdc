$("form").submit(function(e){
    if (!confirm("Are you sure you're ready to submit your callback list?")) {
        e.preventDefault();
    }
})