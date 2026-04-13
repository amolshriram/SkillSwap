(() => {
  // Small UX helper: confirm for destructive actions.
  document.addEventListener("submit", (e) => {
    const form = e.target;
    if (!(form instanceof HTMLFormElement)) return;
    const msg = form.getAttribute("data-confirm");
    if (msg && !window.confirm(msg)) e.preventDefault();
  });

  // Auto-dismiss flash messages after a short delay.
  window.addEventListener("load", () => {
    const messages = document.querySelectorAll(".message");
    messages.forEach((el) => {
      window.setTimeout(() => {
        el.style.transition = "opacity 300ms ease, transform 300ms ease";
        el.style.opacity = "0";
        el.style.transform = "translateY(-4px)";
        window.setTimeout(() => el.remove(), 350);
      }, 3500);
    });
  });

  // Home: interactive "How it works" steps.
  window.addEventListener("load", () => {
    const root = document.querySelector("[data-how]");
    const stepsWrap = document.querySelector("[data-how-steps]");
    if (!root || !stepsWrap) return;

    const steps = Array.from(stepsWrap.querySelectorAll("[data-step]"));
    if (!steps.length) return;

    const pulse = (el) => {
      el.classList.remove("is-pulsing");
      // Force reflow so animation can restart even on same element
      void el.offsetWidth;
      el.classList.add("is-pulsing");
    };

    const setActive = (el) => {
      steps.forEach((s) => s.classList.toggle("is-active", s === el));
      pulse(el);
    };

    steps.forEach((btn) => {
      btn.addEventListener("animationend", (e) => {
        if (e.animationName === "uStepPulse") btn.classList.remove("is-pulsing");
      });
      btn.addEventListener("click", () => setActive(btn));
      btn.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          setActive(btn);
        }
      });
    });

    // Default active (first card) AFTER listeners are attached
    setActive(steps[0]);
  });
})();

