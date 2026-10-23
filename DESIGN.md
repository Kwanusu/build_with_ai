---
name: Lopper
description: Calm, evidence-first interface for a GitHub tool that finds unused code, unused dev dependencies and lint issues in frontend and backend repos, and removes what a person ticks through a pull request. Stone and lichen surfaces, one ochre action per view, squared-off corners, no shadows except on floating layers.
colors:
  primary: "#36503F"
  accent: "#C2913A"
  accent-hover: "#CFA052"
  on-accent: "#222823"
  logo-accent: "#9C7024"
  background: "#EEF0EA"
  surface: "#F8F9F5"
  surface-inverse: "#1D2420"
  text: "#222823"
  text-secondary: "#545B53"
  border: "#C9CFC3"
  success: "#2F7350"
  warning: "#8A5E0E"
  error: "#A33B35"
  white: "#FFFFFF"
  primary-tint: "#E5E9E3"
  primary-hover: "#EDF0EB"
  success-tint: "#E2EAE2"
  warning-tint: "#ECE7DC"
  error-tint: "#F1E6E1"
  error-hover: "#F5EFEB"
  success-border: "#2F735059"
  warning-border: "#8A5E0E59"
  error-border: "#A33B3559"
  scrim: "#1D242073"
  dark-primary: "#A9C0A6"
  dark-accent: "#D4A653"
  dark-accent-hover: "#E0B66A"
  dark-on-accent: "#1D2420"
  dark-background: "#1D2420"
  dark-surface: "#262F2A"
  dark-text: "#E4E7DF"
  dark-text-secondary: "#A3AA9F"
  dark-border: "#3B4741"
  dark-success: "#7FC29A"
  dark-warning: "#E0B45E"
  dark-error: "#EE968A"
  dark-primary-tint: "#36413A"
  dark-primary-hover: "#2E3832"
  dark-success-tint: "#324138"
  dark-warning-tint: "#3D4032"
  dark-error-tint: "#403D36"
  dark-error-hover: "#333630"
  dark-success-border: "#7FC29A59"
  dark-warning-border: "#E0B45E59"
  dark-error-border: "#EE968A59"
  dark-scrim: "#0000008C"
typography:
  display:
    fontFamily: Red Hat Display
    fontSize: 60px
    fontWeight: 700
    lineHeight: 1
    letterSpacing: -0.025em
  h1:
    fontFamily: Red Hat Display
    fontSize: 48px
    fontWeight: 700
    lineHeight: 1.11
    letterSpacing: -0.025em
  h2:
    fontFamily: Red Hat Display
    fontSize: 36px
    fontWeight: 600
    lineHeight: 1.11
    letterSpacing: -0.025em
  h3:
    fontFamily: Red Hat Display
    fontSize: 20px
    fontWeight: 600
    lineHeight: 1.4
    letterSpacing: 0.025em
  h4:
    fontFamily: Red Hat Display
    fontSize: 18px
    fontWeight: 600
    lineHeight: 1.56
    letterSpacing: 0.025em
  body-lg:
    fontFamily: Red Hat Text
    fontSize: 18px
    fontWeight: 400
    lineHeight: 1.56
    letterSpacing: 0.025em
  body:
    fontFamily: Red Hat Text
    fontSize: 16px
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: 0.025em
  label:
    fontFamily: Red Hat Text
    fontSize: 14px
    fontWeight: 500
    lineHeight: 1.43
    letterSpacing: 0.025em
  button:
    fontFamily: Red Hat Text
    fontSize: 14px
    fontWeight: 500
    lineHeight: 1
    letterSpacing: 0.025em
  small:
    fontFamily: Red Hat Text
    fontSize: 14px
    fontWeight: 400
    lineHeight: 1.43
    letterSpacing: 0.025em
  caption:
    fontFamily: Red Hat Text
    fontSize: 12px
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: 0.025em
  code:
    fontFamily: Red Hat Mono
    fontSize: 14px
    fontWeight: 400
    lineHeight: 1.43
    letterSpacing: 0em
rounded:
  tag: 2px
  control: 6px
  card: 6px
  large: 10px
  pill: 999px
spacing:
  half: 4px
  "1": 8px
  "2": 16px
  "3": 24px
  "4": 32px
  "5": 48px
  "6": 64px
  "7": 128px
  card-padding: 24px
  element-gap: 16px
  section-gap: 64px
  control-height-sm: 32px
  control-height-md: 40px
  control-height-lg: 48px
  topbar-height: 56px
  tabbar-height: 64px
  width-reading: 680px
  width-page: 1200px
