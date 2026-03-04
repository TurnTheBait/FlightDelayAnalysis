"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Globe, MapPin, Clock, Cloud, Volume2, Plane } from "lucide-react";

const NAV_ITEMS = [
    { href: "/", label: "Global Summary", icon: Globe },
    { href: "/map", label: "Airport Map", icon: MapPin },
    { href: "/delays", label: "Operational Delays", icon: Clock },
    { href: "/weather", label: "Weather Impact", icon: Cloud },
    { href: "/noise", label: "Noise & Population", icon: Volume2 },
];

export default function Sidebar() {
    const pathname = usePathname();

    return (
        <aside className="sidebar">
            <div className="sidebar__logo">
                <div className="sidebar__logo-icon">
                    <Plane size={16} color="#fff" />
                </div>
                <span className="sidebar__logo-text">FlightAnalysis</span>
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
    );
}
