'use strict';

var Player = (function() {

  function Player(config) {
    var defaults = {};
    this.opt = _.extend({}, defaults, config);
    this.init();
  }

  Player.prototype.init = function(){
    this.sound = false;
    this.soundIndex = -1;
  };

  Player.prototype.play = function(entry, playFull, $el){
    var spriteKey = playFull ? "full" : "phrase";
    if (entry.index !== this.soundIndex) {
      if (this.sound) this.sound.unload();
      var sound = new Howl({
        src: entry.audioFile,
        sprite: {
          "phrase": [entry.start, entry.dur],
          "full": [0, 60000]
        },
        onend: function(){
          if ($el) $el.removeClass('playing');
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
    if ($el) $el.addClass('playing');
  };

  return Player;

})();
