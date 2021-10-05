/* global bootstrap: false */

function switchWiFiMode() {

    var toggle = document.querySelector('#wirelessAccessPoint')

    toggle.addEventListener('click', function (event) {

        var action, resp

        action = toggle.checked ? 'enable' : 'disable'
        resp = confirm("Are you sure to " + action + " the wireless access point mode?\n\nThis will reboot the device.")

        if (resp == false) {
            event.preventDefault();
            event.stopPropagation();
            return false;
        }

        action = toggle.checked ? 'Enabling' : 'Disabling'
        alert(action + " wireless access point mode.\n\nThe device will reboot automatically in 5 sec.")

/*
        getJSON("/_switch_wifi_mode")
        .then(data => {
            console.log(data);
        });
*/

    }, false)

}


function validateWiFiForm() {

    // Fetch all the forms we want to apply custom Bootstrap validation styles to
    var forms = document.querySelectorAll('.needs-validation')

    // Loop over them and prevent submission
    Array.prototype.slice.call(forms)
    .forEach(function (form) {

        form.addEventListener('submit', function (event) {

            event.preventDefault();
            event.stopPropagation();

            if (form.checkValidity()) {
                processWifiForm(form)
                form.querySelector('button[type=submit]').disabled = true
            }

            form.classList.add('was-validated')

        }, false)

        form.addEventListener('reset', function (event) {
            form.reset()
            form.classList.remove('was-validated')
            form.querySelector('button[type=submit]').disabled = false;
        }, false)

    })
}


function processWifiForm(form) {
    ssid = form.elements["inputSSID"].value
    psk = form.elements["inputPSK"].value
    alert("ssid = " + ssid + "; psk = " + psk);
}


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

    var service, response, stat
    var obj_status, obj_response

    getJSON("/_status")
    .then(function(data) {

        for (const [service, response] of Object.entries(data)) {

            obj_status = document.querySelector('#' + service + '-status')
            obj_response = document.querySelector('#' + service + '-response > .accordion-body')

            if (!response.success) {
                obj_response.innerHTML = response.stderr
                obj_status.innerHTML = 'Not found'
                continue;
            }
            obj_response.innerHTML = response.stdout
            stat = response.stdout.substring(
                response.stdout.indexOf('Active: ') + 8,
                response.stdout.indexOf(' since '),
            )
            obj_status.innerHTML = stat
            if (stat.includes('active')) {
                if (obj_status.classList.contains('bg-secondary')) {
                    obj_status.classList.replace('bg-secondary', 'bg-success')
                }
                if (obj_status.classList.contains('bg-danger')) {
                    obj_status.classList.replace('bg-danger', 'bg-success')
                }
            } else {
                if (obj_status.classList.contains('bg-secondary')) {
                    obj_status.classList.replace('bg-secondary', 'bg-danger')
                }
                if (obj_status.classList.contains('bg-success')) {
                    obj_status.classList.replace('bg-success', 'bg-danger')
                }
            }
        }

    })

}


function loadDashboard() {
  // Graphs
  var ctx = document.getElementById('myChart')
  // eslint-disable-next-line no-unused-vars
  var myChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: [
        'Sunday',
        'Monday',
        'Tuesday',
        'Wednesday',
        'Thursday',
        'Friday',
        'Saturday'
      ],
      datasets: [{
        data: [
          15339,
          21345,
          18483,
          24003,
          23489,
          24092,
          12034
        ],
        lineTension: 0,
        backgroundColor: 'transparent',
        borderColor: '#00a6d6',
        borderWidth: 4,
        pointBackgroundColor: '#00a6d6'
      }]
    },
    options: {
      scales: {
        yAxes: [{
          ticks: {
            beginAtZero: false
          }
        }]
      },
      legend: {
        display: false
      }
    }
  })
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
            case "dashboard-tab":
                console.log("dashboard script")
                loadDashboard()
            case "wifi-tab":
                console.log("wifi script")
                showPasswordToggle()
                validateWiFiForm()
                switchWiFiMode()
            case "status-tab":
                console.log("status script")
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

    // prevent page reload
    window.onbeforeunload = function(event) {
        event.preventDefault();
    }

})()
