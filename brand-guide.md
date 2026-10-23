# Lopper brand guide

Version 1.0. Brand direction: **The Groundskeeper**. Palette: **Lichen and stone**. Typefaces: **Young Serif** and **IBM Plex Sans**.

This guide is the single source of truth for Lopper's brand and design system. Every value below is final unless marked "recommended starting value", which means it was derived to complete the system and can be tuned.

---

## 1. Brand concept

### Product

Lopper finds unused packages and exports in a JavaScript or TypeScript monorepo, with no setup, and removes them through a GitHub pull request a human reviews and merges.

### Mission

Help engineering teams remove dead code with confidence, so a monorepo can grow without everyone being afraid to touch it.

### Primary audience

A senior engineer at a startup of roughly 20 to 100 people who owns a JavaScript or TypeScript monorepo. They're experienced, careful, and a little tired. They know there's dead code in the repo, but one wrong deletion can break production and cost them credibility with the team. They've tried tools like Knip, lost an afternoon to configuration, and gone back to leaving things alone. They don't need excitement. They need to feel safe.

### Positioning against competitors

Knip, depcheck, and ts-prune are powerful, but they ask a lot. You configure them, read their output in a terminal, decide what to trust, and do the deletion yourself.

Lopper needs no setup, shows the evidence behind every finding, and never deletes anything directly. Every change arrives as a pull request a human reviews and merges.

**Positioning statement:** For engineers who know their monorepo has dead code but are afraid to cut it, Lopper is the dead-code tool that shows its reasoning and hands you a pull request, so pruning feels careful instead of risky.

### Name metaphor

A lopper is a garden tool that cuts dead branches carefully and on purpose. Think deliberate pruning, not a chainsaw.

### Brand pillars

1. **Evidence before every cut.** Lopper never asks to be trusted blindly. Each finding shows why it was flagged: where the code is defined, where it was searched for, and why nothing uses it. If we can't show the evidence, we don't make the claim.
2. **Ready the moment you arrive.** Sign in with GitHub, pick a repo, and the scan begins. No config files, no plugins, no setup guide.
3. **A human hand on the shears.** Lopper suggests and the user decides. Nothing leaves the codebase without a pull request a person has read and approved.

### Visual feel

Lopper looks like a well-kept garden on a cool, overcast morning: quiet, orderly, and clearly tended by someone who knows what they're doing. The base is a pale grey-green stone, like lichen on a garden wall, with deep lichen green for the brand and headings. A single warm ochre accent marks the moments that matter, such as the "Create pull request" button and the offcut in the logo. Headlines are set in Young Serif, which has the crafted feel of an old seed-catalog label. Interface text is IBM Plex Sans, and evidence, file paths, and code are set in IBM Plex Mono, so proof always looks like proof. Layouts are spacious and unhurried, with generous white space and nothing competing for attention. Illustration, where used, is fine line drawing of branches, leaves, and a single clean cut, closer to a botanical field guide than a tech startup. Motion is slow and gentle. The overall impression: someone patient and skilled is looking after the codebase, and they won't cut anything without showing you first.

---

## 2. Typography

### Typefaces and roles

| Typeface | Source | Weights used | Role |
|---|---|---|---|
| **Young Serif** | Google Fonts | Regular 400 (the only weight available) | Display text and headings H1 to H3, marketing headlines, the logo wordmark |
| **IBM Plex Sans** | Google Fonts | Regular 400, Medium 500 | All interface text: body, H4 and smaller headings, labels, buttons, navigation, form fields, captions |
| **IBM Plex Mono** | Google Fonts | Regular 400 | Evidence, file paths, package names, export names, code snippets, commit and PR references |

IBM Plex Mono is a supporting face, chosen because it is the matching monospace for IBM Plex Sans.

**Font stacks**

```css
--font-display: "Young Serif", Georgia, "Times New Roman", serif;
--font-sans: "IBM Plex Sans", system-ui, -apple-system, "Segoe UI", sans-serif;
--font-mono: "IBM Plex Mono", ui-monospace, Menlo, Consolas, monospace;
```

**Google Fonts import**

```html
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Young+Serif&family=IBM+Plex+Sans:wght@400;500&family=IBM+Plex+Mono:wght@400&display=swap">
```

### Typography rules

- Young Serif is only used at 25px and above. Below that size, headings use IBM Plex Sans Medium 500.
- Never fake bold or italic in Young Serif. It has one weight and no italic. Create emphasis with size, not weight.
- IBM Plex Sans uses two weights only: 400 for reading text, 500 for headings, labels, and buttons.
- Use sentence case everywhere, including headings and buttons. Never use all caps.
- Body text line length stays between 45 and 75 characters (a max-width of about 680px at 16px).
- Never set body text in Young Serif.

### Type scale

