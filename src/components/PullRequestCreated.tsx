import type { PullRequestResult } from "../api";
import { PULL_REQUEST } from "../content";
import { Frame } from "./Connect";
import { CircleCheckIcon } from "./ui";

interface PullRequestCreatedProps {
  result: PullRequestResult;
  repo: string;
  onBack: () => void;
}

export function PullRequestCreated({ result, repo, onBack }: PullRequestCreatedProps) {
  const { pull_request: pull, applied, skipped } = result;
  const touchesPackageJson = applied.some((change) => change.file_path.endsWith("package.json"));
  return (
    <Frame>
      <div className="flex flex-col items-start gap-2 reading">
        <span className="disc disc-success">
          <CircleCheckIcon />
        </span>
        <h1 className="type-h2">{PULL_REQUEST.title}</h1>
        <p className="type-body-lg c-muted">{PULL_REQUEST.summary(applied.length, repo)}</p>
        <p className="type-code c-muted wrap-break-word">
          #{pull.number} · {pull.branch}
        </p>
        <div className="flex flex-wrap gap-2">
          <a className="btn btn-primary btn-lg" href={pull.url} target="_blank" rel="noopener noreferrer">
            {PULL_REQUEST.open}
          </a>
          <button type="button" className="btn btn-secondary btn-lg" onClick={onBack}>
            {PULL_REQUEST.back}
          </button>
        </div>
      </div>

      <section className="reading flex flex-col gap-2" aria-labelledby="pr-changes">
        <h2 id="pr-changes" className="type-h3">
          {PULL_REQUEST.changesTitle}
        </h2>
        <ul className="flex flex-col gap-1 list-none p-0 m-0">
          {applied.map((change) => (
            <li key={change.id} className="evidence">
              <p className="type-code wrap-break-word">{change.summary}</p>
              <p className="type-code c-muted wrap-break-word">{change.file_path}</p>
            </li>
          ))}
        </ul>
        {touchesPackageJson && <p className="type-small c-muted">{PULL_REQUEST.lockfiles}</p>}
      </section>

      {skipped.length > 0 && (
        <section className="reading flex flex-col gap-2" aria-labelledby="pr-left">
          <h2 id="pr-left" className="type-h3">
            {PULL_REQUEST.leftTitle}
          </h2>
          <p className="type-small c-muted">{PULL_REQUEST.leftIntro}</p>
          <ul className="flex flex-col gap-1 list-none p-0 m-0">
            {skipped.map((change) => (
              <li key={change.id} className="evidence">
                <p className="type-code wrap-break-word">{change.item}</p>
                <p className="type-small c-muted">{change.reason}</p>
              </li>
            ))}
          </ul>
        </section>
      )}
    </Frame>
  );
}
