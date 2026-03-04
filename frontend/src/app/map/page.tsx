import { loadAirportsWithCoords } from "@/lib/csv";
import MapClientWrapper from "@/components/map/MapClientWrapper";

export default function MapPage() {
    const airports = loadAirportsWithCoords();

    return <MapClientWrapper airports={airports} />;
}
