"use client";

import { useAuthStore } from "@/store/useAuthStore";

const en = {
  login_title: "Login",
  login_email: "Email",
  login_password: "Password",
  login_forgot_password: "Forgot password?",
  login_submit: "Sign in",
  login_no_account: "Don't have an account?",
  signup_login_link: "Sign up",
  auth_loading: "Loading...",
  auth_error_authentication: "Authentication failed",
  login_back_to_login: "Back to login",
  auth_remember_me: "Remember me",
  auth_language: "Language",
  auth_show_password: "Show password",
  auth_hide_password: "Hide password",
  signup_title: "Create Account",
  signup_name: "Full Name",
  signup_email: "Email",
  signup_password: "Password",
  signup_confirm_password: "Confirm Password",
  signup_submit: "Sign Up",
  signup_already_have_account: "Already have an account?",
  signup_error_password_length: "Password must be at least 8 characters",
  signup_error_password_match: "Passwords do not match" };

export function useAuthT() {
  const dict = en;
  return (key: string): string => dict[key as keyof typeof dict] ?? key;
}
