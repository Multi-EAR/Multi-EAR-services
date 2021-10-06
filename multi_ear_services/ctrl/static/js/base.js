/* global bootstrap: false */
function switchWiFiMode() {

    let toggle = document.querySelector('#wirelessAccessPoint')
    toggle.addEventListener('click', function (event) {

        var action, resp

        action = toggle.checked ? 'enable' : 'disable'
        resp = confirm("Are you sure to " + action +
                       " the wireless access point mode?\n\nThis will reboot the device.")

        if (resp == false) {
            event.preventDefault();
            event.stopPropagation();
            return false;
        }

        alert(toggle.checked ? 'Enabling' : 'Disabling' + 
              " wireless access point mode.\n\nThe device will reboot automatically in 5 sec.")

        getJSON("/_wlan_access_point", { action: action  } , 'POST')
        .then(data => {
            console.log(data);
        });

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
    var ssid = form.elements["inputSSID"].value
    var psk = form.elements["inputPSK"].value
    getJSON("/_wpa_supplicant", { ssid: ssid, passphrase: psk }, 'POST')
    .then(data => {
        console.log(data);
    });
}


function statusUpdateLoop(content) {
    // init
    let id = null;
    let width = 0;

    clearInterval(id);

    const pb = document.querySelector('#update')

    if (pb === null) { return; }

    id = setInterval(frame, 150);  // ms, times 100 gives 15s

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

    getJSON("/_systemd_status", { service: all })
    .then(function(data) {

        for (const [service, response] of Object.entries(data)) {

            var obj_status = document.querySelector('#' + service + '-status')
            var obj_response = document.querySelector('#' + service + '-response > .accordion-body')

            if (response.returncode === null ) continue

            if (response.stdout === "") {
                obj_response.innerHTML = response.stderr
                obj_status.innerHTML = 'not found'
                if (!obj_status.classList.contains('bg-secondary')) {
                    obj_status.classList.remove('bg-success', 'bg-warning', 'bg-danger')
                    obj_status.classList.add('bg-secondary')
                }
                continue;
            }
            obj_response.innerHTML = response.stdout
            obj_status.innerHTML = response.status

            if (response.status.includes('activating') || response.status.includes('inactive')) {
                if (!obj_status.classList.contains('bg-warning')) {
                    obj_status.classList.remove('bg-secondary', 'bg-success', 'bg-danger')
                    obj_status.classList.add('bg-warning')
                }
            } else if (response.status.includes('active')) {
                if (!obj_status.classList.contains('bg-success')) {
                    obj_status.classList.remove('bg-secondary', 'bg-warning', 'bg-danger')
                    obj_status.classList.add('bg-success')
                }
            } else {
                if (!obj_status.classList.contains('bg-danger')) {
                    obj_status.classList.remove('bg-secondary', 'bg-success', 'bg-warning')
                    obj_status.classList.add('bg-danger')
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
    if (tab === undefined) var tab = document.querySelector('#nav-tabs > .active')

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
                loadDashboard()
                break;
            case "wifi-tab":
                switchWiFiMode()
                showPasswordToggle()
                validateWiFiForm()
                break;
            case "status-tab":
                statusUpdate()
                statusUpdateLoop()
                break;
            default:
                // do nothing
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
        //var tooltip = new bootstrap.Tooltip(tab, {delay: { "show": 1000, "hide": 500 }});

        tab.addEventListener('shown.bs.tab', function (event) {
            loadTabContent(tab);
        })

    })

    // prevent page reload
    window.onbeforeunload = function(event) {
        event.preventDefault();
    }

})()
