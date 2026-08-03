import { t } from "./i18n";

describe("i18n function", () => {
  beforeEach(() => {
    if (typeof window !== "undefined") {
      localStorage.clear();
    }
  });

  it("should return English translation by default", () => {
    expect(t("app.title")).toBe("BedaanWaves");
    expect(t("auth.login")).toBe("Login");
  });

  it("should return Persian translation when lang=fa", () => {
    if (typeof window !== "undefined") {
      localStorage.setItem("lang", "fa");
      expect(t("app.title")).toBe("بیدان ویبس");
      expect(t("auth.login")).toBe("ورود");
    }
  });

  it("should fallback to key if translation not found", () => {
    expect(t("nonexistent.key")).toBe("nonexistent.key");
  });
});