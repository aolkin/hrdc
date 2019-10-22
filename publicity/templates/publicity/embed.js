(function() {
    let div = document.createElement('div');
    let script = document.scripts[document.scripts.length - 1];
    div.innerHTML = '{{ innerHtml|escapejs }}';
    script.parentElement.insertBefore(div, script);    
})();
