"use client";

import { useEffect, useRef, useState } from "react";

interface AnimatedNumberProps {
  value: number | null;
  decimals?: number;
  suffix?: string;
  duration?: number;
  className?: string;
}

export function AnimatedNumber({ value, decimals = 0, suffix = "", duration = 480, className }: AnimatedNumberProps) {
  const [displayValue, setDisplayValue] = useState<number | null>(value === null ? null : 0);
  const previousValue = useRef<number | null>(value === null ? null : 0);

  useEffect(() => {
    if (value === null) {
      previousValue.current = null;
      const frameId = requestAnimationFrame(() => setDisplayValue(null));
      return () => cancelAnimationFrame(frameId);
    }

    const startValue = previousValue.current ?? 0;
    previousValue.current = value;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches || startValue === value) {
      const frameId = requestAnimationFrame(() => setDisplayValue(value));
      return () => cancelAnimationFrame(frameId);
    }

    let frameId = 0;
    const startedAt = performance.now();
    const animate = (now: number) => {
      const progress = Math.min((now - startedAt) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplayValue(startValue + (value - startValue) * eased);
      if (progress < 1) frameId = requestAnimationFrame(animate);
    };
    frameId = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(frameId);
  }, [duration, value]);

  const formatted = displayValue === null ? "--" : displayValue.toFixed(decimals);
  return <span className={`metric-number ${className ?? ""}`}>{formatted}{displayValue === null ? "" : suffix}</span>;
}
