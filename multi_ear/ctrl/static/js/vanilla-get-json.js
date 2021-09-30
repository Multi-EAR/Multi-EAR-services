/*
 * Usage:
 * getJSON("https://jsonplaceholder.typicode.com/comments", { postId: 1})
 *  .then(data => {
 *    console.log(data);
 *  });
 */

function getJSON(url, qs_params) {

    function buildQueryString(params) {

      return Object.entries(params).map(d => `${d[0]}=${d[1]}`).join('&');

    }

    return new Promise((resolve, reject) => {

        const qs = qs_params ? '?' + buildQueryString(qs_params) : '';
        const req = new XMLHttpRequest();

        req.open('GET', `${url}${qs}`);

        req.onload = function() {

            if (req.status >= 200 && req.status < 400) {

                resolve(JSON.parse(req.responseText));

            } else {

                resolve(req.responseText);

            }

        };

        req.onerror = () => reject(req.statusText);
        req.send();

    });

}
