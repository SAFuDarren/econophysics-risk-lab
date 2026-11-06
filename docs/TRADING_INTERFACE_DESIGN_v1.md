# Trading interface design

The primary job is to let a visitor react to observable order intent, place a virtual trade and understand the resulting risk. The market itself is the focal visual. No promotional hero or repeated statistic-card grid precedes it.

## Tokens and visual choices

- Research navy `#173e60`: inherited site identity and primary controls.
- Plot ink `#243b4d`: price labels and high-contrast body text.
- Up teal `#197b70`: rising candles, long-side execution.
- Down rust `#b34e43`: falling candles, short-side execution; functional colour, not decoration.
- Slate `#667785`: secondary data and metadata.
- Grid/paper `#dce5eb` / `#f5f8fa`: plot rhythm and workspace background; main plot remains white.

Source Sans 3 carries controls, readable data and body text. Source Serif 4 carries the restrained page title, following the existing research site. All data uses tabular figures; no tiny all-caps or mandatory monospace labels.

## Layout

Desktop: inherited site header; compact title; single setup/playback strip; main market frame split into chart/events on the left and account/order ticket on the right. The bottom continuation contains a small mechanism view, clear rules and research links.

```
site navigation
title                            short synthetic-market marker
scenario / guided-experiment / playback / retry
market name + last price         account net value
candle chart                     position, trade size, order actions
volume chart                     trades + available capital
event tape                       account history
phase/fast/slow view              review rules / mathematics link
```

Mobile stacks market, ticket and event tape; controls wrap into purposeful rows, plot axes remain inside the viewport, and order actions are reachable with touch. No hover-only explanation or drag-only control is required.

## Brief review

A black terminal with neon gain labels would not match the existing academic site. A white board with restrained market colours and a genuine interactive candle plot provides the trading character without changing the site's identity. The chart, price markers and readable order ticket are the deliberate visual focus; model commentary remains quieter and follows the action.

## Content and states

The fictional instrument is named Collective Index. A concise synthetic-market label is always visible. Guided mode describes set teaching conditions; experiment mode shows only current intent. The empty chart tells users to start or advance one tick. Order feedback uses plain bilingual explanations. End-of-round review opens after all positions settle, with numbers from the accounting module and the engine's actual path. Scores never imply real-world predictive success.

Keyboard focus, reduced motion, dialog dismissal, 390-pixel layout, bilingual state changes and real-engine interactions are acceptance requirements. SVG/canvas assets are native and require no external chart service or remote font requests.

## Review iteration

Real-engine desktop/mobile review identified three interaction issues: a narrow mobile title, order messages below the mobile fold and native-dialog positioning. The title now has a full-width line with the synthetic marker beside the back link; the latest intent/execution message is repeated inside the chart frame; and the modal uses explicit viewport positioning with internal scroll. Guided playback pauses when an intent arrives, giving visitors time to choose before continuing. Experiment playback does not pause automatically. The detailed event tape remains available for chronological review.

The root acceptance run has already exercised long/short entry, partial exit, final settlement, mode/settings changes and language switching with no console or HTTP errors. Final visual screenshots and bounds are checked by root after the iteration; this note does not substitute for those exported QA records.

## Human-paced playback and optional order signals

The playback strip now exposes 0.25×, 0.5×, 1×, 2× and 4×. One-times speed means two real seconds per model tick; the default is 0.5×, or four seconds. The current seconds-per-tick value is visible in both languages. Changing speed preserves the current path, account and model state, and reschedules only the browser timer. Mobile uses one row for play, step and retry, followed by one full-width speed row.

Large-order signals have a separate bordered information area above the chart, with an accessible switch. Turning signals off suppresses intent, execution and completion messages in both this area and the event tape; it also suppresses the revealing guided-mode intent pause and feedback. The market process is unchanged. Signal and speed choices survive retry and scenario resets within the page session. Review records when each message first became visible, so enabling signals later cannot retrospectively count that information at an earlier trade.

The scenario selector and mechanism view remain visible. This switch is an optional-information interaction, not a blinded experiment or an empirical estimate of the value of private information. The model, source code and chosen scenario are public.

`tests/test_trading_controls.cjs` uses a controlled browser clock to verify real pacing, timer changes, signal visibility, pause behavior, state invariance, review information timing, keyboard use and the four responsive widths. It uses the same Playwright environment variables as the main browser acceptance test.

## Evidence-labelled mechanism debrief

The completed-round review uses one time cursor across actual close prices and fills, observed large executions, conditional execution amplification and the risk map. Original observations use teal source tags; model-conditioned quantities use restrained bronze `#8b632a`; the G=1 reference is grey. This is a true sequence, so the three reading columns correspond to trade weights, amplification and the response/risk map. Mobile stacks these readings and renders each SVG at its actual available width.

RMS targets and information costs stay explicit. The observed curve summarizes already realized minute returns; model risk is a next-minute estimate at the selected origin, with coefficients fixed before play. Rich aggregate-execution B is identified as an observed input rather than hidden behind a macro-only claim. Theoretical details use locally rendered LaTeX, while checkpoints keep the first reading concrete. The dialog heading and close button remain reachable during long reviews.
