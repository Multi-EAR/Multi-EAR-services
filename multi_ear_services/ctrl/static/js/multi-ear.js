/* global bootstrap: false */
let debug = window.location.hostname == '127.0.0.1'
let multiEAR = debug ? 'http://multi-ear-3001.local' : ''


function sleep(ms) {

    return new Promise(resolve => setTimeout(resolve, ms));

}


function resetWifiForm(form) {

    form.reset()
    form.classList.remove('was-validated')
    form.querySelector('button[type=submit]').disabled = false;

}


function validateWifiForm() {

    var form = document.getElementById('wifi-add')

    form.addEventListener('submit', function (event) {

        event.preventDefault();
        event.stopPropagation();

        if (form.checkValidity()) {

            append_wpa_supplicant(form)
            form.querySelector('button[type=submit]').disabled = true

        }

        form.classList.add('was-validated')

    }, false)

    form.addEventListener('reset', function (event) {

        resetWifiForm(form)

    }, false)

}


function wifiSecret() {

    var modal = new bootstrap.Modal(document.getElementById('wifi-modal'), {
        backdrop: 'static',
        keyboard: false,
        focus: true,
    })

    return new Promise(resolve => {

        modal.show()

        var form = modal._element.getElementsByTagName('form')[0]
        var secret = null

        form.addEventListener('submit', function (event) {

            event.preventDefault();
            event.stopPropagation();

            if (form.checkValidity()) {

                secret = CryptoJS.SHA256(form.elements["inputSECRET"].value).toString()

                form.removeEventListener('submit', null);

                modal.hide()

            }

            form.classList.add('was-validated')

        }, false)

        modal._element.addEventListener('hidden.bs.modal', function (event) {

            form.reset()
            resolve(secret)

        })

    });

}


function append_wpa_supplicant(form) {

    wifiSecret().then(secret => {

        if (secret === null) return

        var ssid = form.elements["inputSSID"].value
        var psk = form.elements["inputPSK"].value

        getResponse("/_append_wpa_supplicant", { ssid: ssid, passphrase: psk, secret: secret }, 'POST')
        .then(resp => {

            if (resp.status !== 200) {

                alert("Error: " + resp.responseText)

            } else {
    
                alert("\"" + ssid + "\" added to the list of known wireless networks.")
                resetWifiForm(form)

            }

        });

    });

}