components:
  button-primary:
    backgroundColor: "{colors.accent}"
    textColor: "{colors.on-accent}"
    typography: "{typography.button}"
    rounded: "{rounded.control}"
    height: "{spacing.control-height-md}"
    padding: 0 20px
  button-primary-hover:
    backgroundColor: "{colors.accent-hover}"
    textColor: "{colors.on-accent}"
  button-secondary:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.primary}"
    borderColor: "{colors.border}"
    typography: "{typography.button}"
    rounded: "{rounded.control}"
    height: "{spacing.control-height-md}"
    padding: 0 20px
  button-secondary-hover:
    backgroundColor: "{colors.primary-hover}"
    textColor: "{colors.primary}"
    borderColor: "{colors.text-secondary}"
  button-plain:
    textColor: "{colors.primary}"
    typography: "{typography.button}"
    rounded: "{rounded.control}"
    height: "{spacing.control-height-md}"
    padding: 0 20px
  button-danger:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.error}"
    borderColor: "{colors.border}"
    typography: "{typography.button}"
    rounded: "{rounded.control}"
  button-danger-hover:
    backgroundColor: "{colors.error-hover}"
    textColor: "{colors.error}"
    borderColor: "{colors.error}"
  button-sm:
    height: "{spacing.control-height-sm}"
    padding: 0 16px
  button-lg:
    height: "{spacing.control-height-lg}"
    padding: 0 24px
  icon-button:
    textColor: "{colors.text}"
    rounded: "{rounded.control}"
    size: 40px
  input:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text}"
    borderColor: "{colors.border}"
    typography: "{typography.body}"
    rounded: "{rounded.control}"
    height: "{spacing.control-height-md}"
    padding: 0 12px
  input-hover:
    borderColor: "{colors.text-secondary}"
  input-focus:
    borderColor: "{colors.primary}"
  input-error:
    borderColor: "{colors.error}"
  field-label:
    textColor: "{colors.text}"
    typography: "{typography.label}"
  field-helper:
    textColor: "{colors.text-secondary}"
    typography: "{typography.small}"
  field-error-message:
    textColor: "{colors.error}"
    typography: "{typography.small}"
  select:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text}"
    borderColor: "{colors.border}"
    typography: "{typography.body}"
    rounded: "{rounded.control}"
    height: "{spacing.control-height-md}"
    padding: 0 12px
  select-menu:
    backgroundColor: "{colors.surface}"
    borderColor: "{colors.border}"
    rounded: "{rounded.control}"
    padding: 4px
  select-option-selected:
    textColor: "{colors.primary}"
    rounded: "{rounded.tag}"
    padding: 8px 10px
  checkbox:
    backgroundColor: "{colors.surface}"
    borderColor: "{colors.text-secondary}"
    rounded: "{rounded.tag}"
    size: 20px
  checkbox-checked:
    backgroundColor: "{colors.primary}"
    borderColor: "{colors.primary}"
    textColor: "{colors.background}"
  toggle:
    backgroundColor: "{colors.border}"
    rounded: "{rounded.pill}"
    width: 40px
    height: 24px
  toggle-on:
    backgroundColor: "{colors.primary}"
  toggle-thumb:
    backgroundColor: "{colors.surface}"
    size: 18px
  card:
    backgroundColor: "{colors.surface}"
    borderColor: "{colors.border}"
    rounded: "{rounded.card}"
    padding: "{spacing.card-padding}"
  card-hover:
    borderColor: "{colors.text-secondary}"
  card-selected:
    backgroundColor: "{colors.primary-tint}"
    textColor: "{colors.text}"
    borderColor: "{colors.primary}"
  evidence-block:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text}"
    borderColor: "{colors.border}"
    typography: "{typography.code}"
    rounded: "{rounded.card}"
    padding: 16px
  list-row:
    textColor: "{colors.text}"
    borderColor: "{colors.border}"
    typography: "{typography.body}"
    minHeight: 56px
    padding: 16px
  list-row-selected:
    backgroundColor: "{colors.primary-tint}"
    textColor: "{colors.text}"
    edgeColor: "{colors.primary}"
  table-header:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text-secondary}"
    typography: "{typography.label}"
    padding: 12px 16px
  table-cell:
    textColor: "{colors.text}"
    typography: "{typography.small}"
    padding: 12px 16px
  badge:
    rounded: "{rounded.tag}"
    typography: "{typography.label}"
    height: 26px
    padding: 0 8px
  badge-sm:
    typography: "{typography.caption}"
    height: 22px
    padding: 0 6px
  badge-success:
    backgroundColor: "{colors.success-tint}"
    textColor: "{colors.success}"
  badge-warning:
    backgroundColor: "{colors.warning-tint}"
    textColor: "{colors.warning}"
  badge-error:
    backgroundColor: "{colors.error-tint}"
    textColor: "{colors.error}"
  badge-neutral:
    textColor: "{colors.text-secondary}"
    borderColor: "{colors.border}"
  top-bar:
    backgroundColor: "{colors.background}"
    borderColor: "{colors.border}"
    height: "{spacing.topbar-height}"
    padding: 0 24px
  top-bar-mobile:
    height: "{spacing.topbar-height}"
    padding: 0 8px
  top-bar-link:
    textColor: "{colors.text-secondary}"
    typography: "{typography.label}"
  top-bar-link-active:
    textColor: "{colors.primary}"
    underlineColor: "{colors.primary}"
  tab-bar:
    backgroundColor: "{colors.surface}"
    borderColor: "{colors.border}"
    height: "{spacing.tabbar-height}"
  tab-bar-item:
    textColor: "{colors.text-secondary}"
    typography: "{typography.caption}"
  tab-bar-item-active:
    textColor: "{colors.primary}"
  tab-bar-badge:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.background}"
    rounded: "{rounded.pill}"
    size: 18px
  modal:
    backgroundColor: "{colors.surface}"
    borderColor: "{colors.border}"
    rounded: "{rounded.card}"
    padding: 32px
    width: 480px
  modal-sheet:
    rounded: 6px 6px 0 0
    padding: 24px
  toast:
    backgroundColor: "{colors.surface}"
    borderColor: "{colors.border}"
    rounded: "{rounded.card}"
    padding: 16px
    maxWidth: 420px
  empty-state-icon:
    textColor: "{colors.primary}"
    rounded: 50%
    size: 64px
  empty-state-title:
    textColor: "{colors.primary}"
    typography: "{typography.h3}"
  empty-state-message:
    textColor: "{colors.text-secondary}"
    typography: "{typography.body}"
  empty-state-disc:
    backgroundColor: "{colors.primary-tint}"
    textColor: "{colors.primary}"
    rounded: 50%
    size: 64px
  notice-success:
    backgroundColor: "{colors.success-tint}"
    textColor: "{colors.text}"
    borderColor: "{colors.success-border}"
    rounded: "{rounded.card}"
    padding: 16px
  notice-warning:
    backgroundColor: "{colors.warning-tint}"
    textColor: "{colors.text}"
    borderColor: "{colors.warning-border}"
    rounded: "{rounded.card}"
    padding: 16px
  notice-error:
    backgroundColor: "{colors.error-tint}"
    textColor: "{colors.text}"
    borderColor: "{colors.error-border}"
    rounded: "{rounded.card}"
    padding: 16px
  modal-scrim:
    backgroundColor: "{colors.scrim}"
  button-primary-dark:
    backgroundColor: "{colors.dark-accent}"
    textColor: "{colors.dark-on-accent}"
    typography: "{typography.button}"
    rounded: "{rounded.control}"
    height: "{spacing.control-height-md}"
    padding: 0 20px
  button-primary-dark-hover:
    backgroundColor: "{colors.dark-accent-hover}"
    textColor: "{colors.dark-on-accent}"
  button-secondary-dark:
    backgroundColor: "{colors.dark-surface}"
    textColor: "{colors.dark-primary}"
    borderColor: "{colors.dark-border}"
    typography: "{typography.button}"
    rounded: "{rounded.control}"
    height: "{spacing.control-height-md}"
    padding: 0 20px
  button-secondary-dark-hover:
    backgroundColor: "{colors.dark-primary-hover}"
    textColor: "{colors.dark-primary}"
    borderColor: "{colors.dark-text-secondary}"
  button-plain-dark:
    textColor: "{colors.dark-primary}"
    typography: "{typography.button}"
    rounded: "{rounded.control}"
    height: "{spacing.control-height-md}"
    padding: 0 20px
  button-danger-dark:
    backgroundColor: "{colors.dark-surface}"
    textColor: "{colors.dark-error}"
    borderColor: "{colors.dark-border}"
    typography: "{typography.button}"
    rounded: "{rounded.control}"
  button-danger-dark-hover:
    backgroundColor: "{colors.dark-error-hover}"
    textColor: "{colors.dark-error}"
    borderColor: "{colors.dark-error}"
  icon-button-dark:
    textColor: "{colors.dark-text}"
    rounded: "{rounded.control}"
    size: 40px
  input-dark:
    backgroundColor: "{colors.dark-surface}"
    textColor: "{colors.dark-text}"
    borderColor: "{colors.dark-border}"
    typography: "{typography.body}"
    rounded: "{rounded.control}"
    height: "{spacing.control-height-md}"
    padding: 0 12px
  input-dark-hover:
    borderColor: "{colors.dark-text-secondary}"
  input-dark-focus:
    borderColor: "{colors.dark-primary}"
  input-dark-error:
    borderColor: "{colors.dark-error}"
  field-label-dark:
    textColor: "{colors.dark-text}"
    typography: "{typography.label}"
  field-helper-dark:
    textColor: "{colors.dark-text-secondary}"
    typography: "{typography.small}"
  field-error-message-dark:
    textColor: "{colors.dark-error}"
    typography: "{typography.small}"
  select-dark:
    backgroundColor: "{colors.dark-surface}"
    textColor: "{colors.dark-text}"
    borderColor: "{colors.dark-border}"
    typography: "{typography.body}"
    rounded: "{rounded.control}"
    height: "{spacing.control-height-md}"
    padding: 0 12px
  select-menu-dark:
    backgroundColor: "{colors.dark-surface}"
    borderColor: "{colors.dark-border}"
    rounded: "{rounded.control}"
    padding: 4px
  select-option-selected-dark:
    backgroundColor: "{colors.dark-primary-tint}"
    textColor: "{colors.dark-primary}"
    rounded: "{rounded.tag}"
    padding: 8px 10px
  checkbox-dark:
    backgroundColor: "{colors.dark-surface}"
    borderColor: "{colors.dark-text-secondary}"
    rounded: "{rounded.tag}"
    size: 20px
  checkbox-dark-checked:
    backgroundColor: "{colors.dark-primary}"
    borderColor: "{colors.dark-primary}"
    textColor: "{colors.dark-background}"
  toggle-dark:
    backgroundColor: "{colors.dark-border}"
    rounded: "{rounded.pill}"
    width: 40px
    height: 24px
  toggle-dark-on:
    backgroundColor: "{colors.dark-primary}"
  toggle-dark-thumb:
    backgroundColor: "{colors.dark-surface}"
    size: 18px
  card-dark:
    backgroundColor: "{colors.dark-surface}"
    textColor: "{colors.dark-text}"
    borderColor: "{colors.dark-border}"
    rounded: "{rounded.card}"
    padding: "{spacing.card-padding}"
  card-dark-hover:
    borderColor: "{colors.dark-text-secondary}"
  card-dark-selected:
    backgroundColor: "{colors.dark-primary-tint}"
    textColor: "{colors.dark-text}"
    borderColor: "{colors.dark-primary}"
  evidence-block-dark:
    backgroundColor: "{colors.dark-surface}"
    textColor: "{colors.dark-text}"
    borderColor: "{colors.dark-border}"
    typography: "{typography.code}"
    rounded: "{rounded.card}"
    padding: 16px
  list-row-dark:
    textColor: "{colors.dark-text}"
    borderColor: "{colors.dark-border}"
    typography: "{typography.body}"
    minHeight: 56px
    padding: 16px
  list-row-dark-selected:
    backgroundColor: "{colors.dark-primary-tint}"
    textColor: "{colors.dark-text}"
    edgeColor: "{colors.dark-primary}"
  table-header-dark:
    backgroundColor: "{colors.dark-surface}"
    textColor: "{colors.dark-text-secondary}"
    typography: "{typography.label}"
    padding: 12px 16px
  table-cell-dark:
    textColor: "{colors.dark-text}"
    typography: "{typography.small}"
    padding: 12px 16px
  badge-dark-success:
    backgroundColor: "{colors.dark-success-tint}"
    textColor: "{colors.dark-success}"
    rounded: "{rounded.tag}"
    typography: "{typography.label}"
    height: 26px
    padding: 0 8px
  badge-dark-warning:
    backgroundColor: "{colors.dark-warning-tint}"
    textColor: "{colors.dark-warning}"
    rounded: "{rounded.tag}"
    typography: "{typography.label}"
    height: 26px
    padding: 0 8px
  badge-dark-error:
    backgroundColor: "{colors.dark-error-tint}"
    textColor: "{colors.dark-error}"
    rounded: "{rounded.tag}"
    typography: "{typography.label}"
    height: 26px
    padding: 0 8px
  badge-dark-neutral:
    textColor: "{colors.dark-text-secondary}"
    borderColor: "{colors.dark-border}"
    rounded: "{rounded.tag}"
    typography: "{typography.label}"
    height: 26px
    padding: 0 8px
  top-bar-dark:
    backgroundColor: "{colors.dark-background}"
    textColor: "{colors.dark-text}"
    borderColor: "{colors.dark-border}"
    height: "{spacing.topbar-height}"
    padding: 0 24px
  top-bar-dark-link:
    textColor: "{colors.dark-text-secondary}"
    typography: "{typography.label}"
  top-bar-dark-link-active:
    textColor: "{colors.dark-primary}"
    underlineColor: "{colors.dark-primary}"
  tab-bar-dark:
    backgroundColor: "{colors.dark-surface}"
    borderColor: "{colors.dark-border}"
    height: "{spacing.tabbar-height}"
  tab-bar-dark-item:
    textColor: "{colors.dark-text-secondary}"
    typography: "{typography.caption}"
  tab-bar-dark-item-active:
    textColor: "{colors.dark-primary}"
  tab-bar-dark-badge:
    backgroundColor: "{colors.dark-primary}"
    textColor: "{colors.dark-background}"
    rounded: "{rounded.pill}"
    size: 18px
  modal-dark:
    backgroundColor: "{colors.dark-surface}"
    textColor: "{colors.dark-text}"
    borderColor: "{colors.dark-border}"
    rounded: "{rounded.card}"
    padding: 32px
    width: 480px
  modal-dark-scrim:
    backgroundColor: "{colors.dark-scrim}"
  toast-dark:
    backgroundColor: "{colors.dark-surface}"
    textColor: "{colors.dark-text}"
    borderColor: "{colors.dark-border}"
    rounded: "{rounded.card}"
    padding: 16px
    maxWidth: 420px
  empty-state-dark-disc:
    backgroundColor: "{colors.dark-primary-tint}"
    textColor: "{colors.dark-primary}"
    rounded: 50%
    size: 64px
  empty-state-dark-title:
    textColor: "{colors.dark-primary}"
    typography: "{typography.h3}"
  empty-state-dark-message:
    textColor: "{colors.dark-text-secondary}"
    typography: "{typography.body}"
  notice-dark-success:
    backgroundColor: "{colors.dark-success-tint}"
    textColor: "{colors.dark-text}"
    borderColor: "{colors.dark-success-border}"
    rounded: "{rounded.card}"
    padding: 16px
  notice-dark-warning:
    backgroundColor: "{colors.dark-warning-tint}"
    textColor: "{colors.dark-text}"
    borderColor: "{colors.dark-warning-border}"
    rounded: "{rounded.card}"
    padding: 16px
  notice-dark-error:
    backgroundColor: "{colors.dark-error-tint}"
    textColor: "{colors.dark-text}"
    borderColor: "{colors.dark-error-border}"
    rounded: "{rounded.card}"
    padding: 16px
