/* global bootstrap: false */

function resetWifiForm(form) {
    form.reset()
    form.classList.remove('was-validated')
    form.querySelector('button[type=submit]').disabled = false;
}

function validateWifiForm() {

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
            resetWifiForm(form)
        }, false)

    })
}


function processWifiForm(form) {

    var ssid = form.elements["inputSSID"].value
    var psk = form.elements["inputPSK"].value

    getJSON("/_wpa_supplicant", { ssid: ssid, passphrase: psk }, 'POST')
    .then(data => {
        if (data === null) return
        console.log(data);
        alert("\"" + ssid + "\" added to the list of known wireless networks.")
        resetWifiForm(form)
    });
}


function statusUpdateLoop() {

    const progressbar = document.querySelector('#statusUpdater')
    if (progressbar === null) { return; }

    clearInterval(statusUpdater);
    let width = 0;

    statusUpdater = setInterval(progressBarWidth, 100);  // ms, times 100 gives 10s

    function progressBarWidth() {
        if (width == 100) {
            width = 0;
            statusUpdate()
        } else {
            width++;
        }
        progressbar.style.width = width + '%'; 
      }
}


function statusUpdate() {

    getJSON("/_systemd_status", { service: '*' })
    .then(function(data) {

        if (data === null) return

        for (const [service, response] of Object.entries(data)) {

            var id = '#' + service.replace('.', '-')
            var obj_status = document.querySelector(id + '-status')
            var obj_response = document.querySelector(id + '-response > .accordion-body')

            if (response.returncode === null) continue

            if (response.returncode === 4) {
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

           if (response.returncode === 0) {
                if (!obj_status.classList.contains('bg-success')) {
                    obj_status.classList.remove('bg-secondary', 'bg-warning', 'bg-danger')
                    obj_status.classList.add('bg-success')
                }
            } else if (response.status.includes('activating') || response.status.includes('inactive')) {
                if (!obj_status.classList.contains('bg-warning')) {
                    obj_status.classList.remove('bg-secondary', 'bg-success', 'bg-danger')
                    obj_status.classList.add('bg-warning')
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


function loadContent(nav) {

    // nav object set?
    if (nav === undefined) var nav = document.querySelector('#navLeft > .active')

    // get nav-content div
    var content = document.querySelector('#nav-content');

    // clear content on load
    content.innerHTML = ''

    // stop status progressbar interval
    clearInterval(statusUpdater);

    // lazy load new content and trigger nav related functions
    getJSON("/_tab/" + nav.getAttribute("aria-controls"))
    .then(function(data) {
        if (data === null) return
        content.innerHTML = data.html
    })
    .finally(function() {
        switch (nav.getAttribute("aria-controls")) {
            case "dashboard":
                loadDashboard()
                break;
            case "wifi":
                showPasswordToggle()
                validateWifiForm()
                break;
            case "status":
                statusUpdate()
                statusUpdateLoop()
                break;
            default:
                // do nothing
        }
    });
}

// globals
let statusUpdater = null;

(function () {
    'use strict'
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    tooltipTriggerList.forEach(function (tooltipTriggerEl) {
        new bootstrap.Tooltip(tooltipTriggerEl)
    })

    loadContent();

    var navLeft = [].slice.call(document.querySelectorAll('#navLeft > button[data-bs-toggle="tab"]'))
    navLeft.forEach(function (nav) {
        nav.addEventListener('shown.bs.tab', function (event) {
            loadContent(nav);
            var navTOld = document.querySelector('#navTop > ul > li > a.nav-link.active[aria-controls]')
            navTOld.classList.remove('active')
            var navTNew = document.querySelector('#navTop > ul > li > a.nav-link[aria-controls="' + nav.getAttribute("aria-controls") + '"]')
            navTNew.classList.add('active')
        })
    })

    var navTop = [].slice.call(document.querySelectorAll('#navTop > ul > li > a.nav-link[aria-controls]'))
    navTop.forEach(function (nav) {
        nav.addEventListener('click', function (event) {
            loadContent(nav);
            var navTOld = document.querySelector('#navTop > ul > li > a.nav-link.active[aria-controls]')
            navTOld.classList.remove('active')
            nav.classList.add('active')
            var navLOld = document.querySelector('#navLeft > button.nav-link.active[aria-controls]')
            navLOld.classList.remove('active')
            var navLNew = document.querySelector('#navLeft > button.nav-link[aria-controls="' + nav.getAttribute("aria-controls") + '"]')
            navLNew.classList.add('active')
            return false;
        })
    })

    // prevent page reload
    window.onbeforeunload = function(event) {
        event.preventDefault();
    }

})()
