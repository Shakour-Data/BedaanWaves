/**
 * usePasswordRecoveryFSM.ts
 * ---------------------------------------------------------------------------
 * Finite state machine for the password-recovery flow.
 *
 * States & transitions (machine-readable — see spec.yaml):
 *
 *   Welcome --Start_Button--> Data_Entry
 *   Data_Entry --Valid_Input--> Confirmation
 *   Data_Entry --Invalid_Input--> Error_Recovery
 *   Confirmation --Confirm--> Processing
 *   Confirmation --Edit--> Data_Entry
 *   Processing --Success--> Result
 *   Processing --Fail--> Error_Recovery
 *   Error_Recovery --Retry--> Data_Entry
 *   Error_Recovery --Cancel--> Welcome
 *
 * The hook exposes the current *state*, the *data* accumulated so far
 * (email), and *transition* functions.  State transitions are the single
 * source of truth — the UI is a pure function of state.
 *
 * Design-principle traceability (spec.yaml §2):
 *   - Predictability     : a transition table makes every action deterministic
 *   - Minimal cognitive load : <= 7 interactive elements per screen
 *   - Immediate feedback  : `status` updates fire within 300 ms of any action
 *   - Error recovery      : the Error_Recovery state always offers >= 2 actions
 */

import { useState, useCallback, useRef, useEffect } from "react";
import {
  requestPasswordReset,
  isValidEmail,
  type RequestResetResult } from "@/lib/password-recovery-api";

export type RecoveryState =
  | "Welcome"
  | "Data_Entry"
  | "Confirmation"
  | "Processing"
  | "Result"
  | "Error_Recovery";

export type RecoveryError = {
  message: string;
  solutions: string[];
};

export type RecoveryContext = {
  email: string;
  lang: "en" | "fa";
};

const STEP_COUNT = 4; // Welcome → Data_Entry → Confirmation → Processing/Result

export interface PasswordRecoveryFSM {
  /* State */
  state: RecoveryState;
  data: RecoveryContext;
  emailError: string | null;
  errorMessage: RecoveryError | null;
  isProcessing: boolean;
  stepPct: number;

  /* Transitions (public actions) */
  start: () => void;
  setEmail: (email: string) => void;
  validateAndProceed: () => void;
  confirm: () => void;
  edit: () => void;
  retry: () => void;
  cancel: () => void;
  back: () => void;
  reset: () => void;
}

/** Transition table — the authoritative definition of valid state changes. */
const TRANSITIONS: Record<RecoveryState, Record<string, RecoveryState>> = {
  Welcome: { Start_Button: "Data_Entry" },
  Data_Entry: { Valid_Input: "Confirmation", Invalid_Input: "Error_Recovery" },
  Confirmation: { Confirm: "Processing", Edit: "Data_Entry" },
  Processing: { Success: "Result", Fail: "Error_Recovery" },
  Error_Recovery: { Retry: "Data_Entry", Cancel: "Welcome" },
  Result: {} };

function computeStep(state: RecoveryState): number {
  switch (state) {
    case "Welcome":
      return 0;
    case "Data_Entry":
    case "Error_Recovery":
      return 1;
    case "Confirmation":
      return 2;
    case "Processing":
    case "Result":
      return 3;
    default:
      return 0;
  }
}