---

## Overview

Lopper is a GitHub tool for engineers who own a repo that nobody dares to prune. It watches chosen branches, scans frontend and backend code (JavaScript, TypeScript, Python, Go) on every push, and finds unused packages, unused exports, unused dev dependencies and lint issues. A person reads the evidence, ticks what to remove, and Lopper opens a pull request. Lint issues are report only.

The brand idea is a lopper: a tool that cuts dead branches carefully and on purpose. The interface should feel like a well-kept garden on a cool, overcast morning: quiet, orderly and spacious. It's trustworthy and calm. It always shows the evidence and never deletes anything without a human approving it.

Voice: an experienced colleague walking the codebase with you. Plain-spoken and specific, with sentence case everywhere. Lopper is "we" and the user is "you". Buttons start with a verb and say what happens ("Connect a GitHub repo", "Rescan", "Create pull request"). Use specific numbers ("Found 14 unused exports across 3 packages"). Errors say what happened, whether code changed, and what to do next. Automatic scans report and people remove: "Push e41c9a2 by @renata · 6 min ago." Lint is labelled "Report only". The word "failed" is kept for a scan that couldn't run.

Tone by moment: onboarding warm and brief; results factual; before a pull request reassuring ("Nothing will be removed until you merge the pull request."); pull request created quiet; push results matter-of-fact ("This pull request leaves 2 unused items and 1 lint issue."); errors honest and steady.

