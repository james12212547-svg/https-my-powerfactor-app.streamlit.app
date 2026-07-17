import "./globals.css";

export const metadata = {
  title: "PFC Pro Analyzer | Engineering App",
  description: "Advanced Power Factor Correction calculation and simulation web application.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
