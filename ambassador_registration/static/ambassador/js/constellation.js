/* ============================================================
   Constellation / Particle Network Canvas
   Matches the deep cosmic constellation background from
   SPAC Phase 1 & 2 forms.
   ============================================================ */
(function () {
  'use strict';

  var canvas = document.getElementById('constellation-canvas');
  if (!canvas) return;

  var ctx = canvas.getContext('2d');
  if (!ctx) return;

  var width, height;
  var points = [];
  var animFrameId = null;

  function resize() {
    width = canvas.width = window.innerWidth;
    height = canvas.height = Math.max(window.innerHeight, document.documentElement.scrollHeight);
    initPoints();
  }

  function initPoints() {
    // Generate an appropriate density of nodes based on viewport size
    var count = Math.min(Math.floor((width * height) / 20000), 120);
    if (count < 35) count = 35;
    points = [];

    for (var i = 0; i < count; i++) {
      points.push({
        x: Math.random() * width,
        y: Math.random() * height,
        vx: (Math.random() - 0.5) * 0.35,
        vy: (Math.random() - 0.5) * 0.35,
        radius: Math.random() * 2 + 1.2
      });
    }
  }

  function render() {
    ctx.clearRect(0, 0, width, height);

    var maxDist = 130;
    var maxDistSq = maxDist * maxDist;

    // Draw connecting lines
    for (var i = 0; i < points.length; i++) {
      var p1 = points[i];

      // Update positions
      p1.x += p1.vx;
      p1.y += p1.vy;

      if (p1.x < 0 || p1.x > width) p1.vx *= -1;
      if (p1.y < 0 || p1.y > height) p1.vy *= -1;

      // Draw node point
      ctx.beginPath();
      ctx.arc(p1.x, p1.y, p1.radius, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(170, 215, 255, 0.65)';
      ctx.fill();

      // Connect near neighbors
      for (var j = i + 1; j < points.length; j++) {
        var p2 = points[j];
        var dx = p1.x - p2.x;
        var dy = p1.y - p2.y;
        var distSq = dx * dx + dy * dy;

        if (distSq < maxDistSq) {
          var dist = Math.sqrt(distSq);
          var alpha = (1 - dist / maxDist) * 0.28;
          ctx.beginPath();
          ctx.moveTo(p1.x, p1.y);
          ctx.lineTo(p2.x, p2.y);
          ctx.strokeStyle = 'rgba(100, 185, 255, ' + alpha.toFixed(3) + ')';
          ctx.lineWidth = 1;
          ctx.stroke();
        }
      }
    }

    animFrameId = requestAnimationFrame(render);
  }

  window.addEventListener('resize', resize);
  window.addEventListener('orientationchange', resize);
  document.addEventListener('DOMContentLoaded', function () {
    resize();
    render();
  });

  if (document.readyState === 'complete' || document.readyState === 'interactive') {
    resize();
    render();
  }
})();
