import {
  BookOpenText,
  GraduationCap,
  HeartHandshake,
  LayoutGrid,
  Ruler,
  Compass,
  Users,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

export interface NavItem {
  to: string;
  label: string;
  shortLabel: string;
  icon: LucideIcon;
}

export const NAV_ITEMS: NavItem[] = [
  { to: "/", label: "Global Overview", shortLabel: "Overview", icon: LayoutGrid },
  {
    to: "/principles",
    label: "Principle Implementation Analysis",
    shortLabel: "Principles",
    icon: Ruler,
  },
  {
    to: "/regional-equity",
    label: "Regional Distribution",
    shortLabel: "Distribution",
    icon: Compass,
  },
  {
    to: "/best-practices",
    label: "Best Practices Explorer",
    shortLabel: "Practices",
    icon: GraduationCap,
  },
  { to: "/research", label: "Research", shortLabel: "Research", icon: BookOpenText },
  {
    to: "/research/social-isolation",
    label: "Social Isolation Research",
    shortLabel: "Isolation",
    icon: HeartHandshake,
  },
  { to: "/about", label: "Our Story", shortLabel: "Story", icon: Users },
];