Base size 16px, major third ratio (1.25), rounded to whole pixels.

| Token | Font | Weight | Size (desktop) | Size (mobile, under 640px) | Line height | Letter spacing | Use |
|---|---|---|---|---|---|---|---|
| `display` | Young Serif | 400 | 48px / 3rem | 36px / 2.25rem | 1.1 | -0.01em | Marketing hero headline only |
| `h1` | Young Serif | 400 | 39px / 2.4375rem | 31px / 1.9375rem | 1.15 | -0.01em | Page title |
| `h2` | Young Serif | 400 | 31px / 1.9375rem | 25px / 1.5625rem | 1.2 | 0 | Section heading |
| `h3` | Young Serif | 400 | 25px / 1.5625rem | 22px / 1.375rem | 1.25 | 0 | Subsection heading, PR created summary |
| `h4` | IBM Plex Sans | 500 | 20px / 1.25rem | 18px / 1.125rem | 1.35 | 0 | Card titles, package group names on Results |
| `body-lg` | IBM Plex Sans | 400 | 18px / 1.125rem | 17px / 1.0625rem | 1.65 | 0 | Marketing body, intro paragraphs |
| `body` | IBM Plex Sans | 400 | 16px / 1rem | 16px / 1rem | 1.6 | 0 | Default interface and reading text |
| `label` | IBM Plex Sans | 500 | 14px / 0.875rem | 14px / 0.875rem | 1.4 | 0 | Form labels, table headers, tabs |
| `button` | IBM Plex Sans | 500 | 15px / 0.9375rem | 15px / 0.9375rem | 1 | 0 | Button text |
| `small` | IBM Plex Sans | 400 | 14px / 0.875rem | 14px / 0.875rem | 1.5 | 0 | Secondary text, helper text, metadata |
| `caption` | IBM Plex Sans | 400 | 13px / 0.8125rem | 13px / 0.8125rem | 1.45 | 0 | Timestamps, fine print. Smallest allowed size |
| `code` | IBM Plex Mono | 400 | 14px / 0.875rem | 13px / 0.8125rem | 1.6 | 0 | Evidence blocks, file paths, package and export names |

---

## 3. Color

### Light theme (default)

These are the Lichen and stone palette colors, plus three derived neutrals (marked) to complete the system.

| Token | Hex | Role |
|---|---|---|
| `primary` | `#36503F` | Lichen green. Logo, headings, links, selected states, focus ring, checkbox fill, primary brand color |
| `accent` | `#C2913A` | Ochre. Main call-to-action button fill ("Create pull request", "Connect a repo"). Fill only, never text on light backgrounds |
| `accent-hover` | `#CFA052` | Ochre hover and pressed state for the main button. Recommended starting value |
| `on-accent` | `#222823` | Text and icons placed on the ochre button. Always dark, never white |
| `logo-accent` | `#9C7024` | Darker ochre used only for the logo offcut on light backgrounds |
| `background` | `#EEF0EA` | Stone. Page background |
| `surface` | `#F8F9F5` | Cards, panels, evidence blocks, inputs. Recommended starting value |
| `text` | `#222823` | Body text, default icon color |
| `text-secondary` | `#545B53` | Secondary text, helper text, metadata. Recommended starting value |
| `border` | `#C9CFC3` | Dividers, card and input borders. Decorative only, never carries meaning on its own. Recommended starting value |
| `success` | `#2F7350` | "Safe to remove" findings, completed scans, PR created confirmation |
| `warning` | `#8A5E0E` | Findings that need a closer look, such as exports used only in tests |
| `error` | `#A33B35` | Failed scans, errors, packages that couldn't be scanned |

### Dark theme

The Lichen and stone palette has no dark colors, so these were derived to match it. All are recommended starting values.

| Token | Hex | Role |
|---|---|---|
| `primary` | `#A9C0A6` | Soft lichen. Headings, links, selected states, focus ring, logo branch |
| `accent` | `#D4A653` | Ochre. Main call-to-action fill and logo offcut |
| `accent-hover` | `#E0B66A` | Ochre hover and pressed state |
| `on-accent` | `#1D2420` | Text on the ochre button |
| `background` | `#1D2420` | Page background |
| `surface` | `#262F2A` | Cards, panels, evidence blocks, inputs |
| `text` | `#E4E7DF` | Body text, logo wordmark |
| `text-secondary` | `#A3AA9F` | Secondary text and metadata |
| `border` | `#3B4741` | Dividers and borders. Decorative only |
| `success` | `#7FC29A` | Success states |
| `warning` | `#E0B45E` | Warning states |
| `error` | `#EE968A` | Error states |

### Verified contrast (WCAG 2.1)

AA requires 4.5:1 for normal text and 3:1 for large text and graphics.