Source files: tokens in `tokens/*.css` (entry `styles.css`), components in `components/`, screens in `ui_kits/`. Logos in `assets/logo/`.

## Colors

The palette is lichen and stone, with one ochre for action.

- **Primary, lichen `#36503F`** ({colors.primary}): brand, headings, links, selection, focus rings, checked controls, active navigation.
- **Accent, ochre `#C2913A`** ({colors.accent}): the fill of the one main action per view. Hover `#CFA052` ({colors.accent-hover}). Text and icons on ochre are always `#222823` ({colors.on-accent}).
- **Logo accent `#9C7024`** ({colors.logo-accent}): reserved for the logo artwork.
- **Background, stone `#EEF0EA`** ({colors.background}): page and top bar.
- **Surface `#F8F9F5`** ({colors.surface}): cards, inputs, menus, modals, toasts, evidence blocks, tab bar.
- **Text `#222823`** ({colors.text}) for body copy; **text secondary `#545B53`** ({colors.text-secondary}) for helper text, metadata, file paths and strong borders.
- **Border `#C9CFC3`** ({colors.border}): every 1px divider and outline.
- **Status:** success `#2F7350` ({colors.success}), warning `#8A5E0E` ({colors.warning}), error `#A33B35` ({colors.error}). Each always comes with an icon or a word.
- **Inverse `#1D2420`** ({colors.surface-inverse}): the base of the modal scrim.
- **White `#FFFFFF`** ({colors.white}).

