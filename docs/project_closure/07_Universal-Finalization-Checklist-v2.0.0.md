# UNIVERSAL PROJECT FINALIZATION CHECKLIST
## Domain-Agnostic Closure Gate — Works for ANY Project Type: Software, Research, Construction, Content, Event Planning, Consulting, Marketing, Manufacturing

**Document ID:** BW-UNIVERSAL-CLOSURE-v2.0.0  
**Standard:** Aligns with PMBOK® 6th/7th Ed Closing Process Group + ISO 21500 Guidance on Project + Subject to the 4-C Quality Framework (Completeness, Correctness, Consistency, Clarity)  
**Intended Audience:** Project Managers, Program Managers, Project Closure Managers, Delivery Leads, QA Directors, Compliance Officers  
**Classification:** UNIVERSAL — APPLICABLE TO ALL DOMAINS

---

## HOW TO USE THIS CHECKLIST FOR NON-SOFTWARE PROJECTS

**If your project is NOT software, replace the technical test suites from §2.1 with the equivalent Quality Verification listed below.**

| Project Type | §2.1 "Regression & Integration Test Suites" Replacement | §2.2 "Technical Debt / Code" Equivalent |
|--------------|--------------------------------------------------------|------------------------------------------|
| **Scientific Research (e.g., Clinical Trial, Paper)** | (1) Statistical re-analysis (double-blind re-run of primary endpoints, alpha=0.05, power ≥ 0.80). (2) Full reproducibility audit: raw data → tidy data → analysis code → figures 1,2,3 all regenerate identically via single script. (3) Co-author sign-off on every table + figure + supplementary material. (4) IRB / Ethics compliance re-verification (informed-consent rate, adverse-event reporting, data retention schedule). (5) Journal-submission formatting pass: target journal template, word count, ref style matches exactly. | Irreproducible scripts, incomplete raw-data backups, unlabeled version of analysis notebook, stale references to superseded data extracts, hardcoded p-values in manuscript |
| **Commercial Construction (e.g., Office Building Fit-out)** | (1) Punch-list walkthrough 100% complete (every room, every window, every door, every light fixture, every outlet, every plumbing fixture). (2) MEP commissioning: HVAC airflow, electrical load test, plumbing hydrostatic test, fire-alarm full-system test. (3) Structural steel bolt-torque audit report + weld NDT (non-destructive testing: ultrasonic + magnetic particle). (4) Certificate of Occupancy (CO) pre-submission: fire code, accessibility code (ADA/ANSI A117.1), egress widths all pass official inspection. (5) As-Built drawings 100% reconciled vs. Design Development drawings — every RFI / Change Order reflected. | Unapproved change orders, missing MEP submittal data, uncorrected punch-list items > 14 days old, out-of-date spec sections, unreconciled RFI logs, supplier warranty docs not collected |
| **Marketing / Brand / Content Campaign (e.g., Product Launch)** | (1) All assets: Copy deck (English reviewed for: spelling, grammar, AP style, brand voice, legal-approved disclaimer placement). (2) Visual QC: Every image renders correctly across breakpoints (mobile 375, tablet 768, desktop 1280, 4K). RGB vs CMYK verified for digital vs print channels. (3) Accessibility: Alt text on every image, descriptive link text, video captions + audio descriptions present. (4) Legal review complete: trademark ™/® registered marks, competitive claims have substantiation, data citations to third-party research are accurate, GDPR/CCPA opt-outs correct. (5) Calendar audit: All 42 campaign deliverables have scheduled publish dates in CMS/MarTech stack + proofreader + approver assigned. | Unapproved copy, missing image alt text, broken links, uncompressed assets (>5MB unoptimized), stale copyright year, mismatched brand-color hex codes, no-op tracking pixels, expired UTM links |
| **Event Planning (e.g., 2,000-person conference)** | (1) Run-of-Show minute-by-minute script verified against every vendor contract (A/V, Catering, Venue, Security, Badging, Transportation, Hotel Block). (2) Fire Marshal pre-event walkthrough: capacity counts per room, exit sign illumination, emergency egress pathways clear of exhibitor booths. (3) Audio A-B full-room test: wireless mics, backup wired mics, hearing-loop T-coil, live-caption screen, ASL interpreter booth confirmed. (4) Badge count + VIP + press + attendee segmentation 100% reconciled against EventBrite/Cvent RSVP list. (5) Contingency weather plan (outdoor component) + medical on-site + electrical backup generator test run. | Unconfirmed vendor final counts, un-signed event insurance certificate, catering dietary restriction list not cross-checked with attendee list, AV tech-rider not reconciled with actual speakers A/V needs, printed signage contains typo on speaker names |
| **Regulatory / Compliance Deliverable (e.g., FINRA/SEC Filing)** | (1) Every number cross-footed (Excel sheet sum = reported value) by two people independently. (2) Cross-reference to source-of-truth systems (General Ledger trial balance, Trading P&L extracts, HR headcount report). (3) Materiality threshold analysis: every item > 0.5% of Total Assets flagged and individually justified. (4) Legal reviewer sign-off + Compliance reviewer sign-off + CFO sign-off. (5) E-signature audit trail shows all required reviewers in correct chronological order (no backdating). | Un-supported journal entries, rounding errors > 1 unit of precision, stale supporting-workpaper references, unsigned management-representation letter, stale officer titles in signature block |

