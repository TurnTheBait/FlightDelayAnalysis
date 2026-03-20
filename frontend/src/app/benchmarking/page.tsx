import { loadAllBenchmarkData } from "@/lib/csv";
import BenchmarkingContent from "@/components/BenchmarkingContent";
import FadeIn from "@/components/FadeIn";

export default function BenchmarkingPage() {
    const { summaries, details } = loadAllBenchmarkData();

    const categoryCounts = {
        hub: details.general.hub.length,
        large: details.general.large.length,
        medium: details.general.medium.length,
        small: details.general.small.length,
    };

    return (
        <>
            <FadeIn>
                <header className="page-header">
                    <h1 className="page-header__title">Benchmarking</h1>
                    <p className="page-header__subtitle">
                        Airport performance benchmarking by traffic category. Airports are
                        classified into Hub, Large, Medium, and Small tiers based on annual
                        flight volume, then ranked within each tier by weighted sentiment score.
                    </p>
                </header>
            </FadeIn>

            <BenchmarkingContent
                summaries={summaries}
                details={details}
                categoryCounts={categoryCounts}
            />
        </>
    );
}
