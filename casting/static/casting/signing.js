"use strict";

let cc = {};
cc.dirty = false;

$(function () {
    $("select").change(function () {
        cc.dirty = true;
    });
    $("[type=submit]").on("click keyup submit", function (e) {
        if (!confirm(
            "Are you sure you want to submit these responses? " +
                "They are binding and cannot be changed later.\n\n" +
                "YOU MAY ONLY ACCEPT ONE ROLE PER SHOW " +
                "(unless indicated otherwise).\n\n" +
                '(Anything left as "No Response" can be changed later.)')) {
            e.preventDefault();
            return false;
        }
        cc.dirty = false;
    });
    window.onbeforeunload = function () {
        if (cc.dirty) {
            return "You have not submitted your signing choices!";
        }
    }
});