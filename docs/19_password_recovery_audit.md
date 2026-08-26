# Password Recovery — Audit Checklist

> Use this checklist to verify whether an existing system meets the
> user-friendly design specification in `spec.yaml`.

## ① Core Principles (spec §2) — Measurable by AI

- [ ] **Predictability** — Is there a finite state machine (or equivalent transition table)
      that defines every valid state → action → next-state mapping? Can every
      user action be traced to exactly one expected response?
- [ ] **Self-explanatory** — Does every UI section (form, button group, step)
      have a help text, tooltip, or `aria-label` explaining its purpose?
- [ ] **Minimal cognitive load** — At any screen, are there ≤ 7 visible
      interactive options (buttons, links, inputs)? Count and record.
- [ ] **Immediate feedback** — Does every click/keystroke produce a visible
      status change within ≤ 300 ms? Check with a stopwatch or devtools.
- [ ] **Accessibility (WCAG 2.1 AA)** — Run an automated checker (axe-core).
      Verify: color contrast ≥ 4.5:1 for body text, `aria-label` on all
      interactive elements, logical heading order (h1→h2→...), focus trap /
      focus-visible on modals.
- [ ] **Error recovery** — For every error message, verify it (a) uses no
      technical jargon, (b) contains no error codes, and (c) offers ≥ 2
      actionable next steps.

## ② Interaction Flow (spec §3) — State Machine Compliance

- [ ] The system implements exactly the 6 states: `Welcome`, `Data_Entry`,
      `Confirmation`, `Processing`, `Result`, `Error_Recovery`.
- [ ] `Welcome → Data_Entry` on `Start_Button` event.
- [ ] `Data_Entry → Confirmation` on `Valid_Input` event.
- [ ] `Data_Entry → Error_Recovery` on `Invalid_Input` event.
- [ ] `Confirmation → Processing` on `Confirm` event.
- [ ] `Confirmation → Data_Entry` on `Edit` event.
- [ ] `Processing → Result` on `Success` event.
- [ ] `Processing → Error_Recovery` on `Fail` event.
- [ ] `Error_Recovery → Data_Entry` on `Retry` event.
- [ ] `Error_Recovery → Welcome` on `Cancel` event.
- [ ] No forbidden transitions are reachable (e.g. `Welcome → Result` directly).

## ③ UI Component Specs (spec §4)

- [ ] **Primary CTA Button**: background color `#005A9C`, text ≤ 3 words,
      clickable area ≥ 44 × 44 px, ≥ 20 px spacing from adjacent elements.
- [ ] **Input Field**: has a fixed `<label>`, an example placeholder,
      real-time validation, and a validation message rendered directly
      below the field.
- [ ] **Navigation/Menu**: ≤ 5 top-level items, each with icon + text,
      active item indicated by underline or color change.
- [ ] **Error Message**: contains exactly 3 parts — (1) warning icon,
      (2) error text with no error codes, (3) "More Help" button that opens
      a step-by-step guide.
- [ ] **Progress Indicator**: for multi-step processes, shows a progress bar
      with percentage AND step count (e.g. "Step 2 of 4").

## ④ Usability Metrics (spec §5)

- [ ] **Task Completion Rate (first attempt)** ≥ 95% — record from A/B test.
- [ ] **Average task time** ≤ 2 minutes — record from A/B test.
- [ ] **User error rate** ≤ 5% of all interactions — record from A/B test.
- [ ] **System Usability Scale (SUS)** score ≥ 70/100 — record from survey.
- [ ] **Testing protocol**: 100 real users across 3 scenarios — verify
      this was executed.

## ⑤ Edge Cases (spec §6)

- [ ] **Empty input or special characters**: Does the system reject empty
      input and validate against malformed input before transitioning?
- [ ] **Temporary internet disconnection**: Can the user resume after a
      network failure without re-entering data? Is there local auto-save?
- [ ] **Responsive design 320px–1920px**: No horizontal scrolling at any
      width. Content reflows gracefully.
- [ ] **Dark/Light mode**: Auto-switches; all colors maintain ≥ 4.5:1
      contrast in both modes.
- [ ] **Screen reader support**: Every interactive element has `aria-label`
      or visible text; dynamic content uses `aria-live`.

## ⑥ Anti-Patterns Forbidden (spec §9)

- [ ] No technical jargon ("exception", "socket", "buffer") in user-facing
      messages — grep the codebase for these terms in UI strings.
- [ ] Buttons do not jump/reposition between steps — positions are stable.
- [ ] No pop-ups overlap while the user is typing — verify z-index stacking.
- [ ] No horizontal scrolling on any page — viewport `overflow-x: hidden`
      or equivalent; all content fits within 100vw.

## ⑦ Concrete Scenario Verification (spec §8)

- [ ] Login page has a "Forgot password?" link.
- [ ] Clicking it opens a flow with exactly 1 input (email) and 1 primary
      button ("Send recovery link").
- [ ] After valid email → green message: "Recovery link sent to your email".
- [ ] If invalid email → red message: "This email is not registered..."
      with ≥ 2 actionable solutions.
- [ ] A visible "Back" button exists in the top-left corner at every step.

## ⑧ Technical Metadata (spec §7)

- [ ] `spec.yaml` (or `manifest.json`) exists at the project root.
- [ ] Contains the required fields: `version`, `language_family`,
      `feedback_modes`, `error_philosophy`, `learning_mechanism`,
      `testing_protocol`.

## ⑨ Audit Score

| Category | Items | Passed | Failed |
|---|---|---|---|
| Core Principles | 6 | _ | _ |
| State Machine | 9 | _ | _ |
| UI Components | 5 | _ | _ |
| Usability Metrics | 4 | _ | _ |
| Edge Cases | 5 | _ | _ |
| Anti-patterns | 4 | _ | _ |
| Scenario | 5 | _ | _ |
| Metadata | 1 | _ | _ |
| **Total** | **34** | **__** | **__** |

**Overall verdict**: □ PASS (all mandatory) □ FAIL (see failed items above)
