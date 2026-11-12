import { Fragment } from "react";
import { Link } from "react-router-dom";

// Turns the assistant's plain text into safe React elements:
// [text](/path) links to a page on this site, **bold** becomes <strong>, `/path` or a bare /path on this site becomes a link,
// and other `code` is shown as plain text. No raw HTML is ever injected.
const TOKEN = /(\[[^\]]+\]\([^)\s]+\)|\*\*[^*]+\*\*|`[^`]+`|(?<![\w.])\/(?:products|about|login|signup)(?:\/[\w-]+)?(?:\?[\w=&%+-]+)?)/g;

function isSitePath(text: string) {
  return /^\/(products|about|login|signup)\b/.test(text);
}

export default function ChatText({ text, onNavigate }: { text: string; onNavigate?: () => void }) {
  const parts = text.split(TOKEN);
  return (
    <>
      {parts.map((part, i) => {
        if (!part) return null;
        const md = part.match(/^\[([^\]]+)\]\(([^)\s]+)\)$/);
        if (md) {
          // Markdown link: keep it only if it points to a page on this site.
          const path = md[2].replace(/^https?:\/\/[^/]+/, "");
          return isSitePath(path) ? (
            <Link key={i} to={path} className="chat-link" onClick={onNavigate}>
              {md[1].replace(/^https?:\/\/[^/]+/, "").replace(/^[\w.-]+\.(com|edu|org)/, "") || path}
            </Link>
          ) : (
            <Fragment key={i}>{md[1]}</Fragment>
          );
        }
        if (part.startsWith("**") && part.endsWith("**")) return <strong key={i}>{part.slice(2, -2)}</strong>;
        const inner = part.startsWith("`") && part.endsWith("`") ? part.slice(1, -1) : part;
        if (isSitePath(inner)) {
          return (
            <Link key={i} to={inner} className="chat-link" onClick={onNavigate}>
              {inner}
            </Link>
          );
        }
        return <Fragment key={i}>{inner}</Fragment>;
      })}
    </>
  );
}