function autohotspot() {

    wifiSecret().then(secret => {

        if (secret === null) return

        getResponse("/_autohotspot", { secret: secret }, 'POST')
        .then(resp => {

            if (resp.status !== 200) {

                alert("Error: " + resp.responseText)

            } else {

                alert("Wi-Fi autohotspot script triggered.\n\nConnection to the device could be lost.")

            }

        });

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

    getResponse("/_systemd_status", { service: '*' })
    .then(function(resp) {

        if (resp.status !== 200) return

        var data = JSON.parse(resp.responseText)

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


function bytes(bytes, label) {

    if (bytes == 0) return '';

    var s = ['bytes', 'KB', 'MB', 'GB', 'TB', 'PB'];
    var e = Math.floor(Math.log(bytes)/Math.log(1024));
    var value = ((bytes/Math.pow(1024, Math.floor(e))).toFixed(2));

    e = (e<0) ? (-e) : e;

    if (label) value += ' ' + s[e];

    return value;

}


var chart_pabs, chart_pdif, chart_ics, chart_acc
var chart_system_load, chart_memory_usage


function loadDashboard() {

    chart_pabs = Highcharts.chart('chart-pabs', {
        chart: {
            type: 'line',
            zoomType: 'x'
        },
        data: {
            csvURL: multiEAR + '/api/dataselect/query?d=multi_ear&m=multi_ear&f=LPS33HW&s=2m&_f=csv',
            enablePolling: true,
            dataRefreshRate: 5,
            parsed: function (columns) {
                columns[1] = columns[1].map(function (value, index) {
                    return (index === 0) ? value : value/4096
                })
            },
        },
        tooltip: {
            valueDecimals: 2
        },
        xAxis: {
            type: 'datetime'
        },
        yAxis: {
            title: {
                text: 'Absolute pressure [hPa]',
            },
        },
        title: {
            text: 'Absolute Pressure'
        },
    });

    chart_pdif = Highcharts.chart('chart-pdif', {
        chart: {
            type: 'line',
            zoomType: 'x'
        },
        data: {
            csvURL: multiEAR + '/api/dataselect/query?d=multi_ear&m=multi_ear&f=DLVR,SP210&s=2m&_f=csv',
            enablePolling: true,
            dataRefreshRate: 5,
            parsed: function (columns) {
                columns[1] = columns[1].map(function (value, index) {
                    return (index === 0) ? value : value * 250 / 655300
                })
                columns[2] = columns[2].map(function (value, index) {
                    return (index === 0) ? value : value * 249.08 / ( 0.9 * 32768 )
                })

            },
        },
        tooltip: {
            valueDecimals: 2
        },
        xAxis: {
            type: 'datetime'
        },
        yAxis: {
            title: {
                text: 'Differential pressure [Pa]',
            },
        },
        title: {
            text: 'Differential Pressure'
        },
    });

    chart_ics = Highcharts.chart('chart-ics', {
        chart: {
            type: 'line',
            zoomType: 'x'
        },
        data: {
            csvURL: multiEAR + '/api/dataselect/query?d=multi_ear&m=multi_ear&f=^ICS&s=2m&_f=csv',
            enablePolling: true,
            dataRefreshRate: 5,
            parsed: function (columns) {
                columns[1] = columns[1].map(function (value, index) {
                    return (index === 0) ? value : value * 100 / 4096
                })
            },
        },
        tooltip: {
            valueDecimals: 1
        },
        xAxis: {
            type: 'datetime'
        },
        yAxis: {
            title: {
                text: '?? [??]',
            },
        },
        title: {
            text: 'Sound Pressure Level'
        },
    });

    chart_acc = Highcharts.chart('chart-acc', {
        chart: {
            type: 'line',
            zoomType: 'x'
        },
        data: {
            csvURL: multiEAR + '/api/dataselect/query?d=multi_ear&m=multi_ear&f=^LIS3DH&s=2m&_f=csv',
            enablePolling: true,
            dataRefreshRate: 5,
            parsed: function (columns) {
                for (let i = 1; i <= 3; i++) {
                    columns[i] = columns[i].map(function (value, index) {
                        return (index === 0) ? value : value * 0.076
                    })
                }
            },
        },
        tooltip: {
            valueDecimals: 2
        },
        xAxis: {
            type: 'datetime'
        },
        yAxis: {
            title: {
                text: 'Acceleration [mg]',
            },
        },
        title: {
            text: 'Acceleration'
        },
    });

    chart_system_load = Highcharts.chart('chart-system-load', {
        chart: {
            type: 'spline',
            zoomType: 'x'
        },
        data: {
            csvURL: multiEAR + '/api/dataselect/query?d=telegraf&m=system&f=load*&s=30m&_f=csv',
            enablePolling: true,
            dataRefreshRate: 30,
        },
        tooltip: {
            valueDecimals: 2
        },
        xAxis: {
            type: 'datetime'
        },
        yAxis: {
            min: 0,
            title: {
                text: 'System load [-]',
            },
        },
        title: {
            text: 'System load'
        },
    });

    chart_memory_usage = Highcharts.chart('chart-memory-usage', {
        chart: {
            type: 'spline',
            zoomType: 'x'
        },
        data: {
            csvURL: multiEAR + '/api/dataselect/query?d=telegraf&m=mem&f=used,buffered,cached,free&s=30m&_f=csv',
            enablePolling: true,
            dataRefreshRate: 30,
        },
        tooltip: {
            formatter: function() { return bytes(this.y, true); }
        },
        xAxis: {
            type: 'datetime'
        },
        yAxis: {
            title: {
                text: 'Memory usage',
            },
            labels: {
                formatter: function() { return bytes(this.value, true); }
            },
        },
        title: {
            text: 'Memory usage'
        },
    });

}


function stopChart(chart) {

    if (chart !== undefined) {

        chart.data.options['enablePolling'] = false
        chart.destroy()
        chart = undefined

    }

    return chart

}


function stopDashboard() {

    chart_pabs = stopChart(chart_pabs)
    chart_pdif = stopChart(chart_pdif)
    chart_ics = stopChart(chart_ics)
    chart_acc = stopChart(chart_acc)
    chart_system_load = stopChart(chart_system_load)
    chart_memory_usage = stopChart(chart_memory_usage)

}


function loadPCB () {

    resizePCB()

    var pcbItems = [].slice.call(document.querySelectorAll('.pcb > svg > *'))

    var pcbPopovers = pcbItems.map(function (item) {

        var id = item.id.replace('PCB-', '')

        var popover = new bootstrap.Popover(item, {
            placement: 'left',
            trigger: 'hover focus',
        })

        var dl = document.querySelector('#' + id)

        if (dl !== null) {

            dl.addEventListener('mouseenter', function () {
                popover.show()
            })
            dl.addEventListener('mouseleave', function () {
                popover.hide()
            })

        }

        return popover
    })

}


async function resizePCB () {

    var pcbImg = document.querySelector('.pcb > img')
    var pcbSvg = document.querySelector('.pcb > svg')

    if (pcbImg === null | pcbSvg === null) return

    while (pcbImg.width == 0) { await sleep(100); }

    let w = pcbImg.width
    let h = pcbImg.height

    pcbSvg.style.width = w + "px"
    pcbSvg.style.height = h + "px"
    pcbSvg.setAttribute("viewbox", [0, 0, w, h])

}


function loadContent(nav) {

    // nav object set?
    if (nav === undefined) var nav = document.querySelector('#navbar > ul > li > a.active')

    // extract tab
    var tab = nav.getAttribute("data-bs-target")

    // get nav-content div
    var content = document.querySelector('#content');

    // clear content on load
    content.innerHTML = ''

    // stop status progressbar interval
    clearInterval(statusUpdater);

    // lazy load new content and trigger nav related functions
    getResponse("/_tab/" + tab)
    .then(function(resp) {

        if (resp.status !== 200) { console.log(resp); return; }
        content.innerHTML = JSON.parse(resp.responseText).html

    })
    .finally(function() {

        stopDashboard()

        switch (tab) {

            case "pcb":
                loadPCB()
                break;

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

        // activate tooltips
        var tooltips = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
        tooltips.forEach(function (tooltip) { new bootstrap.Tooltip(tooltip, { placement: 'bottom' }) })

    });

}


// globals
let statusUpdater = null;

(function () {

    'use strict'

    loadContent();

    var navbar = new bootstrap.Collapse(document.querySelector('#navbar'), {toggle: false})

    var navs = [].slice.call(document.querySelectorAll('#navbar > ul > li > a[data-bs-toggle="tab"]'))

    navs.forEach(function (nav) {

        nav.addEventListener('shown.bs.tab', function (event) {

            loadContent(nav);
            navbar.hide();

        })

    })

    window.addEventListener("resize", resizePCB);

    // prevent page reload
    window.onbeforeunload = function(event) {

        event.preventDefault();

    }

})()
