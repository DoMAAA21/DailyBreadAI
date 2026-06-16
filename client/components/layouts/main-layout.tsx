"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { BookOpen, Menu, X } from "lucide-react";
import { appConfig, menuItems, type MenuItem } from "@/lib/menu-config";
import { cn } from "@/lib/utils";

type MainLayoutProps = {
  children: React.ReactNode;
};

function NavLinks({
  items,
  onNavigate,
}: {
  items: MenuItem[];
  onNavigate?: () => void;
}) {
  const pathname = usePathname();

  return (
    <nav className="flex w-full flex-col gap-1.5 px-3 py-3">
      {items.map((item) => {
        const isActive =
          item.href === "/"
            ? pathname === "/"
            : pathname.startsWith(item.href);
        const Icon = item.icon;

        return (
          <Link
            key={item.href}
            href={item.href}
            onClick={onNavigate}
            className={cn(
              "flex w-full items-center gap-3 rounded-xl px-3 py-3 text-sm transition-colors",
              isActive
                ? "bg-sidebar-primary text-sidebar-primary-foreground"
                : "text-sidebar-foreground/80 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
            )}
          >
            <Icon className="size-4 shrink-0" />
            <div className="min-w-0">
              <p className="font-medium">{item.title}</p>
              {item.description ? (
                <p
                  className={cn(
                    "truncate text-xs",
                    isActive
                      ? "text-sidebar-primary-foreground/80"
                      : "text-sidebar-foreground/50"
                  )}
                >
                  {item.description}
                </p>
              ) : null}
            </div>
          </Link>
        );
      })}
    </nav>
  );
}

function SidebarContent({ onNavigate }: { onNavigate?: () => void }) {
  return (
    <div className="flex h-full w-full min-w-0 flex-col">
      <div className="flex items-center gap-3 border-b border-sidebar-border px-5 py-5">
        <div className="flex size-10 items-center justify-center rounded-lg bg-sacred-gold/20">
          <BookOpen className="size-5 text-sacred-gold" />
        </div>
        <div>
          <p className="font-bold text-sidebar-foreground">{appConfig.name}</p>
          <p className="text-xs text-sidebar-foreground/70">{appConfig.tagline}</p>
        </div>
      </div>

      <div className="w-full flex-1 overflow-y-auto">
        <NavLinks items={menuItems} onNavigate={onNavigate} />
      </div>
    </div>
  );
}

export function MainLayout({ children }: MainLayoutProps) {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const pathname = usePathname();

  useEffect(() => {
    setDrawerOpen(false);
  }, [pathname]);

  useEffect(() => {
    if (!drawerOpen) return;

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    return () => {
      document.body.style.overflow = previousOverflow;
    };
  }, [drawerOpen]);

  return (
    <div className="flex h-dvh min-h-0 bg-background">
      <aside className="hidden w-72 shrink-0 flex-col border-r border-sidebar-border bg-accent text-sidebar-foreground md:flex">
        <SidebarContent />
      </aside>

      <div className="flex min-h-0 min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-sacred-gold/20 bg-background px-4 py-3 md:hidden">
          <div className="flex items-center gap-2">
            <div className="flex size-9 items-center justify-center rounded-lg bg-sacred-gold/20">
              <BookOpen className="size-4 text-sacred-gold" />
            </div>
            <div>
              <p className="text-sm font-bold text-foreground">
                {appConfig.name}
              </p>
              <p className="text-xs text-muted-foreground">
                {appConfig.tagline}
              </p>
            </div>
          </div>

          <button
            type="button"
            aria-label={drawerOpen ? "Close menu" : "Open menu"}
            aria-expanded={drawerOpen}
            onClick={() => setDrawerOpen((open) => !open)}
            className="inline-flex size-10 items-center justify-center rounded-lg text-foreground hover:bg-black/5"
          >
            {drawerOpen ? <X className="size-5" /> : <Menu className="size-5" />}
          </button>
        </header>

        <main className="flex min-h-0 flex-1 flex-col overflow-hidden bg-background">
          {children}
        </main>
      </div>

      <div
        className={cn(
          "fixed inset-0 z-40 bg-black/50 transition-opacity md:hidden",
          drawerOpen ? "opacity-100" : "pointer-events-none opacity-0"
        )}
        onClick={() => setDrawerOpen(false)}
        aria-hidden={!drawerOpen}
      />

      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 flex w-72 flex-col border-r border-sidebar-border bg-accent text-sidebar-foreground shadow-2xl transition-transform duration-300 ease-in-out md:hidden",
          drawerOpen ? "translate-x-0" : "-translate-x-full"
        )}
        aria-hidden={!drawerOpen}
      >
        <div className="flex items-center justify-end px-3 pt-3">
          <button
            type="button"
            aria-label="Close menu"
            onClick={() => setDrawerOpen(false)}
            className="inline-flex size-10 items-center justify-center rounded-lg text-sidebar-foreground hover:bg-sidebar-accent"
          >
            <X className="size-5" />
          </button>
        </div>
        <SidebarContent onNavigate={() => setDrawerOpen(false)} />
      </aside>
    </div>
  );
}
