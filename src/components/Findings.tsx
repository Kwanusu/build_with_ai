import { SCAN } from "../content";
import type { Finding, FindingType, Scan } from "../api";
import { Badge, CheckIcon, CircleCheckIcon, TriangleAlertIcon } from "./ui";

interface FindingsProps {
  scan: Scan;
  onTick: (finding: Finding, ticked: boolean) => void;
}

/** The file on GitHub, scrolled to the line. `HEAD` is the repo's default branch. */
function githubUrl(repoUrl: string, finding: Finding): string {
  const path = finding.file_path.split("/").map(encodeURIComponent).join("/");
  return `${repoUrl}/blob/HEAD/${path}${finding.line ? `#L${finding.line}` : ""}`;
}

function FindingRow({
  finding,
  repoUrl,
  canTick,
  onTick,
}: {
  finding: Finding;
  repoUrl: string;
  canTick: boolean;
  onTick: FindingsProps["onTick"];
}) {
  const location = finding.line ? `${finding.file_path}:${finding.line}` : finding.file_path;
  const uncertain = finding.confidence === "uncertain";
  return (
    <li className="evidence flex gap-2">
      {finding.report_only || !canTick ? (
        // Lint issues are report only, and items on a scan you don't own can't be ticked.
        <span className="w-5 flex-none" aria-hidden="true" />
      ) : (
        <label className="checkbox">
          <input
            type="checkbox"
            checked={finding.ticked}
            onChange={(event) => onTick(finding, event.target.checked)}
            aria-label={`Tick ${finding.item} to remove it`}
          />
          <span className="check" aria-hidden="true">
            <CheckIcon />
          </span>
        </label>
      )}
      <div className="flex flex-col gap-1 min-w-0">
        <p className="type-code font-medium wrap-break-word">{finding.item}</p>
        <p className="type-code wrap-break-word">
          <a
            className="code-link"
            href={githubUrl(repoUrl, finding)}
            target="_blank"
            rel="noopener noreferrer"
            title={SCAN.results.openOnGithub}
          >
            {location}
          </a>
        </p>
        <p className="type-small c-muted">{finding.evidence}</p>
        {!finding.report_only && (
          <Badge
            tone={uncertain ? "warning" : "success"}
            className="self-start"
            icon={uncertain ? <TriangleAlertIcon /> : <CircleCheckIcon />}
          >
            {uncertain ? SCAN.badges.uncertain : SCAN.badges.safe}
          </Badge>
        )}
      </div>
    </li>
  );
}

export function Findings({ scan, onTick }: FindingsProps) {
  const byType = (type: FindingType) => scan.findings.filter((finding) => finding.type === type);
  return (
    <div className="flex flex-col gap-4">
      {SCAN.groups.map((group) => {
        const rows = byType(group.type);
        if (rows.length === 0) {
          return null;
        }
        return (
          <section key={group.type} aria-labelledby={`group-${group.type}`} className="flex flex-col gap-2">
            <div className="flex flex-wrap items-center gap-1">
              <h2 id={`group-${group.type}`} className="type-h3">
                {group.title}
              </h2>
              {"badge" in group && <Badge tone="neutral">{group.badge}</Badge>}
              <span className="type-small c-muted">{rows.length}</span>
            </div>
            <ul className="flex flex-col gap-2 list-none p-0 m-0">
              {rows.map((finding) => (
                <FindingRow key={finding.id} finding={finding} repoUrl={scan.repo.url} canTick={scan.can_tick} onTick={onTick} />
              ))}
            </ul>
          </section>
        );
      })}
    </div>
  );
}