Semantic roles in code: `--surface-page` = background, `--surface-card` / `--surface-input` / `--surface-evidence` = surface, `--text-heading` and `--text-link` = primary, `--border-default` = border, `--border-strong` = text secondary, `--border-focus` = primary, `--action-primary-bg` = accent, `--text-on-primary` = background.

Tints are mixes of palette colours in `oklab`, never new hues:
- `--color-primary-tint` (selected surfaces, active tab pill, empty-state icon disc): primary 9% into surface.
- `--color-primary-hover` (hover surfaces): primary 5% into surface.
- `--color-success-tint` 11%, `--color-warning-tint` 11%, `--color-error-tint` 10%, each into surface; used for badge and notice fills.
- `--color-scrim`: `#1D2420` at 45% over transparent.

Each tint is also a token, computed from the mixes above: {colors.primary-tint}, {colors.primary-hover}, {colors.success-tint}, {colors.warning-tint}, {colors.error-tint}, {colors.error-hover}, the notice borders ({colors.success-border}, {colors.warning-border}, {colors.error-border}, tone at 35%) and {colors.scrim}. Dark has a matching `dark-` token for each. Every component has a dark twin named with `-dark` (for example `button-primary-dark`, `card-dark-selected`).

**Dark theme** (`[data-theme="dark"]`): primary `#A9C0A6`, accent `#D4A653`, accent hover `#E0B66A`, on-accent `#1D2420`, logo accent `#D4A653`, background `#1D2420`, surface `#262F2A`, text `#E4E7DF`, text secondary `#A3AA9F`, border `#3B4741`, success `#7FC29A`, warning `#E0B45E`, error `#EE968A`. In dark, tints mix 14% (hover 7%), the scrim is black at 55%, and text on primary is `#1D2420`.

## Typography

Three families from the Red Hat superfamily, loaded from Google Fonts:

- **Red Hat Display** (400–700) for headings: display 60px/700, H1 48px/700, H2 36px/600, H3 20px/600, H4 18px/600.
- **Red Hat Text** (400–600) for all UI and body copy: body 16px/1.5, body large 18px/1.56, labels and buttons 14px/500, small text 14px/1.43, captions 12px/1.5.
- **Red Hat Mono** (400) for evidence, file paths, package and export names, commit SHAs and pull request references: 14px/1.43.

Tracking runs two ways: −0.025em at 36px and above, +0.025em on body sizes, normal on mono.

Fallback stacks: `system-ui, -apple-system, "Segoe UI", sans-serif` for Display and Text; `ui-monospace, Menlo, Consolas, monospace` for Mono.

