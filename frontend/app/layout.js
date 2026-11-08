import "./globals.css";
import Navbar from "@/components/Navbar";

export const metadata = {
  title: "MyShop",
  description: "E-commerce demo built with Next.js + FastAPI + PostgreSQL",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <Navbar />
        <main className="container page">{children}</main>
        <footer className="footer">MyShop — Next.js + FastAPI + PostgreSQL + Razorpay</footer>
      </body>
    </html>
  );
}