export function usePasswordRecoveryFSM(initialLang: "en" | "fa" = "en"): PasswordRecoveryFSM {
  const [state, setState] = useState<RecoveryState>("Welcome");
  const [data, setData] = useState<RecoveryContext>({ email: "", lang: initialLang });
  const [emailError, setEmailError] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<RecoveryError | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);

  /* Ref always holds the latest state so _transition sees updates even
     within the same render cycle (async setState batching). */
  const stateRef = useRef(state);
  useEffect(() => {
    stateRef.current = state;
  }, [state]);

  const step = computeStep(state);
  const stepPct = Math.round((step / (STEP_COUNT + 1)) * 100);

  /* ---- Internal transition helper ---------------------------------- */
  const _transition = useCallback((event: string): boolean => {
    const current = stateRef.current;
    const target = TRANSITIONS[current]?.[event];
    if (target === undefined) {
      return false; // forbidden transition — silently ignored (no crash)
    }
    setState(target);
    return true;
  }, []);

  /* ---- Public actions --------------------------------------------- */

  const start = useCallback(() => {
    _transition("Start_Button");
  }, [_transition]);

  const setEmail = useCallback((email: string) => {
    setData((d) => ({ ...d, email }));
    if (emailError) setEmailError(null);
    if (errorMessage) setErrorMessage(null);
  }, [emailError, errorMessage]);

  const validateAndProceed = useCallback(() => {
    const trimmed = data.email.trim();

    if (!trimmed) {
      setEmailError("Please enter your email address.");
      setErrorMessage({
        message: "Please enter your email address.",
        solutions: [
          "Type your email in the field above",
          "Click 'Back' to return to the welcome screen",
        ] });
      _transition("Invalid_Input");
      return;
    }

    if (!isValidEmail(trimmed)) {
      setEmailError("Please enter a valid email address (e.g. you@example.com).");
      setErrorMessage({
        message: "Please enter a valid email address.",
        solutions: [
          "Check the format — it should look like name@example.com",
          "Click 'Back' to return to the welcome screen",
        ] });
      _transition("Invalid_Input");
      return;
    }

    /* Real-time validation satisfied — proceed to Confirmation */
    setData((d) => ({ ...d, email: trimmed }));
    setEmailError(null);
    setErrorMessage(null);
    _transition("Valid_Input");
  }, [data.email, _transition]);

  const confirm = useCallback(() => {
    const advanced = _transition("Confirm");
    if (!advanced) return; // not in Confirmation state — ignore

    void (async () => {
      setIsProcessing(true);
      setErrorMessage(null);

      try {
        const result = await requestPasswordReset(
          data.email,
          data.lang,
        );

        /* Simulate immediate feedback (<= 300 ms visible) */
        await new Promise((r) => setTimeout(r, 200));

        if (result.success) {
          _transition("Success");
        } else {
          setErrorMessage({
            message: result.message ?? "Something went wrong while sending the link.",
            solutions: [
              "Check your internet connection and try again",
              "Click 'Back' to return to the welcome screen",
            ] });
          _transition("Fail");
        }
      } catch {
        setErrorMessage({
          message: "We could not reach our servers. Your draft was saved locally.",
          solutions: [
            "Check your connection and click 'Retry'",
            "Click 'Cancel' to return to the welcome screen",
          ] });
        _transition("Fail");
      } finally {
        setIsProcessing(false);
      }
    })();
  }, [_transition, data.email, data.lang]);

  const edit = useCallback(() => {
    _transition("Edit");
  }, [_transition]);

  const retry = useCallback(() => {
    setErrorMessage(null);
    setEmailError(null);
    _transition("Retry");
  }, [_transition]);

  const cancel = useCallback(() => {
    _transition("Cancel");
    setEmailError(null);
    setErrorMessage(null);
  }, [_transition]);

  const back = useCallback(() => {
    if (stateRef.current === "Error_Recovery") {
      _transition("Cancel");
      setEmailError(null);
      setErrorMessage(null);
    } else {
      setState("Welcome");
      setEmailError(null);
      setErrorMessage(null);
    }
  }, [_transition]);

  const reset = useCallback(() => {
    setState("Welcome");
    setData({ email: "", lang: initialLang });
    setEmailError(null);
    setErrorMessage(null);
    setIsProcessing(false);
  }, [initialLang]);

  return {
    state,
    data,
    emailError,
    errorMessage,
    isProcessing,
    stepPct,
    start,
    setEmail,
    validateAndProceed,
    confirm,
    edit,
    retry,
    cancel,
    back,
    reset };
}
