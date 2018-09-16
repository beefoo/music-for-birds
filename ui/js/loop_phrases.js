'use strict';

var AppLoopPhrases = (function() {

  function AppLoopPhrases(config) {
    var defaults = {
      dataFile: "/data/output/birds_audio_phrase_stats_query.csv",
      audioDir: "/audio/downloads/birds/",
      audioExt: ".mp3",
      savedFile: "/data/usergen/saved_birds.json",
      saveFile: "/data/usergen/saved_bird_loops.json",
      saveUrl: "/save",
      colors: [
        [120, 28, 129],
        [70, 41, 135],
        [63, 89, 169],
        [70, 134, 194],
        [88, 164, 172],
        [115, 181, 128],
        [149, 189, 94],
        [185, 189, 74],
        [214, 177, 62],
        [229, 146, 53],
        [229, 94, 43],
        [217, 33, 32]
      ]
    };
    this.opt = _.extend({}, defaults, config);
    this.init();
  }

  function freqToNote(freq) {
    var tuning = 440
    var lineal = 12 * ((Math.log(freq) - Math.log(tuning)) / Math.log(2))
    var midi = Math.round(69 + lineal)
    // return chromatic[midi % 12];
    return midi % 12;
  }

  function lerp(a, b, percent) {
    return (1.0*b - a) * percent + a;
  }

  function loadCsvData(csvFilename){
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
  }

  function loadJsonData(jsonFilename){
    var _this = this;
    var deferred = $.Deferred();
    $.getJSON(jsonFilename, function(data) {
      console.log("Found "+data.length+" entries in "+jsonFilename);
      deferred.resolve(data);
    }).fail(function() {
      console.log("No data found in "+jsonFilename);
      deferred.resolve([]);
    });
    return deferred.promise();
  }

  function norm(value, a, b){
    var denom = (b - a);
    if (denom > 0 || denom < 0) {
      return (1.0 * value - a) / denom;
    } else {
      return 0;
    }
  }

  function parseNumber(str){
    var isNum = /^[\d\.]+$/.test(str);
    if (isNum && str.indexOf(".") >= 0) return parseFloat(str);
    else if (isNum) return parseInt(str);
    else return str;
  }

  AppLoopPhrases.prototype.init = function(){
    this.$el = $("#app");
    this.$loops = $("#loops");

    this.data = [];
    this.savedData = [];
    this.loops = [];

    var _this = this;
    var dataPromise = loadCsvData(this.opt.dataFile);
    var savedDataPromise = loadJsonData(this.opt.savedFile);

    $.when.apply($, [dataPromise, savedDataPromise]).then(function(data, savedData){
      _this.data = _this.parseData(data);
      _this.savedData = savedData;
      _this.savedData.sort();
      _this.onReady();
    });
  };

  AppLoopPhrases.prototype.loadListeners = function(){
    var _this = this;

    $(window).on("resize", function(e){ _this.onResize(); });

    $(".toggle-phrase").on("click", function(e){
      e.preventDefault();
      _this.togglePhrase($(this));
    });
  };

  AppLoopPhrases.prototype.loadSound = function(filename, phrases, callback){
    var _this = this;
    var sprites = _.object(_.map(phrases, function(p, i){ return [""+i, [p.start, p.dur]]; }));
    var sound = this.sound;
    if (sound) sound.unload();
    var sound = new Howl({
      src: filename,
      sprite: sprites,
      onload: function(){ if (callback) { callback(this); } },
      onend: function(){ _this.progressing = false; }
    });
    this.sound = sound;
  };

  AppLoopPhrases.prototype.loadUi = function(){
    var parents = this.savedData;
    var data = _.filter(this.data, function(d){
      return parents.indexOf(d.parent) >= 0;
    });
    var colors = this.opt.colors;
    var hzs = _.pluck(data, "hzMean");
    var minHz = Math.floor(_.min(hzs));
    var maxHz = Math.ceil(_.max(hzs));

    var html = "";
    _.each(parents, function(parent, i){
      html += '<div class="phrase-group">';
        html += "<div>";
        var phrases = _.where(data, {parent: parent});
        _.each(phrases, function(phrase, j){
          var color = colors[freqToNote(phrase.hzMean)];
          var opacity = lerp(0.2, 1, norm(phrase.hzMean, minHz, maxHz));
          html += '<div class="phrase">';
            html += '<a href="#'+phrase.start+':'+phrase.dur+'" data-index="'+phrase.index+'" class="toggle-phrase" style="background: rgba('+color[0]+','+color[1]+','+color[2]+','+opacity+')"></a>';
          html += "</div>";
        });
        html += "</div>";
        html += "<h2>"+parent+"</h2>";
      html += "</div>";
    });

    this.$loops.html(html);
  };

  AppLoopPhrases.prototype.onReady = function(){
    this.loadUi();
    this.loadListeners();
  };

  AppLoopPhrases.prototype.onResize = function(){

  };

  AppLoopPhrases.prototype.parseData = function(data){
    var audioDir = this.opt.audioDir;
    var audioExt = this.opt.audioExt;
    return _.map(data, function(entry, i){
      entry.audioFile = audioDir + entry.parent + audioExt;
      entry.index = i;
      return entry;
    });
  };

  AppLoopPhrases.prototype.phraseOff = function(phrase){
    if (phrase.sound) {
      phrase.sound.unload();
    }
  };

  AppLoopPhrases.prototype.phraseOn = function(phrase){
    console.log(phrase)
    phrase.sound = new Howl({
      src: phrase.audioFile,
      volume: 0.5,
      sprite: {
        "phrase": [phrase.start, phrase.dur, true]
      },
      onload: function(){
        this.play("phrase");
      }
    });
  };

  AppLoopPhrases.prototype.togglePhrase = function($phrase){
    var $parent = $phrase.parent();
    $parent.toggleClass("active");
    var isActive = $parent.hasClass("active");
    var index = parseInt($phrase.attr("data-index"));
    var phrase = this.data[index];

    if (isActive) {
      this.phraseOn(phrase);
    } else {
      this.phraseOff(phrase);
    }
  };

  return AppLoopPhrases;

})();

$(function() {
  var app = new AppLoopPhrases({});
});
