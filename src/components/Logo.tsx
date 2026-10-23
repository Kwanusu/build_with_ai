import wordmarkLight from "../../assets/logo/lopper-wordmark-light.svg";
import wordmarkDark from "../../assets/logo/lopper-wordmark-dark.svg";
import lockupLight from "../../assets/logo/lopper-lockup-light.svg";
import lockupDark from "../../assets/logo/lopper-lockup-dark.svg";

type LogoVariant = "wordmark" | "lockup";

const SOURCES: Record<LogoVariant, { light: string; dark: string }> = {
  wordmark: { light: wordmarkLight, dark: wordmarkDark },
  lockup: { light: lockupLight, dark: lockupDark },
};

interface LogoProps {
  variant: LogoVariant;
  className?: string;
}

/**
 * The supplied logo files, used as they are. Both colour versions are rendered and
 * the stylesheet shows the one that matches the theme (see .logo-light and .logo-dark).
 */
export function Logo({ variant, className = "" }: LogoProps) {
  const { light, dark } = SOURCES[variant];
  return (
    <span className={`logo logo-${variant} ${className}`.trim()}>
      <img className="logo-light" src={light} alt="Lopper" />
      <img className="logo-dark" src={dark} alt="" aria-hidden="true" />
    </span>
  );
}
