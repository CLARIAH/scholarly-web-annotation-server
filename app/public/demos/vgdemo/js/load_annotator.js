/*document.onreadystatechange = function () { // wait till page is loaded
    if (document.readyState === "complete") {
        console.log("document ready!");
        loadConfig((error, config) => { // load configuration file
            if (error)
                return null;
            // instantiate, configure and insert client
            annotator = new ScholarlyWebAnnotator.ScholarlyWebAnnotator(config);
            var viewerElement = document.getElementById('annotation-viewer');
            annotator.addAnnotationClient(viewerElement);
        });
    }
}
*/

/*document.onreadystatechange = function () { // wait till page is loaded
    if (document.readyState === "complete") {
        console.log("document ready!");
        loadConfig(function(error, config) { // load configuration file
            if (error)
                return null;
            // instantiate, configure and insert client
            annotator = new ScholarlyWebAnnotator.ScholarlyWebAnnotator(config);
            var viewerElement = document.getElementById('annotation-viewer');
            annotator.addAnnotationClient(viewerElement);
        });
    }
    console.log("annotator ready! (I hope)");

}



var loadConfig = function(callback) {
    fetch("annotator_config.json", {
        method: "GET"
    }).then(function(response) {
        return response.json();
    }).then(function(config) {
        return callback(null, config);
    }).catch(function(error) {
        return callback(error, null);
    });
}
*/
var configFile = "./annotator_config.json"; // location of the config file

document.onreadystatechange = function () { // wait till page is loaded
    if (document.readyState === "complete") {
        loadConfig(function(error, config) { // load configuration file
            if (error)
                return null;
            // instantiate, configure and insert client
            annotator = new ScholarlyWebAnnotator.ScholarlyWebAnnotator(config);
            var viewerElement = document.getElementById('swac-viewer');
            annotator.addAnnotationClient(viewerElement);
            console.log("added client");
        });
    }
    console.log("annotator ready! (I hope)");
}

var loadConfig = function(callback) {
    var xhr = new XMLHttpRequest();
    xhr.open("GET", configFile);
    xhr.onreadystatechange = function() {
        if (xhr.readyState === XMLHttpRequest.DONE) {
            try {
                var config = JSON.parse(xhr.responseText);
                return callback(null, config);
            } catch(error) {
                console.log(error);
                return callback(error, null);
            }
        }
    }
    xhr.send();
}
