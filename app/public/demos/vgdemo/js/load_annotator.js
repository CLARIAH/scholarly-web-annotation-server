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
        });
    }
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
