/* global bootstrap: false */



/*
function getWiFiMode() {
    getJSON("/_get_wifi_mode"), {})
    .then(data => {
        console.log(data);
    });
}

function switchWiFiMode() {
    var r = confirm("Are you sure?");
    if (r == false) {
        return;
    }
    getJSON("/_switch_wifi_mode"), {})
    .then(data => {
        console.log(data);
    });
}
*/



function statusUpdateLoop(content) {
    // init
    let id = null;
    let width = 0;

    clearInterval(id);

    const pb = document.querySelector('#update')

    if (pb === null) { return; }

    id = setInterval(frame, 100);

    function frame() {
        if (width == 100) {
            width = 0;
            statusUpdate(content)
        } else {
            width++;
        }
        pb.style.width = width + '%'; 
      }
}


function statusUpdate() {

}


function loadTabContent(tab) {
    // nav-tab set?
    if (tab === undefined) {
        var tab = document.querySelector('#nav-tabs > .active')
    }

    // get nav-content div
    var content = document.querySelector('#nav-content');

    // clear content on load
    content.innerHTML = '' 

    // lazy load new content and trigger tab related functions
    getJSON("/_tab/" + tab.getAttribute("aria-controls"))
    .then(function(data) {
        content.innerHTML = data.html
    })
    .finally(function() {
        switch (tab.id) {
            case "wifi-tab":
                console.log("wifi code")
                showPasswordToggle()
            case "status-tab":
                console.log("status code")
                statusUpdate()
                statusUpdateLoop()
        }
    });
}

(function () {
    'use strict'
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    tooltipTriggerList.forEach(function (tooltipTriggerEl) {
        new bootstrap.Tooltip(tooltipTriggerEl)
    })

    loadTabContent();

    var tabList = [].slice.call(document.querySelectorAll('#nav-tabs > button[data-bs-toggle="tab"]'))
    tabList.forEach(function (tab) {

        //statements suspected to throw exception.
        var tooltip = new bootstrap.Tooltip(tab, {delay: { "show": 1000, "hide": 500 }});

        tab.addEventListener('shown.bs.tab', function (event) {
            loadTabContent(tab);
        })

    })

})()
