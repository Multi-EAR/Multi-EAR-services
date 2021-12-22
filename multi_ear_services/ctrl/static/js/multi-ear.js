/* global bootstrap: false */
let debug = window.location.hostname == '127.0.0.1'
let host = debug ? 'http://multi-ear-' + window.prompt("Enter Multi-EAR id for dev","3001") + '.local' : ''
let statusUpdater = null;
let sensorDataUpdater = null;


Highcharts.setOptions({
    global: { useUTC: true }
})


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

    wifiSecret()
        .then(secret => {

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

    wifiSecret()
        .then(secret => {

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

    getResponse('/_systemd_status', { service: '*' })
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


function fetchSensorData(end) {

    // console.log('Fetch sensordata')

    var fetchButton = document.getElementById('sensorDataFetch')
    fetchButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Loading...'
    fetchButton.disabled = true

    if (end === undefined) {
        end = new Date().toISOString().substring(0, 19)
        var sendorDataEnd = document.getElementById('sensorDataEnd')
        sensorDataEnd.value = end
    }

    var duration = document.getElementById('sensorDataDuration').value
    var decimate = document.getElementById('sensorDataDuration').getAttribute('data-decimate')

    fetch(`${host}/api/dataselect/query?field=^&start=${duration}&end=${end}&format=json`)
        .then(res => res.status == 200 && res.json())
        .then(json => updateCharts(json))

}


async function updateChart(chart, sensorData) {

    let canvas = await chart.renderTo

    if (canvas.getAttribute('data-source') !== 'multi_ear') return

    let addSeries = chart.series.length == 0
    let dataNames = canvas.getAttribute('data-series').split(',')
    let dataScalar = canvas.getAttribute('data-scalar').split(',')
    let dataOffset = canvas.getAttribute('data-offset').split(',')
    let dataSeries = []

    dataNames.forEach( function(name, index) {

        let scalar = eval(dataScalar[index])
        let offset = eval(dataOffset[index])
        let columnIndex = sensorData.columns.indexOf('multi_ear_' + name)

        if (columnIndex === -1) return

        let data = sensorData.data.map( function (row, rowIndex) {
            return [sensorData.index[rowIndex], offset + scalar * row[columnIndex]]
        })

        series = {name: name, data: data}
        addSeries ? chart.addSeries(series) : dataSeries.push(series)

    })

    if (!addSeries) chart.update({series: dataSeries})
    chart.redraw()
    chart.hideLoading()

}


async function updateCharts(sensorData) {

    // console.log('Update sensordata charts')
    if (sensorData === false) {
        window.alert('No sensor data returned')
    } else {
        Highcharts.charts.forEach(chart => updateChart(chart, sensorData))
    }

    var fetchButton = document.getElementById('sensorDataFetch')
    fetchButton.innerHTML = 'Request and plot'
    fetchButton.disabled = false

}


function startSensorDataUpdater() {

    // console.log('Start sensordata interval update')
    window.clearInterval(sensorDataUpdater);
    sensorDataUpdater = setInterval(fetchSensorData, 15000);  // ms, every 15s

    var utcToggle = document.getElementById('useUTC')
    utcToggle.disabled = false

}


function stopSensorDataUpdater() {

    // console.log('Stop sensordata interval update')
    window.clearInterval(sensorDataUpdater);

}


/**
 * Synchronize zooming through the setExtremes event handler.
 */
function syncChartExtremes(e) {
    var thisChart = this.chart;

    if (e.trigger !== 'syncChartExtremes') { // Prevent feedback loop
        Highcharts.each(Highcharts.charts, function (chart) {
            if (chart !== thisChart) {
                if (chart.xAxis[0].setExtremes) { // It is null while updating
                    chart.xAxis[0].setExtremes(
                        e.min,
                        e.max,
                        undefined,
                        false,
                        { trigger: 'syncChartExtremes' }
                    );
                }
            }
        });
    }
}

// https://www.highcharts.com/demo/synchronized-charts

function loadDashboard() {

    // timeseries graph
    var canvas = document.getElementById('sensorDataWS')
    let graph = new TimeseriesGraph(canvas, 15 * 30)

    // initialize charts
    let charts = [].slice.call(document.querySelectorAll('[data-source="multi_ear"]'))

    charts.forEach(chart => {

        let title = chart.getAttribute('data-title')
        let units = chart.getAttribute('data-units')

        Highcharts.chart({
            chart: { renderTo: chart.id, type: 'line', zoomType: 'x', backgroundColor: 'none' },
            credits: { enabled: false },
            tooltip: {
                pointFormat: '{point.y} ' + units,
                shadow: false,
                //valueDecimals: 2
            },
            xAxis: { type: 'datetime', events: { setExtremes: syncChartExtremes } },
            yAxis: { title: { text: `${title} [${units}]` } },
            title: { text: title },
        }).showLoading();

    })

    // Fetch all sensordata of last two minutes and update charts
    fetchSensorData()

    // Enable toggles
    var updateToggle = document.getElementById('sensorDataUpdate')
    updateToggle.addEventListener('click', function (event) {
        updateToggle.checked ? startSensorDataUpdater() : stopSensorDataUpdater()
    })

    var utcToggle = document.getElementById('useUTC')
    utcToggle.addEventListener('click', function (event) {
        Highcharts.charts.forEach(chart => {
            chart.update({time: {useUTC: utcToggle.checked}})
        })
    })

    // Enable fetch button
    var fetchButton = document.getElementById('sensorDataFetch')
    fetchButton.addEventListener('click', function (event) {

        var endtime = document.getElementById('sensorDataEnd').value

        fetchSensorData(endtime)

        stopSensorDataUpdater()
        updateToggle.checked = false
    })

    // Telegraf system-load chart
    Highcharts.chart('chart-system-load', {
        chart: {
            type: 'spline',
            zoomType: 'x',
            backgroundColor: 'none',
        },
        data: {
            csvURL: `${host}/api/dataselect/query?d=telegraf&m=system&f=load*&s=30m&_f=csv`,
            dataRefreshRate: 30,
            enablePolling: true,
            parseDate: Date.parse,
        },
        tooltip: {
            valueDecimals: 3
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
        credits: { 
            enabled: false
        },
    });

    // Telegraf memory-usage chart
    Highcharts.chart('chart-memory-usage', {
        chart: {
            type: 'spline',
            zoomType: 'x',
            backgroundColor: 'none',
        },
        data: {
            csvURL: `${host}/api/dataselect/query?d=telegraf&m=mem&f=used,buffered,cached,free&s=30m&_f=csv`,
            dataRefreshRate: 30,
            enablePolling: true,
            parseDate: Date.parse,
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
        credits: { 
            enabled: false
        },
    });

    // update sensor data
    startSensorDataUpdater()

}


function stopCharts(tab) {

    if (tab === "dashboard") return

    stopSensorDataUpdater()

    Highcharts.charts.forEach(chart => {

        if (chart === undefined) return

        window.clearInterval(chart)
        chart.destroy()

    })

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
    window.clearInterval(statusUpdater);

    // lazy load new content and trigger nav related functions
    getResponse("/_tab/" + tab)
        .then(function(resp) {

            if (resp.status !== 200) { console.log(resp); return; }
            content.innerHTML = JSON.parse(resp.responseText).html

        })
        .finally(function() {

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

            // stop charts if not dashboard tab
            stopCharts(tab)

        });

}


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
