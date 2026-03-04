"use client";

import dynamic from "next/dynamic";
import type { AirportWithCoords } from "@/lib/types";

const AirportMap = dynamic(() => import("./AirportMap"), { ssr: false });

interface Props {
    airports: AirportWithCoords[];
}

export default function MapClientWrapper({ airports }: Props) {
    return <AirportMap airports={airports} />;
}
