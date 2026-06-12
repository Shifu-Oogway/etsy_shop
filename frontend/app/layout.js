import "./globals.css";

export const metadata = {
  title: "Etsy AI — Dashboard",
  description: "Automated Etsy digital product platform",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
