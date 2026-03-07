"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Globe, MapPin, BarChart3, Clock, Cloud, Volume2, Plane, Menu, X } from "lucide-react";

const NAV_ITEMS = [
    { href: "/", label: "Global Summary", icon: Globe },
    { href: "/map", label: "Airport Map", icon: MapPin },
    { href: "/volume", label: "Volume Analysis", icon: BarChart3 },
    { href: "/delays", label: "Operational Delays", icon: Clock },
    { href: "/weather", label: "Weather Impact", icon: Cloud },
    { href: "/noise", label: "Noise & Population", icon: Volume2 },
];

export default function Sidebar() {
    const pathname = usePathname();
    const [mobileOpen, setMobileOpen] = useState(false);

    useEffect(() => {
        setMobileOpen(false);
    }, [pathname]);

    useEffect(() => {
        if (mobileOpen) {
            document.body.style.overflow = "hidden";
        } else {
            document.body.style.overflow = "";
        }
        return () => { document.body.style.overflow = ""; };
    }, [mobileOpen]);

    return (
        <>
            <button
                className="mobile-hamburger"
                onClick={() => setMobileOpen(true)}
                aria-label="Open menu"
            >
                <Menu size={22} />
            </button>

            {mobileOpen && (
                <div
                    className="mobile-overlay"
                    onClick={() => setMobileOpen(false)}
                />
            )}

            <aside className={`sidebar ${mobileOpen ? "sidebar--open" : ""}`}>
                <div className="sidebar__header-row">
                    <div className="sidebar__logo">
                        <div className="sidebar__logo-icon">
                            <Plane size={16} color="#fff" />
                        </div>
                        <span className="sidebar__logo-text">FlightAnalysis</span>
                    </div>
                    <button
                        className="sidebar__close"
                        onClick={() => setMobileOpen(false)}
                        aria-label="Close menu"
                    >
                        <X size={20} />
                    </button>
                </div>
                <nav className="sidebar__nav">
                    {NAV_ITEMS.map((item) => {
                        const isActive = pathname === item.href;
                        const Icon = item.icon;
                        return (
                            <Link
                                key={item.href}
                                href={item.href}
                                className={`sidebar__link ${isActive ? "sidebar__link--active" : ""}`}
                            >
                                <Icon size={18} />
                                {item.label}
                            </Link>
                        );
                    })}
                </nav>
            </aside>
        </>
    );
}
