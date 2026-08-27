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
  signup_error_password_match: "Passwords do not match",
};

const fa = {
  login_title: "ورود",
  login_email: "ایمیل",
  login_password: "رمز عبور",
  login_forgot_password: "فراموشی رمز عبور؟",
  login_submit: "ورود",
  login_no_account: "حساب کاربری ندارید؟",
  signup_login_link: "ثبت نام",
  auth_loading: "در حال بارگذاری...",
  auth_error_authentication: "خطا در احراز هویت",
  login_back_to_login: "بازگشت به ورود",
  auth_remember_me: "مرا به خاطر بسپار",
  auth_language: "زبان",
  auth_show_password: "نمایش رمز",
  auth_hide_password: "مخفی کردن رمز",
  signup_title: "ثبت نام",
  signup_name: "نام کامل",
  signup_email: "ایمیل",
  signup_password: "رمز عبور",
  signup_confirm_password: "تکرار رمز عبور",
  signup_submit: "ثبت نام",
  signup_already_have_account: "قبلاً حساب کاربری دارید؟",
  signup_error_password_length: "رمز عبور باید حداقل ۸ کاراکتر باشد",
  signup_error_password_match: "رمزهای عبور مطابقت ندارند",
};

export function useAuthT() {
  const lang = useAuthStore((s) => s.currentLang) ?? "en";
  const dict = lang === "fa" ? fa : en;
  return (key: string): string => dict[key as keyof typeof dict] ?? key;
}
