'use strict';

var APPTsne = (function() {

  function APPTsne(config) {
    var defaults = {
      dataFile: "/data/output/birds_audio_tsne.csv",
      imageFile: "/data/output/birds_audio_tsne.png",
      audioDir: "/audio/downloads/",
      audioExt: ".mp3",
      saveUrl: "/save",
      resultLimit: 100,
      radius: 4
    };
    this.opt = _.extend({}, defaults, config);
    this.init();
  }

  APPTsne.prototype.init = function(){
    this.$el = $("#app");
    this.$tsne = $("#tsne");
    this.data = [];

    var _this = this;
    var dataPromise = UTIL.loadCsvData(this.opt.dataFile);

    this.player = new Player();

    $.when.apply($, [dataPromise]).then(function(data){
      _this.data = _this.parseData(data);
      _this.onReady();
    });
  };

  APPTsne.prototype.loadListeners = function(){
    var _this = this;
    var shifted = false;

    $(document).on('keyup keydown', function(e){
      shifted = e.shiftKey}
    );

    $(window).on("resize", function(e){
      _this.onResize();
    })

    this.$tsne.on("click", function(e){
      _this.onTsneClick(e.pageX, e.pageY, shifted);
    });
  };

  APPTsne.prototype.loadUi = function(){
    var _this = this;
    var $tsne = this.$tsne;
    var $image = $('<img src="'+this.opt.imageFile+'" alt="TSNE image" />');

    $tsne.append($image);
    panzoom($tsne[0]);

    $image .one("load", function() {
      _this.onResize();
    }).each(function() {
      if(this.complete) $(this).load();
    });
  };

  APPTsne.prototype.onReady = function(){
    this.loadUi();

    this.loadListeners();
  };

  APPTsne.prototype.onResize = function(){
    this.tsneOffset = this.$tsne.offset();
    var $image = this.$tsne.find("img").first();
    this.tsneWidth = $image.width();
    this.tsneHeight = $image.height();
    this.tsneDotWidth = this.opt.radius * 2.0 / this.tsneWidth;
    this.tsneDotHeight = this.opt.radius * 2.0 / this.tsneHeight;
  };

  APPTsne.prototype.onTsneClick = function(x, y, playFull){
    var offset = this.$tsne.offset();
    var rw = this.tsneDotWidth;
    var rh = this.tsneDotHeight;
    var rx = (x - offset.left) / this.tsneWidth - rw;
    var ry = (y - offset.top) / this.tsneHeight - rh;
    var rx1 = rx + rw;
    var ry1 = ry + rh;

    // console.log(rx, ry, rx1, ry1);

    var matches = _.filter(this.data, function(d){
      return d.x >= rx && d.x <= rx1 && d.y >= ry && d.y <= ry1;
    });

    // if found multiple, sort by distance from click
    if (matches.length > 1) {
      console.log("Found multiple");
      matches = _.sortBy(matches, function(d){
        return UTIL.distance(rx + rw/2, ry + rh/2, d.x, d.y);
      });
    }

    if (matches.length > 0) {
      var entry = matches[0];
      console.log("Found ", entry);
      this.player.play(entry, playFull);

    } else {
      console.log("Nothing found.");
    }
  };

  APPTsne.prototype.parseData = function(data){
    var audioDir = this.opt.audioDir;
    var audioExt = this.opt.audioExt;
    return _.map(data, function(entry, i){
      var group = (entry.group && entry.group.length) ? entry.group + "/" : "";
      entry.audioFile = audioDir + group + entry.parent + audioExt;
      entry.keywords = entry.parent.toLowerCase();
      entry.index = i;
      return entry;
    });
  };

  return APPTsne;

})();

$(function() {
  var app = new APPTsne({});
});
