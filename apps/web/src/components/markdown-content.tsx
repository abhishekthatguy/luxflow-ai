import type { ReactNode } from "react";

function renderInline(text: string): ReactNode[] {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return (
        <strong key={i} className="font-semibold text-slate-900">
          {part.slice(2, -2)}
        </strong>
      );
    }
    return part;
  });
}

export function MarkdownContent({ content }: { content: string }) {
  const blocks = content.split(/\n(?=## )/);

  return (
    <article className="prose-sm max-w-none space-y-4 text-sm text-slate-700">
      {blocks.map((block, blockIdx) => {
        const lines = block.trim().split("\n");
        if (!lines[0]) return null;

        if (lines[0].startsWith("## ")) {
          const heading = lines[0].slice(3).trim();
          const body = lines.slice(1).join("\n").trim();
          return (
            <section key={blockIdx} className="rounded-lg border border-slate-200 bg-slate-50/80 p-4">
              <h3 className="text-base font-semibold text-slate-900">{heading}</h3>
              {body && (
                <div className="mt-2 space-y-2 whitespace-pre-wrap leading-relaxed">
                  {body.split("\n").map((line, lineIdx) => {
                    if (line.trim() === "---") {
                      return <hr key={lineIdx} className="border-slate-200" />;
                    }
                    if (!line.trim()) return <div key={lineIdx} className="h-1" />;
                    return <p key={lineIdx}>{renderInline(line)}</p>;
                  })}
                </div>
              )}
            </section>
          );
        }

        return (
          <div key={blockIdx} className="space-y-2 whitespace-pre-wrap leading-relaxed">
            {lines.map((line, lineIdx) => (
              <p key={lineIdx}>{renderInline(line)}</p>
            ))}
          </div>
        );
      })}
    </article>
  );
}