---

## THE 4-C QUALITY FRAMEWORK — DEFINED (ALL DOMAINS)

Every final deliverable must satisfy all FOUR Cs:

| C | Dimension | Definition (ISO 9126-aligned) | Test Question You Ask |
|---|-----------|--------------------------------|----------------------|
| **1. COMPLETENESS** | Every item promised in the Statement of Work (SOW) / Contract / PRD / Research Protocol is PRESENT in the final package. Nothing required is missing. No scope items left "later" or "deferred to future" without formal Change Order / CR record. | "If the customer opened the final delivery box and used ONLY what's inside, could they accomplish the ENTIRE stated purpose of the project without calling us for something we forgot?" |
| **2. CORRECTNESS** | Facts, figures, calculations, data, measurements, code, language, legal clauses are FREE of error. Numerical cross-footings balance. Spelling/grammar is error-free. Technical outputs match known-good benchmarks (golden data set). | "If an independent third-party domain expert reviewed this deliverable line-by-line, would they sign a sworn affidavit that every statement in it is true and accurate to the best of their professional knowledge?" |
| **3. CONSISTENCY** | Terminology, naming, units, formatting, version numbers, color palettes, fonts, tone-of-voice, structural conventions are UNIFORM across every page, file, artifact, module, drawing, slide. No "file A says X = 5, file B says X = 6" discrepancy. No "Chapter 1 uses SI units, Chapter 4 uses Imperial" chaos. | "If you printed every deliverable on paper, shuffled the pages, and asked a new person to read them — could they tell they belong to the SAME project, without seeing the cover? Or are there jarring style/naming/format jumps between pages?" |
| **4. CLARITY** | Any sufficiently-qualified reader (target persona defined upfront) can understand the deliverable WITHOUT calling the author. Ambiguity is zero. All abbreviations defined on first use. All acronyms spelled out. All dependencies explicitly called out. All assumptions listed. All edge cases addressed (see §2.1 edge-case pattern). | "If we handed ONLY this deliverable (no Slack history, no meeting recordings, no author available) to the intended audience, would they be able to use it correctly on their first try with 95% accuracy?" |

---

## MASTER UNIVERSAL FINALIZATION CHECKLIST
### Section I: Completeness (C-1) — 32 Checks

