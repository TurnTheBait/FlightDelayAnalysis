import type { Metadata } from "next";
import "./globals.css";
import Sidebar from "@/components/Sidebar";
import ThemeToggle from "@/components/ThemeToggle";

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
    <html lang="en" suppressHydrationWarning>
      <body>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              try {
                if (localStorage.getItem('theme') === 'light') {
                  document.documentElement.setAttribute('data-theme', 'light');
                }
              } catch (e) {}
            `,
          }}
        />
        <div className="ambient-blob ambient-blob--primary" />
        <div className="ambient-blob ambient-blob--secondary" />
        <ThemeToggle />
        <div className="app-shell">
          <Sidebar />
          <main className="main-content">{children}</main>
        </div>
      </body>
    </html>
  );
}
