'use strict';

var AppQueryPhrases = (function() {

  function AppQueryPhrases(config) {
    var defaults = {
      dataFile: "/data/output/birds_audio_phrase_stats_query.csv",
      audioDir: "/audio/downloads/birds/",
      audioExt: ".mp3",
      resultLimit: 100
    };
    this.opt = _.extend({}, defaults, config);
    this.init();
  }

  function parseNumber(str){
    var isNum = /^[\d\.]+$/.test(str);
    if (isNum && str.indexOf(".") >= 0) return parseFloat(str);
    else if (isNum) return parseInt(str);
    else return str;
  }

  AppQueryPhrases.prototype.init = function(){
    this.$el = $("#app");

    var _this = this;
    var dataPromise = this.loadData(this.opt.dataFile);
    this.ranges = {};

    $.when.apply($, [dataPromise]).then(function(){
      _this.onReady();
      _this.loadListeners();
    });
  };

  AppQueryPhrases.prototype.loadData = function(csvFilename){
    var _this = this;
    var deferred = $.Deferred();

    Papa.parse(csvFilename, {
      download: true,
      header: true,
      dynamicTyping: true,
      skipEmptyLines: true,
      complete: function(results) {
        if (results.errors.length) {
          console.log(results.errors[0].message);
        }
        console.log("Found "+results.data.length+" rows");
        _this.data = _this.parseData(results.data);
        _this.rowCount = results.data.length;
        // console.log(_this.data);
        deferred.resolve();
      }
    });

    return deferred.promise();
  };

  AppQueryPhrases.prototype.loadListeners = function(){
    var _this = this;
  };

  AppQueryPhrases.prototype.loadSlider = function($slider){
    var _this = this;
    var key = $slider.attr('data-key');
    var $target = $($slider.attr('data-target'));

    // get min max in data
    var values = _.pluck(this.data, key);
    var minValue = Math.floor(_.min(values));
    var maxValue = Math.ceil(_.max(values));

    this.ranges[key] = [minValue, maxValue];

    $target.val(minValue + " - " + maxValue);
    $slider.slider({
      range: true,
      min: minValue,
      max: maxValue,
      values: [minValue, maxValue],
      slide: function(e, ui) {
        _this.onSlide(ui.values[0], ui.values[1], key, $target);
      }
    });

  };

  AppQueryPhrases.prototype.loadUi = function(){
    var _this = this;
    $('.slider').each(function(){
      _this.loadSlider($(this));
    });
  };

  AppQueryPhrases.prototype.onReady = function(){
    this.loadUi();
    this.query();
  };

  AppQueryPhrases.prototype.onSlide = function(minValue, maxValue, key, $target) {
    $target.val(minValue + " - " + maxValue);
    this.ranges[key] = [minValue, maxValue];
    this.query();
  }

  AppQueryPhrases.prototype.parseData = function(data){
    var audioDir = this.opt.audioDir;
    var audioExt = this.opt.audioExt;
    return _.map(data, function(entry, i){
      entry.audioFile = audioDir + entry.parent + audioExt;
      entry.index = i;
      return entry;
    });
  };

  AppQueryPhrases.prototype.play = function(entry){
    if (entry.index !== this.soundIndex) {
      if (this.sound) this.sound.unload();
      var sound = new Howl({
        src: entry.audioFile,
        sprite: {
          "phrase": [entry.start, entry.dur]
        }
      });
      sound.once('load', function(){
        sound.play("phrase");
      });
      this.sound = sound;

    } else if (this.sound && this.sound.state()==="loaded") {
      this.sound.play("phrase");
    }
    this.soundIndex = entry.index;
  };

  AppQueryPhrases.prototype.query = function(){

  };

  AppQueryPhrases.prototype.render = function(){

  };

  return AppQueryPhrases;

})();

$(function() {
  var app = new AppQueryPhrases({});
});