| ID | Check (Domain-Agnostic) | Applicable Project Types | Verification Method | PASS Criteria | Status ☐/☑ |
|----|-------------------------|--------------------------|---------------------|---------------|-------------|
| C1-01 | ✅ Full SOW / Contract deliverables list mapped 1:1 to final deliverable inventory with no gaps. | ALL | Side-by-side traceability matrix: Row per SOW item → Column for "Delivered In File X.Y" | 100% of SOW rows have a "Delivered In" filled. 0 rows marked "N/A" without CR number. | ☐ |
| C1-02 | ✅ All Change Orders (CRs / COs) since kickoff are documented: CR number, date, scope delta (+/-), cost delta, schedule delta, sponsor signature. | ALL | Project Change Log. Every entry has: (1) description, (2) impact triple constraint, (3) written approval. | Zero undocumented scope changes. Every change traceable to signed paper / digital CR form. | ☐ |
| C1-03 | ✅ All major / minor / patch changes documented in CHANGELOG (§2.4.2 style — Keep a Changelog format). | Software, Content, Research, Marketing | CHANGELOG.md file exists with entries for every milestone since v0.1. | Changelog covers 100% of releases. Each release has Added/Changed/Fixed sections. | ☐ |
| C1-04 | ✅ Final version number / nomenclature assigned (SemVer for software, Calendar Versioning for events/research, Construction Drawing Revision: A, B, C…). | ALL | VERSION.txt / document title page / drawing title block. | Version on every deliverable matches the one agreed in Project Closure meeting. | ☐ |
| C1-05 | ✅ All "TODO / FIXME / TBD / DEFERRED / PLACEHOLDER" placeholders removed from final text/code/drawings. | Software, Research, Construction, Content | Project-wide grep / find-in-files for the 6 placeholder strings. | 0 matches across 100% of files in delivery tree. Any intentional "placeholder" must be in CHANGELOG as Known Issue. | ☐ |
| C1-06 | ✅ All supporting references cited (journal articles, standards, building codes, data sources, competitor benchmarks). | Research, Content, Compliance, Marketing | Reference list / Bibliography / Works Cited section. | Every statement that references external data has a citation. URL links resolve (click test 10% sample; 0 broken). | ☐ |
| C1-07 | ✅ All pre-requisite inputs / dependencies explicitly listed with versions: "This work requires Python 3.11 + PostgreSQL 16 + Redis 7.4 (§2.3 README Prerequisites)" OR "This report assumes US GAAP ASC 606 effective date 2025-01-01". | ALL | Prerequisite / Assumptions section in README or Front Matter of document. | Reader can set up environment without guessing. 0 implicit assumptions. | ☐ |
| C1-08 | ✅ Final delivery file-packaging matches §2.4.1 canonical folder structure (or equivalent for non-software: research data / construction drawings / marketing assets organized into standard subfolders). | ALL | Open the archive. Walk every top-level folder. Compare against Master Folder Structure definition. | Every promised folder present. No stray files in archive root. | ☐ |
| C1-09 | ✅ Cryptographic checksum (MD5 legacy + SHA-256 authoritative §2.4.3) calculated for master package with reproducible packaging procedure. | ALL (digital deliverables) | `sha256sum` on receiving side matches documented checksum. | 64 hex character match character-by-character. Documented verification procedure included. | ☐ |
| C1-10 | ✅ Intellectual Property (IP) ownership, copyright notices, licenses of third-party components, patent disclosures: All present in LICENSE.txt + NOTICE.txt. | Software, Research, Content, Marketing | Locate LICENSE.txt at root. NOTICE.txt enumerates every third-party component with its own license. | No unfilled fields in IP section. All open-source licenses compatible. All stock-images credited. | ☐ |
| C1-11 | ✅ Data privacy (GDPR / CCPA / HIPAA) / personally identifiable information (PII) purged from final delivery package. | ALL that handle user data. | PII scan: grep for email regex, phone regex, SSN regex, street-address regex. | 0 PII matches. If PII is required by design (research study), de-identification certificate on file. | ☐ |
| C1-12 | ✅ All raw source materials retained in separate retention location per records-retention policy (7 years minimum for financial/medical; 10 years construction; 3 years marketing). | ALL | Records Retention Schedule. Audit: 10% sample of raw source files present in retention store. | Retention location accessible. S3 / off-site tape / physical file cabinet locked. Access control list in place. | ☐ |
| C1-13 | ✅ User-facing manual / operating manual / methodology doc present. | ALL (§2.3.2 for software; equivalent for non-software: User Manual for lab equipment, O&M Manual for construction building, Campaign Playbook for marketing, Run-of-Show binder for events) | Locate manual. Open to page 1. Walk table of contents. | Manual covers: install/configure/operate/troubleshoot/decommission OR research/analyze/reproduce. | ☐ |
| C1-14 | ✅ Administrator / Operator / Maintainer guide separate from user guide. | Software, Construction, Event (venue teardown guide), Research (lab manager tear-down SOPs) | Admin Guide includes: patching, upgrade, backup, restore, user management, audit logs. | 10 critical admin actions documented with step-by-step + screenshots / photos. | ☐ |
| C1-15 | ✅ Training materials produced: Slide deck + recording (30-min walkthrough video) + hands-on lab environment / demo dataset. | Software, Construction (operator training), Marketing (campaign execution training) | Training folder contains: slide deck (.pptx), video (.mp4 1080p), demo data set. | Training assets validated against target audience (3 users review + sign off "I can operate after this training"). | ☐ |
| C1-16 | ✅ Warranty / Guarantee terms documented clearly: "90-day warranty period from date of acceptance; bug-fix SLA P1 = 24h fix; P2 = 3 business days; P3 = best effort." | Software, Construction, Manufacturing, Equipment Purchase | Warranty clause in handover contract. | No ambiguous "reasonable effort." SLA times in hours/days. Clear start/end dates. | ☐ |
| C1-17 | ✅ Knowledge transfer / training sessions held with receiving team. Attendance roster signed. Q&A log captured. | ALL | Attendance sheet (names + roles + signatures). Q&A document with 20+ logged questions + written answers. | ≥ 90% of receiving team attended. Q&A log reviewed and closed by trainers. | ☐ |
| C1-18 | ✅ Outstanding items / post-deferred backlog triaged: (a) Must-fix before go-live → fixed before closure. (b) Post-launch patch → v2.0.1 issue tracker. (c) Future v3.0 → roadmap with estimated quarter. | Software, Research, Content | Triage spreadsheet with 3 columns + assignees. | MUST-FIX column = 0 items at closure. 0 un-triaged gray items. | ☐ |
| C1-19 | ✅ All 5 critical edge cases (adapt per §2.1 pattern: top-5 failure modes specific to project type) have documented expected outcome + verified pass. | ALL | Edge case table in QA report. Each row: description, reproduction, expected, status. | All 5 = PASS. 0 edge cases "not tested." | ☐ |
| C1-20 | ✅ Critical-path integration check end-to-end (non-software equivalent: commissioning test). Walk through the PRIMARY VALUE STREAM from start to finish. Example for software: Register → Login → Dashboard → Ranking → Stock page → Forecast → Alert; Example for research: Raw CSV → Clean → Run model → Generate figures → Compose paper → PDF export → Journal submission zip. | ALL | Document step-by-step walkthrough with screenshots/photos at each step. Final step produces the documented "happy path" output. | 0 failures in E2E walkthrough. Every intermediary step output within expected tolerance. | ☐ |
| C1-21 | ✅ All Accessibility requirements (WCAG 2.1 AA for digital / ADA Title III for physical construction / 508 for government) 100% verified with independent audit. | Software, Marketing (digital properties), Construction (physical), Events (venue) | Accessibility Audit Report (axe-core for digital, CASp inspector for physical) + remediation log. | 0 critical / high / medium issues. All low issues either fixed OR documented as "structural infeasible, reasonable accommodation in place". | ☐ |
| C1-22 | ✅ Security review sign-off (software: SAST + DAST + secret scan + dependency audit; non-software: data security classification, building site security plan, event crowd safety plan). | ALL | Security Review Report, signed by CISO / designated Security Officer. | 0 unremediated critical / high findings. Every medium finding has remediation owner + date committed. | ☐ |
| C1-23 | ✅ Performance / Capacity / Throughput requirements met. Example for software: 120 concurrent users (§2.1); For research: statistical power ≥ 0.80 at effect size d=0.4; For construction: HVAC 30 ton cooling capacity meets design load at 95°F ambient; For event: venue 2,000-person capacity ticketed. | ALL | Performance Test Report / Commissioning Report / Statistical Power Analysis Report. | Measured value ≥ 110% of contractual requirement (10% safety margin). | ☐ |
| C1-24 | ✅ Compatibility matrix verified: Software (Chrome 120+, Firefox 121+, Safari 17.2+, Edge 120+); Research (R 4.3.1 on Win/Mac/Linux reproduce same results ± floating point tolerance); Construction (equipment fits through standard 36" door, electrical plug NEMA 5-15); Marketing (renders correctly on iPhone 15, Samsung S24, 15" laptop, 27" 4K). | ALL | Compatibility Test Matrix. N rows = target platform, columns = Tests run, PASS/FAIL. | 100% PASS rate across all supported platforms. All unsupported platforms listed as "not tested — not supported". | ☐ |
| C1-25 | ✅ Rollback / Recovery / Contingency plan in place for go-live day. Top 3 residual risks identified (§2.5 pattern). Each has Mitigation + Step-by-step Rollback. | ALL (Software: R-01 DB schema, R-02 auth, R-03 ML cold-start; Research: statistical analysis re-run plan; Construction: weather-delay re-schedule; Marketing: campaign pause + revert to evergreen copy; Event: indoor-rain plan, medical-emergency evacuation plan) | Risk Register. Top 3 risks. Mitigation column. Step-by-step Rollback column. Estimated rollback duration. | Each risk has named owner. Rollback steps tested in dry-run. Duration realistic (add 20% contingency). | ☐ |
| C1-26 | ✅ Backup strategy validated via actual restore. (Software: §2.6 Phase 1.8; Research: raw data recoverable from cold storage in < 4h, checksum OK; Construction: as-builts backed up in 3 locations; Marketing: campaign assets in DAM version history.) | ALL | Restore DRY RUN documented. Walkthrough from "worst case total loss scenario" to "fully restored". | RTO (Recovery Time Objective) met. RPO (Recovery Point Objective) met. Restore output matches known-good snapshot. | ☐ |
| C1-27 | ✅ Production / Live environment monitoring: Alert rules configured. PagerDuty / Opsgenie / on-call roster active. Test page sent to every on-call rotation member. ACK < 5 minutes. | Software, Events (on-call staff), Construction (24h security hotline), Research (lab equipment failure alarm system) | Test alert documented. Time-stamp of page. Time-stamp of acknowledgment. | All on-call members acknowledged within 5 minutes. All escalation chains work (no dead phone numbers / invalid emails). | ☐ |
| C1-28 | ✅ Final stakeholder sign-off page executed (§2.6 signature page pattern). All required roles signed with date. | ALL | Signature page physically printed + wet signed OR digital e-signature (DocuSign / Adobe Sign) with audit trail. | 100% of required signatories have signed. 0 signature lines are blank. Dates consistent. | ☐ |
| C1-29 | ✅ Executive Summary produced (§2.6.1 pattern): Achievements quantified (before/after table), ROI 12-month estimate, Lessons Learned top 6. | ALL | One-page Executive Summary PDF. Distribute to Steering Committee 48 hours before Closure meeting. | Sponsor reads summary, signs off "I have read, understood, and agree with the achievements, ROI, and lessons learned." | ☐ |
| C1-30 | ✅ Financial closure: All vendor invoices paid or accrued. All contractor POs closed. Cost vs budget variance report final. Any over-budget > 10% has variance explanation signed. | ALL | Project Financial Closure Report. Final spend vs. baseline budget. Cost Performance Index (CPI) = Earned Value / Actual Cost. | 0 open POs. 0 disputed invoices in litigation. CPI ≥ 0.90 (within 10% budget tolerance, sign-off required if < 0.90). | ☐ |
| C1-31 | ✅ Schedule closure: Final Gantt / schedule. Planned finish vs actual finish. Variance days. Any critical-path slip > 5 days has root-cause analysis. | ALL | Final Schedule Report. Baseline vs Actual columns. Milestone slip table. | No "we'll finish it later" milestones. All 100% complete milestones marked 100% in PM tool. | ☐ |
| C1-32 | ✅ Team recognition: Individual thank-you notes distributed. Team celebration event booked. Lessons learned shared HR-wide for future similar projects. | ALL (mandatory, people-management hygiene) | Thank-you note distribution list. Celebration event calendar invite. Lessons learned catalog entry filed. | 100% of FTE team members have received personal recognition from Sponsor. | ☐ |

---

### Section II: Correctness (C-2) — 16 Checks

| ID | Check | Verification Method | PASS Criteria | Status ☐/☑ |
|----|-------|---------------------|---------------|-------------|
| C2-01 | Numerical cross-footing: All Σ columns = Σ rows (Excel tables, SQL SUM, construction cost estimates, campaign budget totals). | 2-person independent cross-foot. 10% of numerical cells spot-checked by third person. | 0 arithmetical errors. If error found → 100% recheck all cells, not just 10%. | ☐ |
| C2-02 | Unit-of-measurement consistency: All figures in same unit (USD, not mix USD/EUR; meters not mix feet/inches; Celsius not mix °C/°F). Conversion factors documented where required. | Grep all numbers + their units. | Every numeric figure has explicit unit annotation. Conversion factors have source (NIST, OANDA closing rate date). | ☐ |
| C2-03 | Date range validity: All end dates > start dates. All project dates after project kickoff. All research/financial dates within dataset range. | Scripted check of all YYYY-MM-DD fields. | 0 negative-duration ranges. 0 dates outside data-boundary. | ☐ |
| C2-04 | Spelling + grammar pass (EN-US dictionary, AP style or Chicago Manual as applicable). | Grammarly / Microsoft Editor professional-grade + human proofreader pass. | 0 spelling errors. 0 grammar issues. Brand-name capitalizations correct (e.g., BedaanWaves not Bedaanwaves, PostgreSQL not Postgres). | ☐ |
| C2-05 | Technical accuracy: All code compiles / all formulas compute / all blueprints dimensionally accurate / all arguments logically sound. | Independent domain-expert review. Checklist-style verification. | Reviewer sign-off on technical accuracy. Any corrections incorporated. | ☐ |
| C2-06 | Reproducibility / determinism: Golden input → golden output. | Run full pipeline twice on identical inputs. | Output_1 == Output_2 (allowing documented floating-point epsilon tolerance: 1e-9). | ☐ |
| C2-07 | No hardcoded secrets / passwords / API keys / private keys embedded in source or sample data. | Gitleaks / truffleHog / regex scan entire repo / text corpus. | 0 secret matches. ENV variables or Vault referenced. | ☐ |
| C2-08 | Legal + contractual compliance: All clauses honored. No deliverable contradicts the MSA/SOW. Regulatory stamps present where required (UL, CE, FCC, FDA, CE marking, etc.). | Legal / Compliance review sign-off. | Reviewer: "No conflicts. All regulatory stamps applicable to this project class are affixed." | ☐ |
| C2-09 | Version history / audit trail: All files have meaningful commit messages. All edits tracked. No anonymous modifications. | Git log / document metadata / DMS history. | Every change has author + timestamp + rationale (commit message / comment). | ☐ |
| C2-10 | Calculation benchmark: Compare against known-good third-party result ("golden data set"). | Benchmark script. | MAPE < 0.1% vs golden; or 100% match for discrete outputs. | ☐ |
| C2-11 | Terminology accuracy: Industry jargon used correctly per ISO/IEEE/ASME/ASTM/GAAP/IFRS standards. | Subject matter expert glossary review. | 0 misused technical terms. First-use abbreviation spelled out. | ☐ |
| C2-12 | "Clickable" references: Every hyperlink resolves, every file-path in documentation exists, every table/figure reference points to real page. | Automated link checker + manual 10% sample. | 0 broken links. 0 "Figure 12" references to non-existent figures. | ☐ |
| C2-13 | No off-by-one errors: Array indices, pagination offsets, floor plans room numbering, seating chart seat count. | Automated boundary test + manual. | Min=0, Max=N-1 all handled correctly. Empty input case handled. | ☐ |
| C2-14 | Timezone + Daylight-Saving: All timestamps explicit ISO 8601 UTC or with offset. Localization correct (market open at 13:30 UTC = 09:30 ET, EST/EDT transitions handled). | DST boundary test. | No ambiguous "00:00" midnight interpretations without explicit zone. | ☐ |
| C2-15 | No plagiarism / unattributed content: Original text written for this project OR licensed-in content clearly marked with attribution. | Plagiarism scan (Turnitin / iThenticate for research; Copyscape for marketing). | Similarity score < 5%. All quoted / licensed material clearly marked + referenced. | ☐ |
| C2-16 | Final sign-off on Correctness: QA Director / Verification Engineer / QC Manager signs. | QC Report. Signature. | QC Director: "I attest that this deliverable has been verified against Section II Correctness criteria and meets all contractual quality requirements." | ☐ |

---

### Section III: Consistency (C-3) — 12 Checks

| ID | Check | Verification Method | PASS Criteria | Status ☐/☑ |
|----|-------|---------------------|---------------|-------------|
| C3-01 | Naming conventions: All variables / files / folders / drawing sheets / campaign assets follow single documented standard (§2.2.2 ISO pattern — PascalCase, snake_case, kebab-case consistent per layer). | Grep for mixed-case / mixed-convention offenders. | 0 offenders. Documentation naming rules file in place. | ☐ |
| C3-02 | Brand system: Colors match hex codes, fonts match (Inter only, per project memory), logo variants used correctly (clear space rule), tone of voice matches brand guide. | Spot check 20 visual elements against brand style guide. | 0 mismatches. No off-brand purple / green / "designer's personal favorite". | ☐ |
| C3-03 | Spacing / layout grid: 8px spacing grid honored. Paragraph leading consistent. Drawing border sizes consistent. | Automated layout diff (UI) / CAD layer check (construction). | All measured margins / padding ∈ 8·N pixels (or mm for print). | ☐ |
| C3-04 | Terminology consistency: Same term used everywhere (e.g., always "Total Score" never "Overall Rating" interchangeably; always "symbol" never "ticker" / "instrument" / "code"). | Grep entire corpus for all synonyms. | Canonical term list in glossary. Only canonical forms used in final text. | ☐ |
| C3-05 | Document formatting: Page margins, header/footer, page numbering, table of contents depth, section numbering (§1.2.3 or 1.2.3 pattern), footnote styles — identical across ALL pages. | Visual inspection of every 10th page + first / last page of every document. | No page jumps from "portrait" to "landscape" without rotation indicator. Section numbering no gaps / no duplicates. | ☐ |
| C3-06 | Unit display: Currency symbol position ($123.45 always, never 123.45$), thousands separator, decimal mark consistent per target locale (en_US). | Spot check 30 numeric displays. | All numbers formatted with a single Intl.NumberFormat locale. No mid-report flips. | ☐ |
| C3-07 | Error message / label / UI copy writing style: Active voice, similar sentence length, "Action + Object" pattern. | Review 20 error messages / labels. | All messages actionable. 0 passive voice. 0 "An error occurred" without specific code. | ☐ |
| C3-08 | File format consistency: All images same format (PNG for UI screenshots, JPEG for photos). All deliverables PDF/A-3 for long-term archiving where applicable. | `file` utility scan all assets. | 0 random BMP / TIFF / ancient formats. All PDF = PDF/A or PDF 1.7+ tagged. | ☐ |
| C3-09 | Accessibility features uniformly applied: Alt text on every image (no empty alt="" except decorative images), keyboard focus ring visible on ALL interactive elements, color-contrast ratio tested on 5 representative screens. | Sample audit: 10% of pages / screens / panels. | 0 gaps in alt text. 0 "can't tab to this button" issues. | ☐ |
| C3-10 | Dependency versions: All libraries pinned (exact versions). No >= or * in dependency manifests. All build toolchains locked (lockfile commit). | Review requirements.txt / package-lock.json / Cargo.lock. | 100% pinned. Builds reproducible via lockfile. | ☐ |
| C3-11 | Logging / audit format: All log entries use ISO 8601 UTC timestamps, trace_id propagation, severity level (FATAL/ERROR/WARN/INFO/DEBUG) first field. | Sample 50 log lines from staging. Parse with JSON parser. | 100% parse correctly. 0 hand-formatted multi-line stack traces breaking JSON. | ☐ |
| C3-12 | Consistency sign-off: Design Lead / Documentation Lead / Drafting Manager signs. | Consistency Review Report. Signature. | "All deliverables in this package are visually and semantically consistent per Section III criteria." | ☐ |

---

### Section IV: Clarity (C-4) — 10 Checks

| ID | Check | Verification Method | PASS Criteria | Status ☐/☑ |
|----|-------|---------------------|---------------|-------------|
| C4-01 | Glossary of terms: All domain-specific words defined upfront. Target audience = intended reader (no expert-only jargon without definition). | Read glossary. Count industry-specific terms in document. | 100% of technical / specialized terms appear in glossary on first use. | ☐ |
| C4-02 | All abbreviations + acronyms spelled out on FIRST occurrence with abbreviation in parentheses: "Internal Rate of Return (IRR)" not just "IRR". On second use: OK to use IRR alone. | Grep 100+ common acronyms. Check first occurrence. | 0 undefined acronyms. (Exception: common English acronyms OK: USA, PDF, URL) | ☐ |
| C4-03 | Step-by-step instructions: Numbered steps, not bullets. Action verb first: "Click **Login**" not "Login is done via clicking the button". One action per step. | Sample 5 instruction sequences. Walk them with a naive user (intern). | Naive user completes all 5 sequences in < 2× documented expected time. 0 calls for help. | ☐ |
| C4-04 | All assumptions explicitly listed. Example: "This analysis assumes risk-free rate = 4.5% (US Treasury 10Y 2026-08-30 close)". "This campaign assumes CPM = $25 on Meta Audience Network." | Assumptions section. Trace every numerical parameter → source. | No "magic numbers" floating in text. Reader can reproduce ALL calculations from assumptions alone. | ☐ |
| C4-05 | Known limitations + caveats clearly called out. NOT buried in footnotes. Prominent call-out box. | "Known limitations / Caveats" section, same prominence as Results. | 0 caveats only in 8pt font footer. All limitations read by target persona without scrolling to page 47 of 48. | ☐ |
| C4-06 | Logical flow: Table of Contents → Introduction → Background → Method → Results → Discussion → Conclusion → Recommendations → Appendix → References. Equivalent for non-research projects (SOW → Plan → Execute → Verify → Close). | Read TOC, read each section's first + last paragraph. | Story arc clear. No jumping back and forth. | ☐ |
| C4-07 | "If X then Y else Z" decision trees explicit (not implied). Troubleshooting / FAQ section present (§2.3.1 Troubleshooting F-001 to F-010 for software; equivalent Q&A section for events: "What if it rains? → Move to Hall B"). | Count ambiguous paragraphs (ask 3 readers what happens in case X). All 3 agree = clear. Otherwise rewrite. | < 5% of paragraphs result in split reader interpretation. | ☐ |
| C4-08 | Plain language / Plain English: Avoid passive voice, avoid jargon where plain word works. Keep Flesch-Kincaid Grade Level ≤ 10 (8th-grade reading level) for user-facing docs. | Run Flesch-Kincaid score on user manual. | Score ≤ 10.0. Any sentence > 35 words split into 2 sentences. | ☐ |
| C4-09 | Visual cues for severity: Green (OK) / Yellow (Warning) / Red (Critical) — consistently used throughout UI, reports, dashboards. | Sample 20 status indicators. | No "red background for positive result" cultural misalignment. | ☐ |
| C4-10 | Index / Searchable keywords: Document index at back (long documents) OR SEO meta-description + document title (web properties) OR searchable PDF with embedded OCR layer (scanned engineering drawings). | Search for 10 key terms. Index page numbers correct. | 10/10 terms found on first try at correct page. | ☐ |

---

## FINAL SIGN-OFF ON 4-C FRAMEWORK

```
UNIVERSAL PROJECT FINALIZATION GATE — 4-C QUALITY CERTIFICATE

I, ___________________________________, acting in the capacity of
Project Closure Manager / Delivery Lead for ___________________________________
(Project Name, Version, Date),

DO HEREBY CERTIFY AND ATTEST that:

[  ] SECTION I:   COMPLETENESS — 32 / 32 checks PASS
[  ] SECTION II:  CORRECTNESS  — 16 / 16 checks PASS
[  ] SECTION III: CONSISTENCY  — 12 / 12 checks PASS
[  ] SECTION IV:  CLARITY      — 10 / 10 checks PASS

TOTAL: 70 / 70 UNIVERSAL CHECKS PASSED.

The above project is hereby QUALIFIED and ELIGIBLE for formal closure
and handover to the receiving organization. All acceptance criteria
have been met. All open items have been triaged. All signatures on the
Stakeholder Handover Kit (§2.6) have been obtained.

Signed: ________________________________    Date: _______________________
Printed Name: _____________________________
Title: ___________________________________
Witnessed by: _____________________________    Date: _______________________
```

---

### APPENDIX: MAPPING BACK TO BEDAANWAVES SOFTWARE (§2.1 — §2.7)

Every BedaanWaves v2.0.0 closure section maps to the 4-C framework:

| BedaanWaves § | Maps to Universal 4-C Section |
|---------------|-------------------------------|
| §2.1 Final QA Sign-off | C1-19, C1-20, C1-21, C1-22, C1-23, C1-24 (Completeness + Correctness) |
| §2.2 Code & Asset Hardening | C2-07 (secrets), C3-01 (naming), C3-10 (dep pinning) |
| §2.3 Documentation | C4-01 … C4-10 (Clarity) + C3-05 (format consistency) |
| §2.4 Delivery Packaging + CHANGELOG | C1-03 (CHANGELOG), C1-08 (folder structure), C1-09 (checksums) |
| §2.5 Risk Mitigation + Rollback | C1-25 (top-3 risks + rollback) |
| §2.6 Handover Kit + Punch-list | C1-28 (signatures), C1-29 (exec summary), full punch list = all Cs |
| (Implicit in build pipeline) | C2-06 (reproducibility: lockfiles, deterministic zip) |

---
*Document ID: BW-UNIVERSAL-CLOSURE-v2.0.0 · Retain indefinitely in PMO best-practices library.*