| Pair | Light ratio | Dark ratio | Result |
|---|---|---|---|
| `text` on `background` | 13.1:1 | 12.7:1 | Pass AAA |
| `text` on `surface` | 14.2:1 | 11.0:1 | Pass AAA |
| `text-secondary` on `background` | 6.1:1 | 6.7:1 | Pass AA |
| `text-secondary` on `surface` | 6.6:1 | 5.8:1 | Pass AA |
| `primary` on `surface` (headings, links) | 8.4:1 | 7.1:1 | Pass AAA |
| `on-accent` on `accent` (button text) | 5.3:1 | 7.1:1 | Pass AA |
| `on-accent` on `accent-hover` | 6.3:1 | 8.4:1 | Pass AA |
| `success` on `surface` | 5.4:1 | 6.6:1 | Pass AA |
| `warning` on `surface` | 5.4:1 | 7.1:1 | Pass AA |
| `error` on `surface` | 6.1:1 | 6.2:1 | Pass AA |
| `logo-accent` on `surface` (logo graphic) | 4.2:1 | n/a | Pass 3:1 for graphics |
| `accent` `#C2913A` as text on `background` | 2.5:1 | n/a | **Fails. Never use ochre as text in light theme** |

### Color rules

- One ochre button per view. Every other button is secondary (outline or plain).
- Ochre is a fill color in the light theme. Never use it for text, links, or thin icons on light backgrounds.
- Text on ochre is always `on-accent` (dark), never white.
- Status colors can be used as text, icons, and borders. Always pair them with an icon or a word, never color alone.
- Keep the ochre accent visually separate from `error`. The button and an error message must never look alike.
- Lichen green is the brand color. Ochre is for action. Don't swap these roles.

---

## 4. Logo

### Logo files

All logo files are outlined SVG (letters converted to shapes), with transparent backgrounds. Always use these files. Never retype the wordmark in a live font.

| File | Version | Use on |
|---|---|---|
| `lopper-wordmark-light.svg` | Wordmark | Light backgrounds |
| `lopper-wordmark-dark.svg` | Wordmark | Dark backgrounds |
| `lopper-lockup-light.svg` | Wordmark with symbol | Light backgrounds |
| `lopper-lockup-dark.svg` | Wordmark with symbol | Dark backgrounds |
| `lopper-app-icon.svg` | App icon | Any background |

### The three versions

**Wordmark.** "Lopper" in Young Serif, with the top of the L sliced at an angle and an ochre offcut sitting just above the cut. The cut is the brand idea built into the name: something removed cleanly and on purpose. This is the primary logo.

**Wordmark with symbol (lockup).** A single branch with one leaf and an ochre tip cut cleanly away, placed to the left of an uncut "Lopper" wordmark. Use it where the brand needs more presence, such as the marketing site header and social cards.

**App icon.** The cut L monogram in stone on a rounded lichen-green tile, with an ochre offcut. Use it for the favicon, the GitHub App avatar, browser tabs, and anywhere the logo is 32px wide or smaller.

### Logo colors

| Element | Light background | Dark background | App icon |
|---|---|---|---|
| Letters and branch | `#36503F` | `#E4E7DF` (letters), `#A9C0A6` (branch) | `#EEF0EA` monogram |
| Offcut | `#9C7024` | `#D4A653` | `#D4A653` |
| Tile | none | none | `#36503F`, corner radius 22% of the tile width |

### Minimum sizes

| Version | Minimum width |
|---|---|
| Wordmark | 120px digital, 30mm print |
| Lockup | 140px digital, 35mm print |
| App icon | 16px. Use this version, not a wordmark, for anything 32px or smaller |

### Clear space

- **Wordmark and lockup:** keep clear space on every side equal to the height of the lowercase "o" in the wordmark. No text, edges, or other graphics inside that space.
- **App icon:** keep clear space on every side equal to one eighth of the icon's width.

### Placement

- Use the light versions on `background` `#EEF0EA`, `surface` `#F8F9F5`, or white.
- Use the dark versions on `#1D2420` or any equally dark, plain background.
- On dark backgrounds the app icon's green tile has low edge contrast. If the tile shape must be visible, add a 1px `#EEF0EA` outline at 30% opacity.
- Place the logo on plain backgrounds only. If a photo or pattern is unavoidable, put the logo on a solid panel.

### Logo don'ts

- Don't recolor the logo outside the colors above.
- Don't move, resize, rotate, or remove the offcut. Don't join it back to the letter.
- Don't stretch, squash, skew, or rotate the logo.
- Don't add shadows, outlines, gradients, glows, or textures.
- Don't put the cut L treatment and the branch symbol together. The lockup uses an uncut wordmark on purpose.
- Don't add the leaf to the L. It turns the letter into a "Ł".
- Don't rebuild the wordmark in Young Serif text. Use the outlined files.
- Don't use the wordmark or lockup below their minimum sizes. Switch to the app icon.

