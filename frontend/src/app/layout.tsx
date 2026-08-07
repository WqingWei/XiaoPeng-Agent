import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "小鹏 AI 出行服务管家",
  description: "面向车主自驾与 Robotaxi 乘客的智能出行服务编排 Agent",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="zh-CN"
      className="h-full antialiased"
    >
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
