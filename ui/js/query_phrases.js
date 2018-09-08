'use strict';

var AppQueryPhrases = (function() {

  function AppQueryPhrases(config) {
    var defaults = {
      dataFile: "/data/output/birds_audio_phrase_stats_query.csv",
      audioDir: "/audio/downloads/birds/",
      audioExt: ".mp3",
      saveDir: "/data/usergen/",
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
    this.$resultCount = $("#result-count");
    this.$results = $("#results");

    var _this = this;
    var dataPromise = this.loadData(this.opt.dataFile);
    this.ranges = {};

    $.when.apply($, [dataPromise]).then(function(){
      _this.onReady();
      _this.loadListeners();
    });
  };

  AppQueryPhrases.prototype.getSelectValues = function(){
    this.sortBy = $('input[name="select-sort"]:checked').val();
    this.sortDirection = parseInt($('input[name="select-direction"]:checked').val());
    this.notes = $('input[name="select-notes"]:checked').map(function(){
      return $(this).val();
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
    var shifted = false;

    $(document).on('keyup keydown', function(e){
      shifted = e.shiftKey}
    );

    $('input[type="checkbox"], input[type="radio"]').on("change", function(e){
      _this.query();
    });

    this.$results.on("click", ".play-button", function(e){
      var entry = _this.data[parseInt($(this).attr("data-index"))];
      _this.play(entry, shifted);
    });
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

  AppQueryPhrases.prototype.play = function(entry, playFull){
    var spriteKey = playFull ? "full" : "phrase";
    if (entry.index !== this.soundIndex) {
      if (this.sound) this.sound.unload();
      var sound = new Howl({
        src: entry.audioFile,
        sprite: {
          "phrase": [entry.start, entry.dur],
          "full": [0, 60000]
        }
      });
      sound.once('load', function(){
        sound.play(spriteKey);
      });
      this.sound = sound;

    } else if (this.sound && this.sound.state()==="loaded") {
      this.sound.play(spriteKey);
    }
    this.soundIndex = entry.index;
  };

  AppQueryPhrases.prototype.query = function(){
    this.getSelectValues();

    var sortBy = this.sortBy;
    var sortDirection = this.sortDirection;
    var notes = this.notes;
    var ranges = this.ranges;
    // console.log(sortBy, sortDirection, notes.length, ranges);

    var results = _.filter(this.data, function(d){
      var valid = true;
      if (notes.length) {
        valid = _.every(notes, function(note){
          return d.notes.includes(note);
        });
      }
      if (valid) {
        valid = _.every(ranges, function(values, key){
          return d[key] >= values[0] && d[key] <= values[1];
        });
      }
      return valid;
    });

    results = _.sortBy(results, function(d){
      return sortDirection * d[sortBy];
    });

    this.render(results);
  };

  AppQueryPhrases.prototype.render = function(results){
    this.$resultCount.text(results.length);

    var resultLimit = this.opt.resultLimit;
    if (results.length > resultLimit) {
      results = results.slice(0, resultLimit);
    }

    var htmlString = "";

    // parent,start,dur,count,hzMean,durMean,powMean,hzStd,beatStd,notes
    _.each(results, function(r, i){
      var row = '<tr>';
        row += '<td>'+(i+1)+'.</td>';
        row += '<td>'+r.parent+'</td>';
        row += '<td>'+r.dur+'</td>';
        row += '<td>'+r.count+'</td>';
        row += '<td>'+r.hzMean+'</td>';
        row += '<td>'+r.durMean+'</td>';
        row += '<td>'+r.powMean+'</td>';
        row += '<td>'+r.hzStd+'</td>';
        row += '<td>'+r.beatStd+'</td>';
        row += '<td><button class="play-button" data-index="'+r.index+'">play</button></td>';
        row += '<td><button class="save-button" data-index="'+r.index+'">save</button></td>';
      row += '</tr>';
      htmlString += row;
    });

    this.$results.html(htmlString);
  };

  return AppQueryPhrases;

})();

$(function() {
  var app = new AppQueryPhrases({});
});
