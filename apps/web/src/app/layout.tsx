import type { Metadata } from "next";
import Sidebar from "@/components/sidebar";
import "./globals.css";

export const metadata: Metadata = {
  title: "Interview Agent",
  description: "单用户多画像智能模拟面试系统",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN" className="h-full antialiased">
      <body className="min-h-full flex bg-bg text-ink">
        <Sidebar />
        <main className="flex-1 ml-60 flex justify-center px-6 py-8">
          <div className="w-full max-w-3xl animate-fade-in">
            {children}
          </div>
        </main>
      </body>
    </html>
  );
}
