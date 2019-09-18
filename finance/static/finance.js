"use strict";

$(() => {
    let dirty = false;
    
    window.addEventListener("beforeunload", (e) => {
	if (dirty) {
	    let msg = "Your unsaved changes will be lost.";
	    e.preventDefault();
	    e.returnValue = msg;
	    return msg;
	} else {
	    delete e["returnValue"];
	}
    });
    
    $(document.body).on("input", "input, select", (e) => {
	dirty = true;
    });
    
    $(document.body).on("submit", "form", (e) => {
	dirty = false;
    });
    
    window.setDirty = function(val) {
	dirty = val;
    }
});
