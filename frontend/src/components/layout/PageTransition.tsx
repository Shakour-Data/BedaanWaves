"use client";

import { type ReactNode, useState, useEffect, useRef } from "react";
import { cn } from "@/lib/cn";

interface PageTransitionProps {
  children: ReactNode;
  transitionType?: "fade" | "slide";
}

export function PageTransition({
  children,
  transitionType = "fade",
}: PageTransitionProps) {
  const [displayChildren, setDisplayChildren] = useState(children);
  const [transitionStage, setTransitionStage] = useState("enter");
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const prevChildrenRef = useRef(children);

  useEffect(() => {
    if (children !== prevChildrenRef.current) {
      prevChildrenRef.current = children;
      setTransitionStage("exit");

      timeoutRef.current = setTimeout(() => {
        setDisplayChildren(children);
        setTransitionStage("enter");
      }, 200);
    }

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [children]);

  const animationClass =
    transitionType === "slide"
      ? transitionStage === "enter"
        ? "page-transition-slide-enter"
        : "page-transition-slide-exit"
      : transitionStage === "enter"
      ? "page-transition-enter"
      : "page-transition-exit";

  return (
    <div className={animationClass} key={transitionStage}>
      {displayChildren}
    </div>
  );
}

interface ScrollRevealProps {
  children: ReactNode;
  delay?: number;
  className?: string;
  once?: boolean;
}

export function ScrollReveal({
  children,
  delay = 0,
  className,
  once = true,
}: ScrollRevealProps) {
  const ref = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (!ref.current) return;
    const obs = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true);
          if (once) obs.disconnect();
        }
      },
      { threshold: 0.08, rootMargin: "0px 0px -40px" }
    );
    obs.observe(ref.current);
    return () => obs.disconnect();
  }, [once]);

  return (
    <div
      ref={ref}
      className={cn(
        "transition-all duration-700 ease-[cubic-bezier(0.16,1,0.3,1)]",
        visible ? "opacity-100 translate-y-0 scale-100" : "opacity-0 translate-y-8 scale-95",
        className
      )}
      style={{ transitionDelay: `${delay}ms` }}
    >
      {children}
    </div>
  );
}
