"use client";

import { useState, useRef, useEffect, useMemo } from "react";
import { Search, X } from "lucide-react";
import type { AirportWithCoords } from "@/lib/types";

interface Props {
    airports: AirportWithCoords[];
    onSelect: (airport: AirportWithCoords) => void;
}

export default function AirportSearch({ airports, onSelect }: Props) {
    const [query, setQuery] = useState("");
    const [open, setOpen] = useState(false);
    const inputRef = useRef<HTMLInputElement>(null);
    const containerRef = useRef<HTMLDivElement>(null);

    const filtered = useMemo(() => {
        if (!query.trim()) return [];
        const q = query.toLowerCase();
        return airports
            .filter(
                (a) =>
                    a.airport_code.toLowerCase().includes(q) ||
                    a.name.toLowerCase().includes(q) ||
                    a.municipality.toLowerCase().includes(q)
            )
            .slice(0, 8);
    }, [query, airports]);

    useEffect(() => {
        function handleClickOutside(e: MouseEvent) {
            if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
                setOpen(false);
            }
        }
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    function handlePick(airport: AirportWithCoords) {
        onSelect(airport);
        setQuery("");
        setOpen(false);
    }

    return (
        <div className="map-search" ref={containerRef}>
            <div className="map-search__input-wrap">
                <Search size={16} className="map-search__icon" />
                <input
                    ref={inputRef}
                    type="text"
                    className="map-search__input"
                    placeholder="Search airport..."
                    value={query}
                    onChange={(e) => {
                        setQuery(e.target.value);
                        setOpen(true);
                    }}
                    onFocus={() => setOpen(true)}
                />
                {query && (
                    <button
                        className="map-search__clear"
                        onClick={() => {
                            setQuery("");
                            inputRef.current?.focus();
                        }}
                    >
                        <X size={14} />
                    </button>
                )}
            </div>
            {open && filtered.length > 0 && (
                <div className="map-search__results">
                    {filtered.map((a) => (
                        <button
                            key={a.airport_code}
                            className="map-search__result"
                            onClick={() => handlePick(a)}
                        >
                            <span className="map-search__result-code">
                                {a.airport_code}
                            </span>
                            <span className="map-search__result-name">{a.name}</span>
                        </button>
                    ))}
                </div>
            )}
        </div>
    );
}
