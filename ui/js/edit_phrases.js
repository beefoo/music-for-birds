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

// var AudioContext = window.AudioContext || window.webkitAudioContext || window.mozAudioContext;
// context = new AudioContext();
//
// var animationID;
//
// var audio = new Audio();
// audio.src = 'song-thrush-rspb.mp3';
// audio.controls = true;
// audio.onpause = function(){
//   window.cancelAnimationFrame(animationID);
// }
//
// var fileInput = $("#audio-file");
// fileInput.on("change", function(e) {
//
//   audio.pause();
//   window.cancelAnimationFrame(animationID);
//
//   //see http://lostechies.com/derickbailey/2013/09/23/getting-audio-file-information-with-htmls-file-api-and-audio-element/
//   var file = e.currentTarget.files[0];
//   var objectUrl = URL.createObjectURL(file);
//
//
//   // var reader = new FileReader();
//   // reader.onload = function(ev) {
//     audio.src = objectUrl;
//
//   // }
//   // console.log(reader);
//   // reader.readAsDataURL(file);
//
// })
//
// audio.onplay = function(){
//   demo.render();
// }
// // audio.autoplay = true;
// document.body.appendChild(audio);
//
// // (function(){
//
// 	var demo = new Demo({
// 		ui: {
//       logScale:{
//         title: "Logarithmic Frequency Scale?",
//         value: false
//       },
//       soundSamples:{
//         title: "Sound Sample",
//         value: "song-thrush-rspb",
//         values: [
//           ["Bird Song (Song Thrush)", "song-thrush-rspb"],
//           ["Orca (Killer whale)","transient-orca"],
//           ["Police Siren","police-siren"],
//           ["Modem (Dial up)","modem"],
//           ["Violin","violin"],
//           ["Whistling","whistle"],
//           ["Sad Trombone","sad-trombone"]
//           //["Erskine Butterfield", "erskine-butterfield"]
//         ] //the first value in each pair is the label, the second is the value
//       }
// 		},
//
// 		canvas: document.getElementById("canvas"),
//     canvasLog: document.getElementById("canvas-log"),
// 		labels: document.getElementById("labels"),
//
// 		controls: true,
// 		// Log mode.
// 		log: false,
// 		// Show axis labels, and how many ticks.
// 		showLabels: true,
// 		ticks: 5,
// 		speed: 3,
// 		// FFT bin size,
// 		fftsize: 2048,
// 		oscillator: false,
// 		color: true,
//
// 		init: function(){
//       $("#demo").append($("#canvas"));
//       $("#demo").append($("#canvas-log"));
//       $("#demo").append($("#labels"));
// 			this.attachedCallback();
// 			this.onStream();
//       $("#ui-container").append($(".audio-file-wrapper"));
//       $("#ui-container").append($("audio"));
//     window.cancelAnimationFrame(animationID);
//     $("#demo").height(Math.round($("#demo").width()*0.67));
//
// 		},
//
// 		update: function(e){
//
//       if (e == "logScale"){
//         if (this.ui.logScale.value === false){
//           this.log = false;
//         } else {
//           this.log = true;
//         }
//         // this.ctx.fillRect(0,0,this.width, this.height, this.speed, this.speed);
//         this.logChanged();
//       }
//
//       if (e == "soundSamples"){
//         audio.pause();
//         window.cancelAnimationFrame(animationID);
//         this.ctx.fillRect(0,0,this.width, this.height);
//         audio.src = '/demos/spectrum-analyzer/' + this.ui.soundSamples.value + ".mp3";
//       }
// 		},
//
//
//
//
// // Assumes context is an AudioContext defined outside of this class.
//
//
//   attachedCallback: function() {
//     this.tempCanvas = document.createElement('canvas'),
//     // Get input from the microphone.
//     // if (navigator.mozGetUserMedia) {
//     //   navigator.mozGetUserMedia({audio: true},
//     //                             this.onStream.bind(this),
//     //                             this.onStreamError.bind(this));
//     // } else if (navigator.webkitGetUserMedia) {
//     //   navigator.webkitGetUserMedia({audio: true},
//     //                             this.onStream.bind(this),
//     //                             this.onStreamError.bind(this));
//     // }
//     // this.onStream();
//     this.ctx = this.canvas.getContext('2d');
//   },
//
//   render: function() {
//     //console.log('Render');
//     this.width = window.innerWidth;
//     this.width = $("#demo").width();
//     this.height = window.innerHeight;
//     this.height = Math.round(this.width*0.67);
//
//
//     var didResize = false;
//     // Ensure dimensions are accurate.
//     if (this.canvas.width != this.width) {
//       this.canvas.width = this.width;
//       this.labels.width = this.width;
//       didResize = true;
//     }
//     if (this.canvas.height != this.height) {
//       this.canvas.height = this.height;
//       this.labels.height = this.height;
//       didResize = true;
//     }
//
//     //this.renderTimeDomain();
//     this.renderFreqDomain();
//
//     if (this.showLabels && didResize) {
//       this.renderAxesLabels();
//     }
//
//     animationID = requestAnimationFrame(this.render.bind(this));
//
//     var now = new Date();
//     if (this.lastRenderTime_) {
//       this.instantaneousFPS = now - this.lastRenderTime_;
//     }
//     this.lastRenderTime_ = now;
//   },
//
//   renderTimeDomain: function() {
//     var times = new Uint8Array(this.analyser.frequencyBinCount);
//     this.analyser.getByteTimeDomainData(times);
//
//     for (var i = 0; i < times.length; i++) {
//       var value = times[i];
//       var percent = value / 256;
//       var barHeight = this.height * percent;
//       var offset = this.height - barHeight - 1;
//       var barWidth = this.width/times.length;
//       this.ctx.fillStyle = 'black';
//       this.ctx.fillRect(i * barWidth, offset, 1, 1);
//     }
//   },
//
//   renderFreqDomain: function() {
//     var freq = new Uint8Array(this.analyser.frequencyBinCount);
//     this.analyser.getByteFrequencyData(freq);
//
//     var ctx = this.ctx;
//     // Copy the current canvas onto the temp canvas.
//     this.tempCanvas.width = this.width;
//     this.tempCanvas.height = this.height;
//     //console.log(this.canvas.height, this.tempCanvas.height);
//     var tempCtx = this.tempCanvas.getContext('2d');
//     tempCtx.drawImage(this.canvas, 0, 0, this.width, this.height);
//
//     // Iterate over the frequencies.
//     for (var i = 0; i < freq.length; i++) {
//       var value;
//       // Draw each pixel with the specific color.
//       if (this.log) {
//         logIndex = this.logScale(i, freq.length);
//         value = freq[logIndex];
//       } else {
//         value = freq[i];
//       }
//
//       ctx.fillStyle = (this.color ? this.getFullColor(value) : this.getGrayColor(value));
//
//       var percent = i / freq.length;
//       var y = Math.round(percent * this.height);
//
//       // draw the line at the right side of the canvas
//       ctx.fillRect(this.width - this.speed, this.height - y,
//                    this.speed, this.speed);
//     }
//
//     // Translate the canvas.
//     ctx.translate(-this.speed, 0);
//     // Draw the copied image.
//     // console.log(this.width, this.height);
//     ctx.drawImage(this.tempCanvas, 0, 0, this.width, this.height,
//                   0, 0, this.width, this.height);
//
//     // Reset the transformation matrix.
//     ctx.setTransform(1, 0, 0, 1, 0, 0);
//   },
//
//   /**
//    * Given an index and the total number of entries, return the
//    * log-scaled value.
//    */
//   logScale: function(index, total, opt_base) {
//     var base = opt_base || 2;
//     var logmax = this.logBase(total + 1, base);
//     var exp = logmax * index / total;
//     return Math.round(Math.pow(base, exp) - 1);
//   },
//
//   logBase: function(val, base) {
//     return Math.log(val) / Math.log(base);
//   },
//
//   renderAxesLabels: function() {
//     var canvas = this.labels;
//     canvas.width = this.width;
//     canvas.height = this.height;
//     var ctx = canvas.getContext('2d');
//     var startFreq = 440;
//     var nyquist = context.sampleRate/2;
//     var endFreq = nyquist - startFreq;
//     var step = (endFreq - startFreq) / this.ticks;
//     var yLabelOffset = 5;
//     // Render the vertical frequency axis.
//     for (var i = 0; i <= this.ticks; i++) {
//       var freq = startFreq + (step * i);
//       // Get the y coordinate from the current label.
//       var index = this.freqToIndex(freq);
//       var percent = index / this.getFFTBinCount();
//       var y = (1-percent) * this.height;
//       var x = this.width - 60;
//       // Get the value for the current y coordinate.
//       var label;
//       if (this.log) {
//         // Handle a logarithmic scale.
//         var logIndex = this.logScale(index, this.getFFTBinCount());
//         // Never show 0 Hz.
//         freq = Math.max(1, this.indexToFreq(logIndex));
//       }
//       var label = this.formatFreq(freq);
//       var units = this.formatUnits(freq);
//       ctx.font = '16px "Open Sans"';
//       ctx.fillStyle = 'white';
//       // Draw the value.
//       ctx.textAlign = 'right';
//       ctx.fillText(label, x, y + yLabelOffset);
//       // Draw the units.
//       ctx.textAlign = 'left';
//       ctx.fillText(units, x + 10, y + yLabelOffset);
//       // Draw a tick mark.
//       ctx.fillRect(x + 40, y, 30, 2);
//     }
//   },
//
//   clearAxesLabels: function() {
//     var canvas = this.labels;
//     var ctx = canvas.getContext('2d');
//     ctx.clearRect(0, 0, this.width, this.height);
//   },
//
//   formatFreq: function(freq) {
//     return (freq >= 1000 ? (freq/1000).toFixed(1) : Math.round(freq));
//   },
//
//   formatUnits: function(freq) {
//     return (freq >= 1000 ? 'KHz' : 'Hz');
//   },
//
//   indexToFreq: function(index) {
//     var nyquist = context.sampleRate/2;
//     return nyquist/this.getFFTBinCount() * index;
//   },
//
//   freqToIndex: function(frequency) {
//     var nyquist = context.sampleRate/2;
//     return Math.round(frequency/nyquist * this.getFFTBinCount());
//   },
//
//   getFFTBinCount: function() {
//     return this.fftsize / 2;
//   },
//
//   onStream: function(stream) {
//     // var input = context.createMediaStreamSource(stream);
//     var input = context.createMediaElementSource(audio);
//     var analyser = context.createAnalyser();
//     analyser.smoothingTimeConstant = 0;
//     analyser.fftSize = this.fftsize;
//
//     // Connect graph.
//     input.connect(analyser);
//     input.connect(context.destination);
//
//     this.analyser = analyser;
//     // Setup a timer to visualize some stuff.
//     this.render();
//   },
//
//   onStreamError: function(e) {
//     console.error(e);
//   },
//
//   getGrayColor: function(value) {
//     return 'rgb(V, V, V)'.replace(/V/g, 255 - value);
//   },
//
//   getFullColor: function(value) {
//
//     var colorPalette = {
//       0: [0,0,0],
//       10: [75, 0, 159],
//       20: [104,0,251],
//       30: [131,0,255],
//       40: [155,18,157],
//       50: [175, 37, 0],
//       60: [191, 59, 0],
//       70: [206, 88, 0],
//       80: [223, 132, 0],
//       90: [240, 188, 0],
//       100: [255, 252, 0]
//
//     }
//
//     //floor to nearest 10:
//     var decimalised = 100 * value / 255
//     var percent = decimalised / 100;
//     var floored = 10* Math.floor(decimalised / 10);
//     var distFromFloor = decimalised - floored;
//     var distFromFloorPercentage = distFromFloor/10;
//     if (decimalised < 100){
//       var rangeToNextColor = [
//         colorPalette[floored + 10][0] - colorPalette[floored + 10][0],
//         colorPalette[floored + 10][1] - colorPalette[floored + 10][1],
//         colorPalette[floored + 10][2] - colorPalette[floored + 10][2]
//       ]
//     } else {
//       var rangeToNextColor = [0,0,0];
//     }
//
//     var color = [
//       colorPalette[floored][0] + distFromFloorPercentage * rangeToNextColor[0],
//       colorPalette[floored][1] + distFromFloorPercentage * rangeToNextColor[1],
//       colorPalette[floored][2] + distFromFloorPercentage * rangeToNextColor[2]
//     ]
//
//
//     return "rgb(" + color[0] +", "+color[1] +"," + color[2]+")";
//
//     // var fromH = 62;
//     // var toH = 0;
//     // var percent = value / 255;
//     // var delta = percent * (toH - fromH);
//     // var hue = fromH + delta;
//     // return 'hsl(H, 100%, 50%)'.replace(/H/g, hue);
//   },
//
//   logChanged: function() {
//     if (this.showLabels) {
//       this.renderAxesLabels();
//     }
//   },
//
//   ticksChanged: function() {
//     if (this.showLabels) {
//       this.renderAxesLabels();
//     }
//   },
//
//   labelsChanged: function() {
//     if (this.showLabels) {
//       this.renderAxesLabels();
//     } else {
//       this.clearAxesLabels();
//     }
//   }
//
//  	});
//
//  // })();
