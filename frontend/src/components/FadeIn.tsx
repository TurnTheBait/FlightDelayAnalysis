"use client";

import type { ReactNode } from "react";

export default function FadeIn({
    children,
    delay = 0,
    className,
}: {
    children: ReactNode;
    delay?: number;
    className?: string;
}) {
    return (
        <div
            className={`fade-in ${className ?? ""}`}
            style={{ animationDelay: `${delay}s` }}
        >
            {children}
        </div>
    );
}
