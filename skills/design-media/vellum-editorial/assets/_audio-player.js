document.addEventListener('DOMContentLoaded', function() {
  var STATE_KEY = 'vellum_audio';

  var player = document.createElement('div');
  player.className = 'audio-player';
  player.innerHTML =
    '<audio id="site-audio" src="archive/track.mp3" preload="metadata" loop></audio>' +
    '<button class="audio-player__btn" id="audio-toggle" title="Play">' +
      '<span class="audio-player__pulse"></span>' +
      '<i class="ph ph-speaker-high" id="audio-icon"></i>' +
    '</button>' +
    '<div class="audio-player__bars">' +
      '<span class="audio-player__bar"></span>' +
      '<span class="audio-player__bar"></span>' +
      '<span class="audio-player__bar"></span>' +
      '<span class="audio-player__bar"></span>' +
      '<span class="audio-player__bar"></span>' +
    '</div>' +
    '<input type="range" class="audio-player__volume" id="audio-volume" min="0" max="100" value="40" title="Volume">' +
    '<span class="audio-player__label">Track Name</span>';
  document.body.appendChild(player);

  var audio = document.getElementById('site-audio');
  var btn = document.getElementById('audio-toggle');
  var icon = document.getElementById('audio-icon');
  var vol = document.getElementById('audio-volume');
  var bars = player.querySelectorAll('.audio-player__bar');

  var audioCtx = null;
  var analyser = null;
  var source = null;
  var freqData = null;
  var animFrame = null;
  var reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function initAnalyser() {
    if (audioCtx) return;
    try {
      var Ctx = window.AudioContext || window.webkitAudioContext;
      if (!Ctx) return;
      audioCtx = new Ctx();
      analyser = audioCtx.createAnalyser();
      analyser.fftSize = 64;
      analyser.smoothingTimeConstant = 0.8;
      source = audioCtx.createMediaElementSource(audio);
      source.connect(analyser);
      analyser.connect(audioCtx.destination);
      freqData = new Uint8Array(analyser.frequencyBinCount);
    } catch (err) {
      audioCtx = null;
      analyser = null;
    }
  }

  function animateBars() {
    if (!analyser || audio.paused || reducedMotion) {
      cancelAnimationFrame(animFrame);
      animFrame = null;
      bars.forEach(function(b) { b.style.height = '3px'; });
      return;
    }
    analyser.getByteFrequencyData(freqData);
    var binCount = analyser.frequencyBinCount;
    var step = Math.floor(binCount / 5);
    for (var i = 0; i < 5; i++) {
      var val = freqData[i * step + Math.floor(step / 2)];
      var h = 3 + (val / 255) * 17;
      bars[i].style.height = h + 'px';
    }
    animFrame = requestAnimationFrame(animateBars);
  }

  function updateIcon() {
    if (audio.paused) {
      icon.className = 'ph ph-speaker-x';
    } else if (audio.volume === 0) {
      icon.className = 'ph ph-speaker-none';
    } else if (audio.volume < 0.4) {
      icon.className = 'ph ph-speaker-low';
    } else {
      icon.className = 'ph ph-speaker-high';
    }
  }

  function startPlaying() {
    initAnalyser();
    if (audioCtx && audioCtx.state === 'suspended') {
      audioCtx.resume().catch(function() {});
    }
    audio.play().then(function() {
      player.classList.add('audio-player--playing');
      updateIcon();
      animateBars();
    }).catch(function(err) {
      player.classList.remove('audio-player--playing');
      updateIcon();
    });
  }

  function stopPlaying() {
    audio.pause();
    player.classList.remove('audio-player--playing');
    updateIcon();
  }

  audio.addEventListener('error', function() {
    btn.disabled = true;
    btn.title = 'Audio unavailable';
  });

  var saved = null;
  try {
    saved = JSON.parse(sessionStorage.getItem(STATE_KEY));
  } catch (e) {}
  if (saved) {
    audio.volume = saved.volume != null ? saved.volume : 0.4;
    vol.value = Math.round(audio.volume * 100);
    var t = parseFloat(saved.time);
    if (!isNaN(t) && t > 0) audio.currentTime = t;
    if (saved.playing) {
      startPlaying();
    }
  } else {
    audio.volume = 0.4;
  }

  window.addEventListener('vellum:authenticated', function() {
    if (audio.paused) startPlaying();
  });

  btn.addEventListener('click', function() {
    if (audio.paused) {
      startPlaying();
    } else {
      stopPlaying();
    }
  });

  vol.addEventListener('input', function() {
    audio.volume = vol.value / 100;
    updateIcon();
  });

  window.addEventListener('beforeunload', function() {
    try {
      sessionStorage.setItem(STATE_KEY, JSON.stringify({
        playing: !audio.paused,
        time: audio.currentTime,
        volume: audio.volume
      }));
    } catch (e) {}
  });
});
