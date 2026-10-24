import { THEME } from "../content";
import { useTheme, type ThemePreference } from "../theme";
import { IconButton, MonitorIcon, MoonIcon, SunIcon } from "./ui";

const ICONS: Record<ThemePreference, () => React.JSX.Element> = { system: MonitorIcon, light: SunIcon, dark: MoonIcon };

/** One button that steps through match your device, light and dark. Any number can be on the page: they share the choice. */
export function ThemeToggle({ size = "md", className }: { size?: "sm" | "md" | "lg"; className?: string }) {
  const { preference, next, cycle } = useTheme();
  const Icon = ICONS[preference];
  return (
    <IconButton label={THEME.label(THEME.names[preference], THEME.names[next])} onClick={cycle} size={size} className={className}>
      <Icon />
    </IconButton>
  );
}
