/**
 * MPMS — Scroll Reveal & UI Enhancement Animations
 * IntersectionObserver-based entrance animations + polished micro-interactions
 * Respects prefers-reduced-motion
 */

(function () {
  'use strict';

  /* ── Respect reduced-motion preference ─────────────────────────────── */
  const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ── Scroll Reveal ──────────────────────────────────────────────────── */
  if (!prefersReduced && 'IntersectionObserver' in window) {
    const revealObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('is-visible');
            revealObserver.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12, rootMargin: '0px 0px -40px 0px' }
    );

    document.querySelectorAll('.zp-reveal').forEach((el) => revealObserver.observe(el));

    /* Stagger children inside a stagger group */
    document.querySelectorAll('.zp-stagger-group').forEach((group) => {
      const children = group.querySelectorAll('.zp-stagger-child');
      children.forEach((child, i) => {
        child.style.transitionDelay = `${i * 80}ms`;
      });

      const staggerObserver = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) {
              entry.target.querySelectorAll('.zp-stagger-child').forEach((c) => {
                c.classList.add('is-visible');
              });
              staggerObserver.unobserve(entry.target);
            }
          });
        },
        { threshold: 0.08 }
      );
      staggerObserver.observe(group);
    });
  } else {
    /* No animation — just show everything immediately */
    document.querySelectorAll('.zp-reveal, .zp-stagger-child').forEach((el) => {
      el.classList.add('is-visible');
    });
  }

  /* ── Navbar scroll shadow ───────────────────────────────────────────── */
  const navbar = document.querySelector('.zp-navbar');
  if (navbar) {
    const onScroll = () => {
      if (window.scrollY > 8) {
        navbar.classList.add('scrolled');
      } else {
        navbar.classList.remove('scrolled');
      }
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

  /* ── Progress bar animated fill ────────────────────────────────────── */
  if (!prefersReduced && 'IntersectionObserver' in window) {
    const barObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const bar = entry.target;
            const target = bar.getAttribute('data-width') || bar.style.width;
            bar.style.width = '0%';
            requestAnimationFrame(() => {
              setTimeout(() => {
                bar.style.transition = 'width 0.9s cubic-bezier(0.25, 0.46, 0.45, 0.94)';
                bar.style.width = target;
              }, 150);
            });
            barObserver.unobserve(bar);
          }
        });
      },
      { threshold: 0.5 }
    );
    document.querySelectorAll('.progress-bar').forEach((bar) => {
      const w = bar.style.width;
      if (w) bar.setAttribute('data-width', w);
      barObserver.observe(bar);
    });
  }

  /* ── Stat counter animation ─────────────────────────────────────────── */
  if (!prefersReduced && 'IntersectionObserver' in window) {
    const counterObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const el = entry.target;
            const end = parseInt(el.textContent, 10);
            if (!isNaN(end) && end > 0) {
              let start = 0;
              const duration = 900;
              const step = Math.ceil(end / (duration / 16));
              el.textContent = '0';
              const timer = setInterval(() => {
                start += step;
                if (start >= end) {
                  el.textContent = end;
                  clearInterval(timer);
                } else {
                  el.textContent = start;
                }
              }, 16);
            }
            counterObserver.unobserve(el);
          }
        });
      },
      { threshold: 0.6 }
    );
    document.querySelectorAll('.zp-stat-val').forEach((el) => counterObserver.observe(el));
  }

  /* ── Table row hover ripple effect ─────────────────────────────────── */
  document.querySelectorAll('.zp-table tbody tr').forEach((row) => {
    row.addEventListener('mouseenter', () => row.classList.add('zp-row-hover'));
    row.addEventListener('mouseleave', () => row.classList.remove('zp-row-hover'));
  });

  /* ── Flash auto-dismiss after 5s ───────────────────────────────────── */
  document.querySelectorAll('.alert.fade.show').forEach((alert) => {
    setTimeout(() => {
      alert.classList.remove('show');
      setTimeout(() => alert.remove(), 300);
    }, 5000);
  });

  /* ── Smooth active nav highlight on hash change ─────────────────────── */
  const navLinks = document.querySelectorAll('.zp-nav-link[href^="#"]');
  if (navLinks.length) {
    const sections = Array.from(navLinks)
      .map((l) => document.querySelector(l.getAttribute('href')))
      .filter(Boolean);

    const sectionObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            navLinks.forEach((l) => l.classList.remove('active'));
            const active = document.querySelector(`.zp-nav-link[href="#${entry.target.id}"]`);
            if (active) active.classList.add('active');
          }
        });
      },
      { threshold: 0.45 }
    );
    sections.forEach((s) => sectionObserver.observe(s));
  }
})();
