/*
 * Usage:
 * getJSON("https://jsonplaceholder.typicode.com/comments", { postId: 1}, 'GET'| 'POST')
 *  .then(data => {
 *    console.log(data);
 *  });
 */

function getJSON(url, qs_params, qs_type) {

    function buildQueryString(params) {

      return Object.entries(params).map(d => `${d[0]}=${d[1]}`).join('&');

    }

    return new Promise((resolve, reject) => {

        const qs = qs_params ? '?' + buildQueryString(qs_params) : '';
        const type = qs_type ? qs_type : 'GET';
        const req = new XMLHttpRequest();

        req.open(type, `${url}${qs}`);

        req.onload = function() {

            resolve(req)

            /*
            if (req.status >= 200 && req.status < 400) {

                resolve(JSON.parse(req.responseText));

            } else {

                resolve(req.responseText);

            }
            */

        };

        req.onerror = () => reject(req.statusText);
        req.send();

    });

}
