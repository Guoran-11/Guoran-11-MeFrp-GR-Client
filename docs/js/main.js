/* =========================================================
   MeFrp-GR-Client Promo Site · Interactions
   - Cursor glow tracking
   - Particle network
   - IntersectionObserver reveal
   - 3D tilt on cards
   - Number counter
   - Smooth parallax preview
   - Mobile drawer, back-to-top
   ========================================================= */

(() => {
  'use strict';

  /* ---------- Cursor glow ---------- */
  const glow = document.getElementById('cursorGlow');
  if (glow && window.matchMedia('(min-width: 769px)').matches) {
    let tx = window.innerWidth / 2, ty = window.innerHeight / 2;
    let cx = tx, cy = ty;
    window.addEventListener('mousemove', (e) => { tx = e.clientX; ty = e.clientY; });
    const tick = () => {
      cx += (tx - cx) * 0.12;
      cy += (ty - cy) * 0.12;
      glow.style.transform = `translate(${cx}px, ${cy}px) translate(-50%, -50%)`;
      requestAnimationFrame(tick);
    };
    tick();
  }

  /* ---------- Particle network ---------- */
  const canvas = document.getElementById('particleCanvas');
  if (canvas) {
    const ctx = canvas.getContext('2d');
    let particles = [];
    let w, h;
    const PARTICLE_DENSITY = 0.00009; // 每像素粒子数
    const LINK_DIST = 130;

    function resize() {
      w = canvas.width = window.innerWidth * devicePixelRatio;
      h = canvas.height = window.innerHeight * devicePixelRatio;
      canvas.style.width = window.innerWidth + 'px';
      canvas.style.height = window.innerHeight + 'px';
      const target = Math.max(40, Math.min(120, Math.floor(w * h * PARTICLE_DENSITY / (devicePixelRatio ** 2))));
      particles = [];
      for (let i = 0; i < target; i++) {
        particles.push({
          x: Math.random() * w,
          y: Math.random() * h,
          vx: (Math.random() - 0.5) * 0.4 * devicePixelRatio,
          vy: (Math.random() - 0.5) * 0.4 * devicePixelRatio,
          r: (Math.random() * 1.4 + 0.6) * devicePixelRatio
        });
      }
    }
    resize();
    window.addEventListener('resize', resize);

    let mouseX = -9999, mouseY = -9999;
    window.addEventListener('mousemove', (e) => {
      mouseX = e.clientX * devicePixelRatio;
      mouseY = e.clientY * devicePixelRatio;
    });

    function step() {
      ctx.clearRect(0, 0, w, h);
      for (let p of particles) {
        p.x += p.vx; p.y += p.vy;
        if (p.x < 0 || p.x > w) p.vx *= -1;
        if (p.y < 0 || p.y > h) p.vy *= -1;
      }
      // 绘制连线
      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const a = particles[i], b = particles[j];
          const dx = a.x - b.x, dy = a.y - b.y;
          const d = Math.sqrt(dx * dx + dy * dy);
          if (d < LINK_DIST * devicePixelRatio) {
            const alpha = 1 - d / (LINK_DIST * devicePixelRatio);
            ctx.strokeStyle = `rgba(99, 102, 241, ${alpha * 0.18})`;
            ctx.lineWidth = 0.6 * devicePixelRatio;
            ctx.beginPath();
            ctx.moveTo(a.x, a.y);
            ctx.lineTo(b.x, b.y);
            ctx.stroke();
          }
        }
      }
      // 绘制粒子
      for (let p of particles) {
        // 鼠标交互
        const dx = p.x - mouseX, dy = p.y - mouseY;
        const d = Math.sqrt(dx * dx + dy * dy);
        if (d < 120 * devicePixelRatio) {
          ctx.fillStyle = 'rgba(6, 182, 212, 0.8)';
        } else {
          ctx.fillStyle = 'rgba(165, 180, 252, 0.7)';
        }
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fill();
      }
      requestAnimationFrame(step);
    }
    step();
  }

  /* ---------- Navbar scrolled ---------- */
  const navbar = document.getElementById('navbar');
  const onScroll = () => {
    if (window.scrollY > 30) navbar.classList.add('scrolled');
    else navbar.classList.remove('scrolled');
    // back to top
    if (window.scrollY > 400) backTop.classList.add('show');
    else backTop.classList.remove('show');
  };
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  /* ---------- Mobile drawer ---------- */
  const toggle = document.getElementById('navToggle');
  const drawer = document.getElementById('mobileDrawer');
  if (toggle && drawer) {
    toggle.addEventListener('click', () => {
      toggle.classList.toggle('active');
      drawer.classList.toggle('open');
    });
    drawer.querySelectorAll('a').forEach(a => a.addEventListener('click', () => {
      toggle.classList.remove('active');
      drawer.classList.remove('open');
    }));
  }

  /* ---------- Reveal on scroll ---------- */
  const reveals = document.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window) {
    const io = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('in-view');
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -60px 0px' });
    reveals.forEach(el => io.observe(el));
  } else {
    reveals.forEach(el => el.classList.add('in-view'));
  }

  /* ---------- Number counter ---------- */
  const nums = document.querySelectorAll('.stat-num');
  const numObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        const el = entry.target;
        const target = parseInt(el.dataset.target, 10);
        const duration = 1600;
        const start = performance.now();
        const animate = (now) => {
          const t = Math.min(1, (now - start) / duration);
          // easeOutCubic
          const eased = 1 - Math.pow(1 - t, 3);
          el.textContent = Math.floor(eased * target);
          if (t < 1) requestAnimationFrame(animate);
          else el.textContent = target;
        };
        requestAnimationFrame(animate);
        numObserver.unobserve(el);
      }
    });
  }, { threshold: 0.4 });
  nums.forEach(n => numObserver.observe(n));

  /* ---------- 3D tilt on feature cards ---------- */
  const tilts = document.querySelectorAll('.tilt');
  tilts.forEach(card => {
    let raf = null;
    card.addEventListener('mousemove', (e) => {
      const r = card.getBoundingClientRect();
      const x = e.clientX - r.left;
      const y = e.clientY - r.top;
      const rx = ((y / r.height) - 0.5) * -8;
      const ry = ((x / r.width) - 0.5) * 8;
      if (raf) cancelAnimationFrame(raf);
      raf = requestAnimationFrame(() => {
        card.style.transform = `translateY(-4px) perspective(800px) rotateX(${rx}deg) rotateY(${ry}deg)`;
        card.style.setProperty('--mx', `${(x / r.width) * 100}%`);
        card.style.setProperty('--my', `${(y / r.height) * 100}%`);
      });
    });
    card.addEventListener('mouseleave', () => {
      if (raf) cancelAnimationFrame(raf);
      card.style.transform = '';
    });
  });

  /* ---------- Hero preview parallax ---------- */
  const device = document.querySelector('.hero-device');
  if (device && window.matchMedia('(min-width: 961px)').matches) {
    document.addEventListener('mousemove', (e) => {
      const cx = window.innerWidth / 2;
      const cy = window.innerHeight / 2;
      const dx = (e.clientX - cx) / cx;
      const dy = (e.clientY - cy) / cy;
      device.style.transform = `translate3d(${dx * 10}px, ${dy * 8}px, 0)`;
    });
  }

  /* ---------- Preview frame mouse tilt ---------- */
  const previewFrame = document.querySelector('.preview-frame');
  if (previewFrame && window.matchMedia('(min-width: 961px)').matches) {
    const stage = document.querySelector('.preview-stage');
    stage.addEventListener('mousemove', (e) => {
      const r = stage.getBoundingClientRect();
      const x = (e.clientX - r.left) / r.width - 0.5;
      const y = (e.clientY - r.top) / r.height - 0.5;
      previewFrame.style.transform = `rotateX(${-y * 6}deg) rotateY(${x * 8}deg)`;
    });
    stage.addEventListener('mouseleave', () => {
      previewFrame.style.transform = 'rotateX(2deg) rotateY(0deg)';
    });
  }

  /* ---------- Back to top ---------- */
  const backTop = document.getElementById('backTop');
  if (backTop) {
    backTop.addEventListener('click', () => {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }

  /* ---------- Smooth scroll for anchor links ---------- */
  document.querySelectorAll('a[href^="#"]').forEach(a => {
    a.addEventListener('click', (e) => {
      const id = a.getAttribute('href');
      if (id.length < 2) return;
      const target = document.querySelector(id);
      if (!target) return;
      e.preventDefault();
      const offset = 80;
      const top = target.getBoundingClientRect().top + window.scrollY - offset;
      window.scrollTo({ top, behavior: 'smooth' });
    });
  });
})();
