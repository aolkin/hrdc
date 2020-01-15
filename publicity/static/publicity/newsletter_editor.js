$(() => {
    
    let input = $("textarea#id_message").hide();
    let editor = $("<div>").html(input.val()).insertAfter(input);
    let toolbar = $("<div>").insertAfter(input);

    var quill = new Quill(editor[0], {
	modules: {
	    toolbar: [
		['bold', 'italic'],
		[{ 'list': 'ordered'}, { 'list': 'bullet' }],
		['link'],
		['clean'],
	    ]
	},
	placeholder: "Compose your message here...",
	theme: 'snow'
    });
    quill.on('text-change', () => {
        input.val(editor.children(".ql-editor").html());
    });
});
