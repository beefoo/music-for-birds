'use strict';

var AppQueryPhrases = (function() {

  function AppQueryPhrases(config) {
    var defaults = {
      dataFile: "/data/output/birds_audio_phrase_stats_query.csv",
      audioDir: "/audio/downloads/birds/",
      audioExt: ".mp3",
      saveFile: "/data/usergen/saved_birds.json",
      saveUrl: "/save",
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

    this.data = [];
    this.savedData = [];
    this.saveDataQueue = [];

    var _this = this;
    var dataPromise = this.loadData(this.opt.dataFile);
    var savedDataPromise = this.loadSavedData(this.opt.saveFile);
    this.ranges = {};

    $.when.apply($, [dataPromise, savedDataPromise]).then(function(){
      _this.onReady();
      _this.loadListeners();
    });
  };

  AppQueryPhrases.prototype.getSelectValues = function(){
    this.sortBy = $('input[name="select-sort"]:checked').val();
    this.sortDirection = parseInt($('input[name="select-direction"]:checked').val());
    this.filterSaved = $('input[name="select-saved"]:checked').val();
    this.keyword = $('#input-keyword').val().toLowerCase();
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

    $('input[type="checkbox"], input[type="radio"], #input-keyword').on("change", function(e){
      _this.query();
    });

    this.$results.on("click", ".play-button", function(e){
      var entry = _this.data[parseInt($(this).attr("data-index"))];
      _this.play(entry, shifted);
    });

    this.$results.on("click", ".save-button", function(e){
      var $el = $(this);
      var entry = _this.data[parseInt($el.attr("data-index"))];
      _this.save($el, entry);
    });
  };

  AppQueryPhrases.prototype.loadSavedData = function(jsonFilename){
    var _this = this;
    var deferred = $.Deferred();

    $.getJSON(jsonFilename, function(data) {
      _this.savedData = data;
      console.log("Found "+data.length+" saved entries");
      deferred.resolve();

    }).fail(function() {
      _this.savedData = [];
      console.log("No saved data found");
      deferred.resolve();
    });

    return deferred.promise();
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
    var savedData = this.savedData;
    _.each(this.data, function(entry, i){
      entry.saved = (savedData.indexOf(entry.parent) >= 0);
    })
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
      entry.keywords = entry.parent.toLowerCase();
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
    // update ui
    $('.play-button[data-parent="'+entry.parent+'"]').addClass('played');
  };

  AppQueryPhrases.prototype.query = function(){
    this.getSelectValues();

    var sortBy = this.sortBy;
    var sortDirection = this.sortDirection;
    var filterSaved = this.filterSaved;
    var notes = this.notes;
    var ranges = this.ranges;
    var keyword = this.keyword;
    // console.log(sortBy, sortDirection, notes.length, ranges);

    var results = _.filter(this.data, function(d){
      var valid = true;
      if (notes.length) {
        valid = _.find(notes, function(note){
          return d.notes.includes(note);
        });
        valid = valid ? true : false;
      }
      if (valid && filterSaved !== "all") {
        valid = (d.saved && filterSaved==="saved" || !d.saved && filterSaved==="unsaved");
      }
      if (valid && keyword.length) {
        valid = d.keywords.indexOf(keyword) >= 0;
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
        row += '<td><button class="play-button" data-index="'+r.index+'" data-parent="'+r.parent+'">play</button></td>';
        var text = "save";
        var className = "";
        if (r.saved) {
          text = "saved";
          className = " saved";
        }
        row += '<td><button class="save-button'+className+'" data-index="'+r.index+'" data-parent="'+r.parent+'">'+text+'</button></td>';
      row += '</tr>';
      htmlString += row;
    });

    this.$results.html(htmlString);
  };

  AppQueryPhrases.prototype.save = function($el, entry){
    var parent = entry.parent;
    var index = this.savedData.indexOf(parent);
    var wasSaved = (index >= 0);
    var $buttons = $('.save-button[data-parent="'+parent+'"]');
    var entries = _.filter(this.data, function(d){ return d.parent===parent; })

    if (wasSaved) {
      this.savedData.splice(index, 1);
      $buttons.text('save').removeClass('saved');
      _.each(entries, function(entry, i){ entry.saved = false; });
    } else {
      this.savedData.push(entry.parent);
      $buttons.text('saved').addClass('saved');
      _.each(entries, function(entry, i){ entry.saved = true; });
    }

    this.saveData();
  };

  AppQueryPhrases.prototype.saveData = function(){
    var filename = this.opt.saveFile;
    var data = this.savedData.slice(0);

    this.saveDataQueue.push({
      filename: filename,
      data: data
    });

    this.saveQueue();
  };

  AppQueryPhrases.prototype.saveQueue = function(){
    if (this.isSaving || !this.saveDataQueue.length) return false;
    var _this = this;

    this.isSaving = true;
    var nextData = this.saveDataQueue.shift();
    var url = this.opt.saveUrl;

    $.ajax({
      type: 'POST',
      url: url,
      data: JSON.stringify(nextData),
      contentType: 'application/json',
      complete: function(jqXHR, textStatus){
        _this.isSaving = false;
        _this.saveQueue();
      },
      success: function(d){ console.log(d.data.length+' entries saved'); },
      error: function(){ console.log('Error with saving data'); }
    });
  };

  return AppQueryPhrases;

})();

$(function() {
  var app = new AppQueryPhrases({});
});
