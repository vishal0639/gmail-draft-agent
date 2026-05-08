import type { Tab } from "@/store/slices/uiSlice";

export const nav: { id: Tab; label: string }[] = [
  { id: "overview", label: "Overview" },
  { id: "inbox", label: "Inbox" },
  { id: "drafts", label: "Drafts" },
  // { id: "settings", label: "Settings" },
];
