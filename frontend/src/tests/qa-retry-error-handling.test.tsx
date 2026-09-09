import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { ErrorMessage } from "@/components/ui/ErrorMessage";

describe("QA Priority 1 - Retry & Error Handling", () => {
  it("renders retry button with correct label", () => {
    render(
      <ErrorMessage
        message="Service unavailable"
        actions={[{ label: "Retry", onAction: () => {} }]}
      />,
    );
    expect(screen.getByRole("button", { name: /retry/i })).toBeInTheDocument();
  });

  it("calls onAction when retry button is clicked", () => {
    const onAction = vi.fn();
    render(
      <ErrorMessage
        message="Service unavailable"
        actions={[{ label: "Retry", onAction }]}
      />,
    );

    screen.getByRole("button", { name: /retry/i }).click();
    expect(onAction).toHaveBeenCalledTimes(1);
  });

  it("renders error icon for accessibility", () => {
    render(<ErrorMessage message="Error occurred" />);
    const alert = screen.getByRole("alert");
    expect(alert).toBeInTheDocument();
    expect(alert).toHaveTextContent("Error occurred");
  });

  it("renders help steps when provided", async () => {
    render(
      <ErrorMessage
        message="Error"
        helpTitle="Troubleshooting"
        moreHelpSteps={["Step 1", "Step 2"]}
      />,
    );
    const helpButton = screen.getByLabelText("Troubleshooting");
    expect(helpButton).toBeInTheDocument();
    helpButton.click();
    expect(await screen.findByText("Step 1")).toBeInTheDocument();
    expect(await screen.findByText("Step 2")).toBeInTheDocument();
  });

  it("shows More Help button when help steps exist", () => {
    render(
      <ErrorMessage
        message="Error"
        moreHelpSteps={["Check connection"]}
      />,
    );
    expect(screen.getByRole("button", { name: /show step-by-step help/i })).toBeInTheDocument();
  });
});
