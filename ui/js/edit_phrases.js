'use strict';

var AppEditPhrases = (function() {

  function AppEditPhrases(config) {
    var defaults = {
      dataFile: "/data/output/birds_audio_phrase_stats_query.csv",
      audioDir: "/audio/downloads/birds/",
      audioExt: ".mp3",
      savedFile: "/data/usergen/saved_birds.json",
      saveFile: "/data/usergen/edited_birds.json",
      saveUrl: "/save"
    };
    this.opt = _.extend({}, defaults, config);
    this.init();
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

  function parseNumber(str){
    var isNum = /^[\d\.]+$/.test(str);
    if (isNum && str.indexOf(".") >= 0) return parseFloat(str);
    else if (isNum) return parseInt(str);
    else return str;
  }

  function pxToPercent($el) {
    var parentW = $el.parent().width();
    var x = $el.position().left / parentW;
    var w = $el.width() / parentW;
    $el.css({
      left: (x * 100) + '%',
      width: (w * 100) + '%'
    });
    return {
      x: x,
      w: w
    }
  }

  AppEditPhrases.prototype.init = function(){
    this.$el = $("#app");
    this.$wrapper = $("#spectrogram-wrapper");
    this.$spectrogram = $("#spectrogram");
    this.$select = $("#select-audio");
    this.$phrases = $("#phrases");

    this.data = [];
    this.savedData = [];
    this.editedData = {};
    this.saveDataQueue = [];

    var _this = this;
    var dataPromise = loadCsvData(this.opt.dataFile);
    var savedDataPromise = loadJsonData(this.opt.savedFile);
    var editedDataPromise = loadJsonData(this.opt.saveFile);

    $.when.apply($, [dataPromise, savedDataPromise, editedDataPromise]).then(function(data, savedData, editedData){
      _this.data = _this.parseData(data);
      _this.savedData = savedData;
      _this.editedData = editedData.length ? editedData : {};
      _this.onReady();
      _this.loadListeners();
    });
  };

  AppEditPhrases.prototype.loadListeners = function(){
    var _this = this;

    this.$select.on("change", function(e){ _this.onSelect(); });

    $(window).on("resize", function(e){ _this.onResize(); })
  };

  AppEditPhrases.prototype.loadUi = function(){
    var $select = this.$select;

    _.each(this.savedData, function(d, i){
      $select.append($('<option value="'+i+'">'+d+'</option>'))
    });
  };

  AppEditPhrases.prototype.onReady = function(){
    this.loadUi();
    this.onResize();
    this.onSelect();
  };

  AppEditPhrases.prototype.onResize = function(){
    var w = this.$wrapper.width();
    var h = this.$wrapper.height();
    this.$spectrogram.width(w);
    this.$spectrogram.height(h);
  };

  AppEditPhrases.prototype.onSelect = function(){
    var _this = this;
    var parent = this.savedData[parseInt(this.$select.val())];
    var filename = this.opt.audioDir + parent + this.opt.audioExt;
    var phrases = _.where(this.data, {parent: parent});
    var sprites = _.object(_.map(phrases, function(p, i){ return [""+i, [p.start, p.dur]]; }))

    var sound = this.sound;
    if (sound) sound.unload();
    var sound = new Howl({
      src: filename,
      sprite: sprites,
      onload: function(){
        _this.renderAudio(this);
        _this.renderPhrases(this, phrases);
      }
    });
  };

  AppEditPhrases.prototype.parseData = function(data){
    var audioDir = this.opt.audioDir;
    var audioExt = this.opt.audioExt;
    return _.map(data, function(entry, i){
      entry.audioFile = audioDir + entry.parent + audioExt;
      entry.index = i;
      return entry;
    });
  };

  AppEditPhrases.prototype.renderAudio = function(sound) {

  };

  AppEditPhrases.prototype.renderPhrases = function(sound, phrases) {
    var _this = this;
    var dur = sound.duration() * 1000;
    var $phrases = this.$phrases;

    $phrases.empty();
    var $container = $('<div></div>');
    _.each(phrases, function(p){
      var $phrase = $('<div class="phrase"></div>');
      var w = p.dur / dur * 100;
      var x = p.start / dur * 100;
      $phrase.css({
        width: w + "%",
        left: x + "%"
      });
      $container.append($phrase);
    });
    $phrases.append($container);
    $('.phrase').draggable({
      axis: "x",
      containment: "parent",
      stop: function(e, ui) {
        var dim = pxToPercent($(this));
      }
    }).resizable({
      containment: "parent",
      handles: "e, w",
      resize: function(e, ui) {
        $(this).css('height', '100%');
      },
      stop: function(e, ui) {
        var dim = pxToPercent($(this));
      }
    });
  };

  AppEditPhrases.prototype.saveData = function(){
    var filename = this.opt.saveFile;
    var data = this.editedData.slice(0);

    this.saveDataQueue.push({
      filename: filename,
      data: data
    });

    this.saveQueue();
  };

  AppEditPhrases.prototype.saveQueue = function(){
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

  return AppEditPhrases;

})();

$(function() {
  var app = new AppEditPhrases({});
});
