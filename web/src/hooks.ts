import { useLayoutEffect, useRef, useState } from "react";

/** Tracks the rendered width of an element so SVG charts can redraw responsively. */
export function useWidth<T extends HTMLElement>(fallback = 800) {
  const ref = useRef<T>(null);
  const [width, setWidth] = useState(fallback);
  useLayoutEffect(() => {
    const node = ref.current;
    if (!node) return;
    setWidth(node.clientWidth);
    const observer = new ResizeObserver(([entry]) => setWidth(entry.contentRect.width));
    observer.observe(node);
    return () => observer.disconnect();
  }, []);
  return [ref, width] as const;
}

export type Hover<T> = { item: T; x: number; y: number } | null;
