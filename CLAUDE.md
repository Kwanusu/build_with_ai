## Stack

- TypeScript, React 19 and Vite. Styling is Tailwind CSS 4, with the theme generated from DESIGN.md. Tests use Vitest and Testing Library.
- `npm run dev` starts the dev server. `npm run build` type-checks and builds to `dist/`. `npm run typecheck` only type-checks.
- `npm test` runs the tests. Run it, and `npm run build`, before every commit.
- Layout: `src/content.ts` holds page copy, `src/components/` the React components, `src/index.css` the semantic colour roles and component styles, and `styles.css` the generated Tailwind theme.
- Logos are in `assets/logo/`. Use the files as supplied through `src/components/Logo.tsx`; never retype, recolour or redraw them. The lockup goes in the header, the wordmark in the footer and on small screens, and the app icon is the favicon.
- Write all code in TypeScript. Keep copy in `src/content.ts`, not inline in components.

## Design

- Read DESIGN.md before any change to the interface.
- Use only the colors, fonts, sizes, spacing and corner radius in DESIGN.md. Never hard-code a value that isn't in it.
- If a screen needs something DESIGN.md doesn't have, ask me first, then add it to DESIGN.md before using it.
- After any edit to DESIGN.md, run `npm run design:lint` and fix every error and contrast warning, then run `npm run tokens` to regenerate `styles.css`. (`npx @google/design.md lint` prints nothing on this machine, so the script calls the CLI with node directly.)
- Use the primary (ochre) button once per view.
