"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Sidebar } from "@/components/layout/sidebar";
import { TopNav } from "@/components/layout/top-nav";
import { InspectorPanel } from "@/components/layout/inspector";
import { StatusBar } from "@/components/layout/status-bar";
import { CommandPalette } from "@/components/command/command-palette";

export default function AppShellLayout({ children }: { children: React.ReactNode }) {
  const [commandOpen, setCommandOpen] = useState(false);

  return (
    <div className="flex h-screen overflow-hidden bg-[var(--background)] text-[var(--foreground)]">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <TopNav onOpenCommand={() => setCommandOpen(true)} />
        <div className="flex min-h-0 flex-1">
          <main className="sf-scrollbar min-w-0 flex-1 overflow-auto p-6">
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.25 }}
            >
              {children}
            </motion.div>
          </main>
          <InspectorPanel />
        </div>
        <StatusBar />
      </div>
      <CommandPalette open={commandOpen} onOpenChange={setCommandOpen} />
    </div>
  );
}
