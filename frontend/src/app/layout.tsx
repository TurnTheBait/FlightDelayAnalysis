import type { Metadata } from "next";
import "./globals.css";
import Sidebar from "@/components/Sidebar";

export const metadata: Metadata = {
  title: "FlightPulse - Aviation Data Dashboard",
  description:
    "Advanced aviation data dashboard combining NLP sentiment analysis, media pressure indexing, flight delays, weather data, and geospatial population analysis across European airports.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <div className="ambient-blob ambient-blob--primary" />
        <div className="ambient-blob ambient-blob--secondary" />
        <div className="app-shell">
          <Sidebar />
          <main className="main-content">{children}</main>
        </div>
      </body>
    </html>
  );
}
