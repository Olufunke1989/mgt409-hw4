import { useEffect } from "react";
import { useLocation } from "react-router-dom";

/** Gives each product a steady pastel background, so the grid feels varied but calm. */
export function tintFor(id: string): string {
  let h = 0;
  for (let i = 0; i < id.length; i++) h = (h * 31 + id.charCodeAt(i)) >>> 0;
  return `tint-${h % 5}`;
}

// Rough colours for the swatches next to the colour names on product pages.
const SWATCHES: [RegExp, string][] = [
  [/navy/, "#1c2a5a"], [/royal|bright blue|electric/, "#2f5bff"], [/blue/, "#3c6fd1"],
  [/charcoal/, "#3d3f45"], [/black/, "#16161a"], [/heather|gray|grey|ash|silver/, "#b8bcc6"],
  [/white|cream|ivory/, "#ffffff"], [/red|maroon|crimson/, "#c8322f"], [/coral|salmon|peach/, "#ff8a73"],
  [/pink/, "#f4a3c0"], [/green|forest|kelly/, "#2f8a57"], [/yellow|gold/, "#f2c94c"], [/orange/, "#f2994a"],
  [/purple|violet|lavender/, "#9b7bff"], [/brown|tan|khaki/, "#a07a52"],
];
export function swatchFor(color: string): string {
  const c = color.toLowerCase();
  return SWATCHES.find(([re]) => re.test(c))?.[1] ?? "#d9d4e8";
}

/**
 * Gentle motion for the whole site:
 * - elements with class "reveal" fade up as they scroll into view
 * - a --scroll variable lets decorative shapes drift a little (parallax)
 * Turned off automatically for people who prefer reduced motion.
 */
export function useSiteMotion() {
  const { pathname } = useLocation();

  useEffect(() => {
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const io = new IntersectionObserver(
      (entries) => {
        for (const e of entries) {
          if (e.isIntersecting) {
            e.target.classList.add("in");
            io.unobserve(e.target);
          }
        }
      },
      { rootMargin: "0px 0px -8% 0px", threshold: 0.08 },
    );
    const watch = () => {
      document.querySelectorAll(".reveal:not(.in)").forEach((el) => {
        if (reduce) el.classList.add("in");
        else io.observe(el);
      });
    };
    watch();
    const mo = new MutationObserver(watch);
    mo.observe(document.getElementById("main") ?? document.body, { childList: true, subtree: true });
    return () => {
      io.disconnect();
      mo.disconnect();
    };
  }, [pathname]);

  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    let frame = 0;
    const onScroll = () => {
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(() => document.documentElement.style.setProperty("--scroll", String(window.scrollY)));
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => {
      window.removeEventListener("scroll", onScroll);
      cancelAnimationFrame(frame);
    };
  }, []);
}
