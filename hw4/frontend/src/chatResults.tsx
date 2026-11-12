import { createContext, useContext, useState, type ReactNode } from "react";
import type { ChatSearchResults } from "./types";

interface ChatResultsState {
  results: ChatSearchResults | null;
  open: boolean;
  setResults: (r: ChatSearchResults | null) => void;
  setOpen: (open: boolean) => void;
}

const Ctx = createContext<ChatResultsState | null>(null);

/** Holds the products the chatbot most recently found, so any page can show them. */
export function ChatResultsProvider({ children }: { children: ReactNode }) {
  const [results, setResultsState] = useState<ChatSearchResults | null>(null);
  const [open, setOpen] = useState(false);
  const setResults = (r: ChatSearchResults | null) => {
    setResultsState(r);
    setOpen(Boolean(r));
  };
  return <Ctx.Provider value={{ results, open, setResults, setOpen }}>{children}</Ctx.Provider>;
}

export function useChatResults() {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useChatResults must be used inside ChatResultsProvider");
  return ctx;
}
