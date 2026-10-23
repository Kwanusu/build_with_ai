import { EXAMPLE, type ExampleFinding } from "../content";
import { Badge, CheckIcon, CircleCheckIcon, TriangleAlertIcon } from "./ui";

function Finding({ finding }: { finding: ExampleFinding }) {
  return (
    <li className="evidence flex gap-2">
      <span
        className={`check ${finding.ticked ? "check-on" : ""}`.trim()}
        role="img"
        aria-label={finding.ticked ? "Ticked" : "Not ticked"}
      >
        {finding.ticked && <CheckIcon />}
      </span>
      <div className="flex flex-col gap-1 min-w-0">
        <p className="type-code wrap-break-word">
          <span className="font-medium">{finding.name}</span> {finding.statement}
        </p>
        <p className="type-code c-muted wrap-break-word">{finding.path}</p>
        <p className="type-small c-muted">{finding.detail}</p>
        <Badge
          tone={finding.tone}
          className="self-start"
          icon={finding.tone === "success" ? <CircleCheckIcon /> : <TriangleAlertIcon />}
        >
          {finding.badge}
        </Badge>
      </div>
    </li>
  );
}

export function ExampleResults() {
  return (
    <div className="card flex flex-col gap-2" role="group" aria-label="Example results screen">
      <div className="flex flex-col gap-half">
        <p className="type-code c-muted">{EXAMPLE.caption}</p>
        <h2 className="type-h4">{EXAMPLE.title}</h2>
      </div>
      <ul className="flex flex-col gap-2 list-none p-0 m-0">
        {EXAMPLE.findings.map((finding) => (
          <Finding key={finding.name} finding={finding} />
        ))}
      </ul>
      <p className="type-small c-muted">{EXAMPLE.summary}</p>
    </div>
  );
}
