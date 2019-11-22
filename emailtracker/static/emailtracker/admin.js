$(() => {
    
    let input = $("textarea#id_body").hide();
    let editor = $("<div>").html(input.val()).insertAfter(input);
    let toolbar = $("<div>").insertAfter(input);

    var quill = new Quill(editor[0], {
	//modules: { toolbar: toolbar[0] },
	placeholder: "Compose your message body here...",
	theme: 'snow'
    });
    quill.on('text-change', () => {
        input.val(editor.children(".ql-editor").html());
    });
});
