"use client";

import { useState, useEffect } from "react";

export function useTheme() {
    const [theme, setTheme] = useState<"light" | "dark">("dark");

    useEffect(() => {
        // Initial setup
        const isLight = document.documentElement.getAttribute("data-theme") === "light";
        setTheme(isLight ? "light" : "dark");

        // Listen for future changes
        const observer = new MutationObserver((mutations) => {
            for (const mutation of mutations) {
                if (mutation.type === "attributes" && mutation.attributeName === "data-theme") {
                    const newTheme = document.documentElement.getAttribute("data-theme") === "light" ? "light" : "dark";
                    setTheme(newTheme);
                }
            }
        });

        observer.observe(document.documentElement, {
            attributes: true,
            attributeFilter: ["data-theme"]
        });

        return () => observer.disconnect();
    }, []);

    return theme;
}
