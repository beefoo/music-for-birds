// Utility functions
(function() {
  window.UTIL = {};

  UTIL.freqToNote = function(freq) {
    var tuning = 440
    var lineal = 12 * ((Math.log(freq) - Math.log(tuning)) / Math.log(2))
    var midi = Math.round(69 + lineal)
    // return chromatic[midi % 12];
    return midi % 12;
  }

  UTIL.lerp = function(a, b, percent) {
    return (1.0*b - a) * percent + a;
  };

  UTIL.loadCsvData = function(csvFilename){
    var deferred = $.Deferred();
    Papa.parse(csvFilename, {
      download: true,
      header: true,
      dynamicTyping: true,
      skipEmptyLines: true,
      complete: function(results) {
        if (results.errors.length) console.log(results.errors[0].message);
        console.log("Found "+results.data.length+" rows in "+csvFilename);
        deferred.resolve(results.data);
      }
    });
    return deferred.promise();
  };

  UTIL.loadJsonData = function(jsonFilename){
    var deferred = $.Deferred();
    $.getJSON(jsonFilename, function(data) {
      console.log("Found "+data.length+" entries in "+jsonFilename);
      deferred.resolve(data);
    }).fail(function() {
      console.log("No data found in "+jsonFilename);
      deferred.resolve([]);
    });
    return deferred.promise();
  };

  UTIL.norm = function(value, a, b){
    var denom = (b - a);
    if (denom > 0 || denom < 0) {
      return (1.0 * value - a) / denom;
    } else {
      return 0;
    }
  };

  UTIL.parseNumber = function(str){
    var isNum = /^[\d\.]+$/.test(str);
    if (isNum && str.indexOf(".") >= 0) return parseFloat(str);
    else if (isNum) return parseInt(str);
    else return str;
  };

})();
