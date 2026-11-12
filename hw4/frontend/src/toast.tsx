import { createContext, useCallback, useContext, useRef, useState, type ReactNode } from "react";

type Tone = "info" | "success" | "error";
interface Toast {
  id: number;
  message: string;
  tone: Tone;
  action?: { label: string; onClick: () => void };
}
type ShowToast = (message: string, tone?: Tone, action?: Toast["action"]) => void;

const ToastCtx = createContext<ShowToast>(() => {});

/** Small pop-up notifications ("You're logged out", "Couldn't load products", …). */
export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const nextId = useRef(1);

  const dismiss = (id: number) => setToasts((t) => t.filter((x) => x.id !== id));

  const show = useCallback<ShowToast>((message, tone = "info", action) => {
    const id = nextId.current++;
    setToasts((t) => [...t.slice(-2), { id, message, tone, action }]);
    window.setTimeout(() => dismiss(id), tone === "error" ? 7000 : 4500);
  }, []);

  return (
    <ToastCtx.Provider value={show}>
      {children}
      <div className="toasts" role="region" aria-label="Notifications">
        {toasts.map((t) => (
          <div key={t.id} className={`toast toast-${t.tone}`} role={t.tone === "error" ? "alert" : "status"}>
            <span>{t.message}</span>
            {t.action && (
              <button
                className="toast-action"
                onClick={() => {
                  t.action!.onClick();
                  dismiss(t.id);
                }}
              >
                {t.action.label}
              </button>
            )}
            <button className="toast-close" aria-label="Dismiss notification" onClick={() => dismiss(t.id)}>
              ✕
            </button>
          </div>
        ))}
      </div>
    </ToastCtx.Provider>
  );
}

export const useToast = () => useContext(ToastCtx);
