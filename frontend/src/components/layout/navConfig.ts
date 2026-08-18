import { BookOpenText, GraduationCap, LayoutGrid, Map, Ruler, Compass, Users } from "lucide-react";
import type { LucideIcon } from "lucide-react";

export interface NavItem {
  to: string;
  label: string;
  shortLabel: string;
  icon: LucideIcon;
}

export const NAV_ITEMS: NavItem[] = [
  { to: "/", label: "Global Overview", shortLabel: "Overview", icon: LayoutGrid },
  { to: "/principles", label: "Principle Gap Analysis", shortLabel: "Principles", icon: Ruler },
  { to: "/regional-equity", label: "Regional Equity", shortLabel: "Equity", icon: Compass },
  {
    to: "/best-practices",
    label: "Best Practices Explorer",
    shortLabel: "Practices",
    icon: GraduationCap,
  },
  { to: "/impact-map", label: "Impact Map", shortLabel: "Map", icon: Map },
  { to: "/research", label: "Research", shortLabel: "Research", icon: BookOpenText },
  { to: "/about", label: "About Us", shortLabel: "About", icon: Users },
];
