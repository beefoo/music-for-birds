'use strict';

var AppBrowsePhrases = (function() {

  function AppBrowsePhrases(config) {
    var defaults = {
      dataFile: "/data/output/birds_audio_phrases.csv",
      imgFile: "/data/output/birds_audio_phrases.png",
      audioDir: "/audio/downloads/birds/",
      audioExt: ".mp3"
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

  AppBrowsePhrases.prototype.init = function(){
    this.$el = $("#app");

    var _this = this;
    var dataPromise = this.loadData(this.opt.dataFile);
    var imagePromise = this.loadImage(this.opt.imgFile);

    $.when.apply($, [dataPromise, imagePromise]).then(function(){
      _this.onReady();
      _this.onResize();
      _this.loadListeners();
    });
  };

  AppBrowsePhrases.prototype.loadData = function(csvFilename){
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

  AppBrowsePhrases.prototype.loadImage = function(filename){
    var deferred = $.Deferred();
    var _this = this;
    var $image = $('<img src="'+filename+'" alt="Visualization of bird call phrases" />');
    var $wrapper = $('<div class="image-wrapper"></div>');

    $image.on("load", function(){
      var width = $(this).width();
      var height = $(this).height();
      $wrapper.css("width", width + "px");
      _this.imageWidth = width;
      _this.imageHeight = height;
      deferred.resolve();
    });

    $wrapper.append($image);

    var $helper = $('<div class="image-helper"><div class="image-label"></div></div>');
    $wrapper.append($helper);
    this.$el.append($wrapper);

    this.$imageWrapper = $wrapper;
    this.$imageHelper = $helper;
    this.$imageLabel = $helper.find(".image-label");

    return deferred.promise();
  };

  AppBrowsePhrases.prototype.loadListeners = function(){
    var _this = this;
    var listening = false;

    this.$imageWrapper.on("mouseover", function(e){ listening = true; });
    this.$imageWrapper.on("mouseout", function(e){ listening = false; });
    this.$imageWrapper.on("click", function(e){ _this.onPhraseSelect(); });

    $(document).on("mousemove", function(e){
      if (listening) _this.onImageOver(e.pageX, e.pageY);
    });

    $(window).on("resize", function(e){ _this.onResize(); })
  };

  AppBrowsePhrases.prototype.onImageOver = function(wx, wy){
    var y = wy - this.imageOffset.top;
    var index = parseInt(y / this.rowHeight);
    this.currentPhrase = this.data[index];

    this.$imageHelper.css('top', (index*this.rowHeight)+"px");
    this.$imageLabel.text(this.data[index].parent);
  };

  AppBrowsePhrases.prototype.onPhraseSelect = function(){
    if (!this.currentPhrase) return false;
    var phrase = this.currentPhrase;

    this.play(phrase);
  };

  AppBrowsePhrases.prototype.onReady = function(){
    this.rowHeight = 1.0 * this.imageHeight / this.rowCount;
    this.$imageHelper.height(this.rowHeight);
  };

  AppBrowsePhrases.prototype.onResize = function(){
    this.imageOffset = this.$imageWrapper.offset();
  };

  AppBrowsePhrases.prototype.parseData = function(data){
    var audioDir = this.opt.audioDir;
    var audioExt = this.opt.audioExt;
    return _.map(data, function(entry, i){
      if (!entry.phrase) return entry;
      var phrase = entry.phrase.split(",");
      var keys = ["start", "dur", "power", "hz", "note", "octave"];
      entry.phrase = _.map(phrase, function(note){
        var values = _.map(note.split(":"), function(v){ return parseNumber(v); });
        return _.object(keys, values);
      });
      entry.audioFile = audioDir + entry.parent + audioExt;
      entry.index = i;
      return entry;
    });
  };

  AppBrowsePhrases.prototype.play = function(entry){
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

  return AppBrowsePhrases;

})();

$(function() {
  var app = new AppBrowsePhrases({});
});
