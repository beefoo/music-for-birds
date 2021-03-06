'use strict';

var AppEditPhrases = (function() {

  function AppEditPhrases(config) {
    var defaults = {
      dataFile: "/data/output/birds_audio_phrase_stats_query.csv",
      audioDir: "/audio/downloads/birds/",
      audioExt: ".mp3",
      imageDir: "/data/output/images/",
      imageExt: ".png",
      savedFile: "/data/usergen/saved_birds.json",
      saveFile: "/data/usergen/edited_birds.json",
      saveUrl: "/save",
      zoomStep: 10,
      zoomRange: [100, 500]
    };
    this.opt = _.extend({}, defaults, config);
    this.init();
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
    this.$editor = $("#editor");
    this.$wrapper = $("#spectrogram-wrapper");
    this.$spectrogram = $("#spectrogram");
    this.$select = $("#select-audio");
    this.$phrases = $("#phrases");

    this.data = [];
    this.savedData = [];
    this.editedData = {};
    this.saveDataQueue = [];
    this.zoom = 100;

    var _this = this;
    var dataPromise = UTIL.loadCsvData(this.opt.dataFile);
    var savedDataPromise = UTIL.loadJsonData(this.opt.savedFile);
    var editedDataPromise = UTIL.loadJsonData(this.opt.saveFile);

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

    $(window).on("resize", function(e){ _this.onResize(); });

    this.$wrapper.on('mousewheel', function(e) {
      _this.onZoom(e.deltaY, e.pageX);
    });

    $(document).on("keypress", function(e){
      var key = String.fromCharCode(e.which);
      switch(key) {
        case " ":
          _this.playCurrent();
          break;
      }
    })

    this.$phrases.on("mousedown", ".phrase", function(e){
      _this.onSelectPhrase($(this));
    });
  };

  AppEditPhrases.prototype.loadSound = function(filename, phrases, callback){
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

  AppEditPhrases.prototype.loadUi = function(){
    var $select = this.$select;

    _.each(this.savedData, function(d, i){
      $select.append($('<option value="'+i+'">'+d+'</option>'))
    });
  };

  AppEditPhrases.prototype.onEditPhrase = function(){
    var containerW = this.$phrases.width();
    var audioDuration = this.currentAudioDuration;
    var phrases = $(".phrase").map(function(){
      var $el = $(this);
      var start =  parseInt($el.position().left / containerW * audioDuration);
      var dur = parseInt($el.width() / containerW * audioDuration);
      return {
        "start": start,
        "dur": dur
      };
    }).get();

    this.loadSound(this.currentFilename, phrases);
  };

  AppEditPhrases.prototype.onReady = function(){
    this.loadUi();
    this.onResize();
    this.onSelect();
  };

  AppEditPhrases.prototype.onResize = function(){
    this.elOffset = this.$el.offset();
    this.elWidth = this.$el.width();
  };

  AppEditPhrases.prototype.onSelect = function(){
    var _this = this;
    var index = parseInt(this.$select.val())
    var parent = this.savedData[index];
    var filename = this.opt.audioDir + parent + this.opt.audioExt;
    var phrases = _.where(this.data, {parent: parent});
    this.renderSpectrogram(this.opt.imageDir + parent + this.opt.imageExt);

    this.loadSound(filename, phrases, function(audio){
      _this.currentAudioDuration = audio.duration() * 1000;
      _this.renderPhrases(audio, phrases);
    });

    this.currentPhraseIndex = false;
    this.currentPhraseEl = false;
    this.currentIndex = index;
    this.currentPhrases = phrases;
    this.currentFilename = filename;
  };

  AppEditPhrases.prototype.onSelectPhrase = function($phrase){
    $(".phrase").removeClass("selected");
    $phrase.addClass("selected");
    this.currentPhraseIndex = parseInt($phrase.attr("data-index"));
    this.currentPhraseEl = $phrase.find(".progress").first();
    this.currentPhrase = this.currentPhrases[this.currentPhraseIndex];
  };

  AppEditPhrases.prototype.onZoom = function(delta, mouseX){
    var zoomStep = this.opt.zoomStep;
    var zoomRange = this.opt.zoomRange;

    var zoom = this.zoom + delta * zoomStep;
    if (zoom < zoomRange[0]) zoom = zoomRange[0];
    else if (zoom > zoomRange[1]) zoom = zoomRange[1];

    var $wrapper = this.$wrapper;
    var wrapperOffset = $wrapper.offset();
    var wrapperWidth = $wrapper.width();

    var appX = this.elOffset.left;
    var appWidth = this.elWidth;
    var wrapperX = wrapperOffset.left;
    var anchorPos = (mouseX - wrapperX + appX) / wrapperWidth;
    var anchorX = mouseX + appX;
    var newWidth = appWidth * (zoom/100.0);
    var scrollLeft = (anchorPos * newWidth - anchorX);

    if (scrollLeft < 0) scrollLeft = 0;
    if (scrollLeft > newWidth-appWidth) scrollLeft = newWidth-appWidth;

    this.$wrapper.css("width", zoom + "%");
    this.$editor.scrollLeft(scrollLeft);

    this.zoom = zoom;
  };

  AppEditPhrases.prototype.parseData = function(data){
    var audioDir = this.opt.audioDir;
    var audioExt = this.opt.audioExt;
    var imageDir = this.opt.imageDir;
    var imageExt = this.opt.imageExt;
    return _.map(data, function(entry, i){
      entry.audioFile = audioDir + entry.parent + audioExt;
      entry.imageFile = imageDir + entry.parent + imageExt;
      entry.index = i;
      return entry;
    });
  };

  AppEditPhrases.prototype.playCurrent = function(){
    var _this = this;
    var index = this.currentPhraseIndex;
    var sound = this.sound;

    if (index !== false && sound) {
      this.progressing = true;
      sound.play(""+index);
      setTimeout(function(){ _this.renderProgress(); }, 10);
    }
  }

  AppEditPhrases.prototype.renderPhrases = function(sound, phrases) {
    var _this = this;
    var dur = sound.duration() * 1000;
    var $phrases = this.$phrases;

    $phrases.empty();
    var $container = $('<div></div>');
    _.each(phrases, function(p, i){
      var $phrase = $('<div class="phrase" data-index="'+i+'"><div class="progress"></div></div>');
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
      start: function(e, ui) {
        _this.onSelectPhrase($(this));
      },
      stop: function(e, ui) {
        var dim = pxToPercent($(this));
        _this.onEditPhrase();
      }
    }).resizable({
      containment: "parent",
      handles: "e, w",
      start: function(e, ui) {
        _this.onSelectPhrase($(this));
      },
      resize: function(e, ui) {
        $(this).css('height', '100%');
      },
      stop: function(e, ui) {
        var dim = pxToPercent($(this));
        _this.onEditPhrase();
      }
    });
  };

  AppEditPhrases.prototype.renderProgress = function(){
    if (!this.progressing || !this.currentPhraseEl || !this.sound || this.currentPhraseIndex===false) return false;

    var current = this.currentPhrase;
    var _this = this;
    var pos = this.sound.seek();
    var progress = UTIL.norm(pos*1000, current.start, current.start+current.dur);
    this.currentPhraseEl.css("left", (progress*100)+"%")

    requestAnimationFrame(function(){ _this.renderProgress(); });
  }

  AppEditPhrases.prototype.renderSpectrogram = function(filename) {
    var $spectrogram = this.$spectrogram;
    $spectrogram.empty();
    $spectrogram.append($('<image src="'+filename+'" />'))
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