Below 640px wide, display drops to 48px with line height 1.11, and H1 drops to 36px.

Keep reading text within 680px ({spacing.width-reading}). Use `text-wrap: balance` on headings and `text-wrap: pretty` on paragraphs.

## Layout

Spacing is on an 8px base: 4, 8, 16, 24, 32, 48, 64 and 128px ({spacing.half} through {spacing.7}). 4px is the half-step for icon-to-label gaps.

- Card padding: 24px ({spacing.card-padding}).
- Gap between elements: 16px ({spacing.element-gap}).
- Gap between form sections: 32px.
- Gap between page sections: 64px ({spacing.section-gap}).
- Page max width: 1200px ({spacing.width-page}).
- Control heights: 32 / 40 / 48px for sm / md / lg.

Breakpoints used in the screens: mobile under 640px, tablet 640–1099px, desktop 1100px and up. Page padding is 24px × 16px on mobile, 32px on tablet and 40px on desktop.

**Mobile:** a 56px top bar, a 64px bottom tab bar plus the safe area, and a sticky bottom action area that holds the main action (for example "Create pull request"). Hit targets are at least 44px; mobile top-bar icon buttons are 48px.

**Desktop:** a 56px top bar with the wordmark, text navigation and actions. Results pages can add a 320px sticky review panel beside the list.

Lay out groups with flex or grid and `gap`. Group sections with whitespace and 1px dividers.

## Elevation & Depth

The interface is flat. Layers are separated by surface colour and a 1px border, not by shadow.

- **Default:** no shadow (`--shadow-none`).
- **Floating layers only** (modal, toast, select menu): `--shadow-overlay`, which is `0 1px 2px rgba(34,40,35,.06), 0 12px 32px -8px rgba(34,40,35,.18)`. In dark it is `0 1px 2px rgba(0,0,0,.3), 0 12px 32px -8px rgba(0,0,0,.5)`.
- **Primary button pressed:** a faint inset, `inset 0 1px 2px rgba(34,40,35,.18)`.
- **Toggle thumb:** `0 1px 2px rgba(34,40,35,.2)`.
- **Selected card:** the 1px primary border is doubled with `inset 0 0 0 1px` primary.
- **Modal scrim:** {colors.surface-inverse} at 45%, with no blur.

Motion: 200ms (`--motion-fast`) for colour and border changes, 300ms (`--motion-slow`) for overlays, both with `cubic-bezier(.22,.61,.36,1)`. Overlays fade and rise 8px (`lp-rise`). Menus and expanded evidence fade (`lp-fade`). Spinners rotate at 900ms linear. Under `prefers-reduced-motion`, durations collapse to 0.01ms.

## Shapes

Corners are small and squared-off.

- **2px** ({rounded.tag}): tags, badges, checkboxes, select options.
- **6px** ({rounded.control}, {rounded.card}): buttons, inputs, selects, cards, tables, list containers, modals, toasts. A mobile sheet rounds only its top corners (6px 6px 0 0).
- **10px** ({rounded.large}): rare cases only.
- **22%** of the tile width: the app icon tile.
- **999px** ({rounded.pill}): only the toggle track, its thumb and the tab-bar count bubble. Empty-state icon discs are circles.

Borders are 1px solid {colors.border}. Checkbox borders are 1.5px. The focus ring is a 2px solid {colors.primary} outline with a 2px offset (inset −2px on list rows).

Icons are Lucide outline icons (`lucide-static@0.460.0`) at 16, 20 or 24px, re-stroked to 1.5px. They inherit `currentColor` by default; status icons take their status colour. Lucide was substituted because no icon set was supplied.

Logo: use the files in `assets/logo/` as supplied.
- `lopper-wordmark-light.svg` and `-dark.svg` are the primary wordmark. Minimum width 120px; 30px tall in the top bar.
- `lopper-wordmark-pruned-p-light.svg` is a supplied alternate. No dark version exists.
- `lopper-app-icon.svg` is for favicons, avatars and anything 32px or smaller. Minimum 16px.
- Clear space is the height of the lowercase "o" for the wordmark, and ⅛ of the width for the app icon.

## Components

All components read the tokens above. States shared across interactive components:
- **Hover:** a faint primary tint (`--surface-hover`) on secondary and plain surfaces; borders darken to {colors.text-secondary}.
- **Pressed:** a deeper tint (`--surface-selected`).
- **Focus:** the 2px {colors.primary} ring.
- **Disabled:** 45% opacity and a `not-allowed` cursor. Whole fields dim to 55%.

### Buttons
- **Primary** (`button-primary`): fill {colors.accent}, text {colors.on-accent}, label {typography.button}, radius {rounded.control}. Hover is {colors.accent-hover}. Pressed keeps the hover fill and adds the faint inset. Use one per view, for the main action.
- **Secondary** (`button-secondary`): fill {colors.surface}, text {colors.primary}, 1px {colors.border} border. Hover gives a primary-hover surface and a {colors.text-secondary} border; pressed gives a primary-tint surface.
- **Plain** (`button-plain`): transparent, text {colors.primary}. Hover and pressed tint the surface the same way as secondary.
- **Danger** (`button-danger`): surface fill, text {colors.error}. Hover gives a 5% error mix and an {colors.error} border; pressed gives the error tint.
- **Sizes:** sm 32px tall with 0 16px padding and a 6px icon gap; md 40px with 0 20px and an 8px gap; lg 48px with 0 24px and an 8px gap. Icons are 16px in sm and 20px in md and lg.
- **Loading:** the button disables itself, sets `aria-busy`, shows a spinner and its label changes to the action in progress ("Creating pull request", "Waiting for GitHub").
- **Disabled:** 45% opacity.
- **Full width** on mobile action bars.
- **Icon button:** 32, 40 or 48px square, radius {rounded.control}, plain or secondary, with the same hover, pressed and focus states. It always has an `aria-label`.

