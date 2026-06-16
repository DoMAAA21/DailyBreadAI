import {
  Bookmark,
  BookOpen,
  MessageSquare,
  Settings,
  type LucideIcon,
} from "lucide-react";

export type MenuItem = {
  title: string;
  href: string;
  icon: LucideIcon;
  description?: string;
};

export const appConfig = {
  name: "Daily Bread AI",
  tagline: "Search the Bible with AI",
};

export const menuItems: MenuItem[] = [
  {
    title: "Chat",
    href: "/",
    icon: MessageSquare,
    description: "Ask questions about Scripture",
  },
  {
    title: "Read",
    href: "/read",
    icon: BookOpen,
    description: "Browse the Bible",
  },
  {
    title: "Bookmarks",
    href: "/bookmarks",
    icon: Bookmark,
    description: "Saved verses and passages",
  },
  {
    title: "Settings",
    href: "/settings",
    icon: Settings,
    description: "Preferences and account",
  },
];
