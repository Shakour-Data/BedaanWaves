"use client";

import { type ReactNode, useState, useEffect, useRef } from "react";

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

  useEffect(() => {
    if (children !== displayChildren) {
      Promise.resolve().then(() => {
        setTransitionStage("exit");

        timeoutRef.current = setTimeout(() => {
          setDisplayChildren(children);
          setTransitionStage("enter");
        }, 200);
      });
    }

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [children, displayChildren]);

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