### Inputs
- **Text input** (`input`): 40px minimum height, padding 0 12px, fill {colors.surface}, 1px {colors.border} border, radius {rounded.control}, text {typography.body}. An optional 20px leading icon sits in {colors.text-secondary}. A mono variant uses {typography.code}.
  - Hover: border {colors.text-secondary}.
  - Focus: border {colors.primary} plus the 2px ring.
  - Error: border {colors.error}, a ring in {colors.error} when focused, and a message below in {colors.error} with a 16px `circle-alert` icon.
  - Read-only: transparent fill.
  - Disabled: field at 55%.
  - Multiline: padding 10px 12px, resizes vertically.
- **Field shell:** the label uses {typography.label} in {colors.text}. "Optional" appears beside it in {colors.text-secondary} at 400 weight. Helper or error text uses {typography.small}. Gap is 6px.
- **Select:** same chrome as the text input, with a 20px chevron in {colors.text-secondary} that rotates 180° when open. The placeholder is in {colors.text-secondary}.
  - Menu (`select-menu`): sits 4px below the field, padding 4px, {rounded.control}, the overlay shadow, max height 260px, and fades in.
  - Options: padding 8px 10px with {rounded.tag}. Hover gives the hover tint; the selected option gets the primary tint, {colors.primary} text and a 16px check.
  - Arrow keys move the highlight, Enter or Space picks, Escape closes.
- **Checkbox:** 20px, {rounded.tag}, 1.5px {colors.text-secondary} border on {colors.surface}. Hover turns the border {colors.primary}. Checked or indeterminate fills {colors.primary} with a 16px check or minus in {colors.background}.
- **Toggle:** a 40 × 24px track. Off is {colors.border}; on is {colors.primary}. There's an 18px {colors.surface} thumb that slides in 200ms. Labels sit 12px to the right with an optional {typography.small} description.
- **Form layout:** max width 480px, 32px between header, fields and actions; 24px between fields; 16px inside a section; two-column sections collapse under 520px.

### Cards
- **Card** (`card`): fill {colors.surface}, 1px {colors.border}, {rounded.card}, 24px padding, no shadow, 16px internal gap.
  - Optional parts: a mono caption eyebrow, a title in {typography.h4}, and a description in {typography.small} {colors.text-secondary}. A footer sits above a 1px divider.
  - Interactive cards: hover gives the hover tint and a {colors.text-secondary} border, and they show the focus ring.
  - Selected: primary-tint fill with a doubled {colors.primary} border.
- **Evidence block:** fill {colors.surface}, 1px border, {rounded.card}, 16px padding, {typography.code}. The title is {typography.label} in {colors.text-secondary}. Each line is a statement with its file path below in {colors.text-secondary}. Every finding shows one.
- **List row:** 56px minimum height, 16px padding, a 1px bottom divider, an optional 20px leading icon in {colors.text-secondary}, the title in {typography.body} (or mono), and the subtitle in {typography.small}.
  - Hover and pressed use the tints.
  - Selected: primary tint plus a 2px {colors.primary} edge on the left side.
  - Disabled: 45%.
  - Clickable rows respond to Enter and Space.
- **Table:** 1px border, {rounded.card}, surface fill. Headers use {typography.label} in {colors.text-secondary}; cells use {typography.small}; padding is 12px 16px (8px 12px when dense). Row hover gives the hover tint and selected rows the primary tint. A header checkbox selects all and shows an indeterminate state. The empty row is centred in {colors.text-secondary} with 32px vertical padding.
- **Badge:** {rounded.tag}, 1px border, tint fill, with a 16px icon (14px in sm). Status badges carry their icon by default: `circle-check`, `triangle-alert`, `circle-x`. md is 26px with 0 8px padding; sm is 22px with 0 6px padding. Tones are neutral, primary, success, warning and error.

### Navigation
- **Top bar** (`top-bar`): 56px tall, fill {colors.background}, 1px bottom border, padding 0 24px on desktop and 0 8px on mobile. It can stick to the top.
  - Desktop: the wordmark at 30px tall, then nav links 24px apart. Links use {typography.label} in {colors.text-secondary}. Hover and active links are {colors.primary}, and the active link gets a 2px {colors.primary} underline and `aria-current="page"`. Actions sit at the right with an 8px gap.
  - Mobile page variant: a 48px back button, a centred title in {typography.body} at 500 weight, and right-hand actions.
