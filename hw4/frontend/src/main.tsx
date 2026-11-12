import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import { AuthProvider } from "./auth";
import { ChatResultsProvider } from "./chatResults";
import { ToastProvider } from "./toast";
import "./styles.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <ToastProvider>
      <AuthProvider>
        <ChatResultsProvider>
          <App />
        </ChatResultsProvider>
      </AuthProvider>
      </ToastProvider>
    </BrowserRouter>
  </StrictMode>,
);