---

## 5. Voice and tone

### Voice

Lopper sounds like an experienced colleague walking the codebase with you: calm, plain-spoken, and specific. It doesn't hype, rush, or shame. When it's confident, it says so and shows why. When it isn't sure, it says that too.

### Tone by moment

| Moment | Tone | Example |
|---|---|---|
| Onboarding, Connect repo | Warm and brief | "Pick a repo and we'll start scanning. There's nothing to set up." |
| Results | Factual and precise | "Found 14 unused exports across 3 packages. Here's why each one was flagged." |
| Before creating a PR | Reassuring and clear | "Nothing will be removed until you merge the pull request." |
| Pull request created | Quiet and complete | "Pull request opened with 12 removals. Review it on GitHub." |
| Errors | Honest and steady, always says what happens next | "We couldn't finish scanning this repo. Your code hasn't been changed. Try scanning again." |

### Words we always use

| Word | Why |
|---|---|
| Evidence | Our core promise. Every finding has it. |
| Prune | Deliberate, careful removal, true to the name. |
| Review | Keeps the human at the center of every change. |
| Unused | Precise and neutral. It describes the code without judging it. |
| Pull request | The safety net. Name it plainly and often. |

### Words we never use

| Word | Why |
|---|---|
| Nuke | Destructive and careless, the opposite of pruning. |
| Magic | Implies hidden reasoning, which contradicts the evidence promise. |
| Guaranteed | Overclaims, and one false flag would break the promise. |
| Bloat | Shames the team that wrote the code. |
| Blazing | Speed hype. We value care over velocity. |

### Writing rules

- Sentence case for everything: headings, buttons, labels, menu items.
- Buttons start with a verb and say exactly what happens: "Connect a repo", "Rescan", "Create pull request", "Open on GitHub". Never "Submit" or "OK".
- An action keeps the same name through the whole flow. "Create pull request" leads to "Pull request created".
- Errors say what happened, then what to do next. They don't apologize and are never vague. Always state whether the user's code was changed.
- Use contractions ("we couldn't", "you'll"). Use active voice.
- No exclamation marks in interface copy.
- Avoid "simply", "just", and "easy". They talk down to the user.
- Numbers are specific: "14 unused exports", not "some unused code".
- When Lopper is unsure about a finding, it says so plainly and shows the evidence it has.

---

## 6. Interface foundations

These are recommended starting values for the design system, chosen to match the brand's calm, spacious feel.

| Token group | Values |
|---|---|
| Spacing scale (4px base) | 4, 8, 12, 16, 24, 32, 48, 64, 96px |
| Corner radius | 6px buttons and inputs, 10px cards and panels, 22% for the app icon tile |
| Borders | 1px solid `border` |
| Shadows | None by default. Separate layers with `surface` and `border` instead |
| Focus ring | 2px solid `primary`, 2px offset |
| Content width | 680px max for reading text, 1120px max for page layouts |
| Motion | 200 to 300ms, ease-out. No bouncing or decorative animation. Respect reduced-motion settings |
| Icons | Outline style, 1.5px stroke, rounded joins, sized 16, 20, or 24px |
| Evidence blocks | `surface` background, 1px `border`, 10px radius, `code` type style, file paths in `text-secondary` |

### Design tokens (CSS)

```css
:root {
  /* Fonts */
  --font-display: "Young Serif", Georgia, "Times New Roman", serif;
  --font-sans: "IBM Plex Sans", system-ui, -apple-system, "Segoe UI", sans-serif;
  --font-mono: "IBM Plex Mono", ui-monospace, Menlo, Consolas, monospace;

  /* Light theme */
  --color-primary: #36503F;
  --color-accent: #C2913A;
  --color-accent-hover: #CFA052;
  --color-on-accent: #222823;
  --color-logo-accent: #9C7024;
  --color-background: #EEF0EA;
  --color-surface: #F8F9F5;
  --color-text: #222823;
  --color-text-secondary: #545B53;
  --color-border: #C9CFC3;
  --color-success: #2F7350;
  --color-warning: #8A5E0E;
  --color-error: #A33B35;

  /* Radius */
  --radius-control: 6px;
  --radius-card: 10px;
}

[data-theme="dark"] {
  --color-primary: #A9C0A6;
  --color-accent: #D4A653;
  --color-accent-hover: #E0B66A;
  --color-on-accent: #1D2420;
  --color-logo-accent: #D4A653;
  --color-background: #1D2420;
  --color-surface: #262F2A;
  --color-text: #E4E7DF;
  --color-text-secondary: #A3AA9F;
  --color-border: #3B4741;
  --color-success: #7FC29A;
  --color-warning: #E0B45E;
  --color-error: #EE968A;
}
```