- **Bottom tab bar** (`tab-bar`): 64px tall plus the safe-area inset, fill {colors.surface}, 1px top border.
  - Items: a 24px icon above a {typography.caption} label in {colors.text-secondary}.
  - Active: {colors.primary} text at 500 weight, with the icon on a 56 × 28px primary-tint pill.
  - Pressed: 70% opacity.
  - Count bubbles are 18px pills in {colors.primary} with mono 11px {colors.background} text.

### Overlays and feedback
- **Modal:** fill {colors.surface}, 1px border, {rounded.card}, overlay shadow, 32px padding, 480px wide.
  - Title in {typography.h3} {colors.primary}, description in {typography.body} {colors.text-secondary}.
  - Enters with an 8px rise in 300ms; Escape closes it.
  - Actions sit in a row, with the primary action rightmost.
- **Sheet** (the mobile modal): full width, top corners only, 24px padding plus the safe area, a 36 × 4px grab handle, and actions stacked full width with the primary action on top.
- **Toast:** surface fill, 1px border, {rounded.card}, overlay shadow, 16px padding, max width 420px. It has a 20px tone icon (info in primary, success, warning, error), a title at 500 weight, a message in {typography.small}, an optional action and a 32px dismiss button. Errors use `role="alert"`; the rest use `role="status"`.
- **Notice** (inline): tone-tint fill, a border in the tone colour at 35% into transparent, {rounded.card}, 16px padding and a 20px tone icon.

### Screen states
Every screen designs all four states.

- **Empty:** a centred empty state with a 64px circular {colors.primary}-tint disc holding a 24px {colors.primary} icon (48px disc and 20px icon in the small size). Below it, the title in {typography.h3} {colors.primary} (H4 in the small size) and the message in {typography.body} {colors.text-secondary}, max width 400px, then actions. Padding is 64px × 24px (32px × 16px small). Say why it's empty and what to do next, with numbers: "We searched 4,486 files across 44 packages and found no unused packages or exports." The default icon is `sprout`; use `leaf` when there's nothing to prune.
- **Loading:**
  - Lists use skeleton rows: blocks in {colors.border} with a surface shimmer over 1.4s, set out like real rows.
  - Long jobs (a scan, creating a pull request) use a steps list. Done steps get a {colors.success} check; the current step gets a 14px {colors.primary} spinner, monospace detail and an optional 4px progress bar on a primary-tint track; pending steps sit at 60% opacity. Each step says what is being read, and the header says the code isn't changed.
  - Buttons show their in-progress label.
- **Error:** an empty-state panel with a `triangle-alert` or relevant icon. It says what happened, whether code changed ("Your code hasn't been changed.") and what to do, with a primary retry action and a plain secondary action. Evidence of the cause goes in an evidence block below. Field errors appear inline, in {colors.error}, under the field. Sign-in failures appear as an error notice above the sign-in button. No apologies.
- **Success:** the content itself. On completion screens (for example "Pull request created"), show a 48px circle with a {colors.success} icon on the success tint, the result in {typography.h2}, a quiet one-line summary, and a link to the next step ("Open pull request on GitHub"). Confirmations that don't change the page use a success toast.

## Do's and Don'ts

**Do**
- Use {colors.accent} for exactly one main action per view.
- Use {colors.primary} for brand, headings, links, selection, focus and active navigation.
- Show an evidence block for every finding, and leave uncertain findings unticked with a warning badge.
- Pair every status colour with an icon or a word.
- Give every interactive element the 2px {colors.primary} focus ring with a 2px offset.
- Use Red Hat Mono for paths, package and export names, SHAs and pull request references.
- Use the token values exactly as written. Use 6px corners for controls and cards, and 2px for tags, badges and checkboxes.
- Design the empty, loading, error and success states for every screen.
- Write in sentence case, use contractions and active voice, start buttons with a verb, and use specific numbers.
- Say before every pull request that nothing is removed until someone merges it.
- Keep mobile hit targets at 44px or larger, and keep the main mobile action in the sticky bottom area.
- Respect `prefers-reduced-motion`.

**Don't**
- Don't use ochre ({colors.accent}) for text or thin icons on light backgrounds, and don't put light text on ochre.
- Don't swap the roles of lichen and ochre.
- Don't invent new hues. Tints are mixes of palette colours only.
- Don't use gradients, textures, patterns, full-bleed photography, backdrop blur or decorative animation.
- Don't add shadows to cards, buttons or inputs. Shadows are only for modals, toasts and select menus.
- Don't use pill-shaped buttons or large corner radii. Pills are only for the toggle and tab-bar count bubbles.
- Don't make a border the only carrier of meaning.
- Don't scale or shrink elements on press, and don't use bounce easing.
- Don't use uppercase labels or all caps.
- Don't use emoji, icon fonts or PNG icons. Unicode symbols are only typographic separators (`·`, `→`).
- Don't redraw, recolour, retype or restyle the logo. Don't place it on busy backgrounds, and don't use it below its minimum size.
- Don't use exclamation marks, apologies, or "simply", "just", "easy", "nuke", "magic", "guaranteed", "bloat" or "blazing".
- Don't write "Submit" or "OK" on buttons, and don't rename an action partway through a flow.
- Don't call lint issues errors or violations, and don't use "failed" for findings.
- Don't imply Lopper removed or changed code on its own. Automatic scans report; people remove.
- Don't delete anything without a pull request a person merges, and don't block merges or fail builds.
- Don't show placeholder text. Use realistic repo content.
