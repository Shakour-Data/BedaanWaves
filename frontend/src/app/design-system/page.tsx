"use client";

import { useState } from "react";

export default function DesignSystemPage() {
  const [modalOpen, setModalOpen] = useState(false);
  const [toastVisible, setToastVisible] = useState(false);

  return (
    <div className="min-h-screen bg-[var(--color-background)]">
      <header className="navbar">
        <span className="navbar-brand">Design System</span>
        <div className="navbar-actions">
          <button
            className="btn btn-ghost btn-md"
            onClick={() => setToastVisible(true)}
          >
            Show Toast
          </button>
        </div>
      </header>

      <main className="container py-8 space-y-12">
        {/* Page Header */}
        <section className="page-header">
          <h1>Design System Showcase</h1>
          <p>
            Standard, beautiful, and universal UI components for web applications.
            Built with CSS custom properties, accessible by default, and responsive
            across all breakpoints.
          </p>
        </section>

        {/* Colors */}
        <section>
          <h2 className="mb-4">1. Color Palette</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
            {[
              { name: "Primary", var: "--color-primary" },
              { name: "Primary Hover", var: "--color-primary-hover" },
              { name: "Secondary", var: "--color-secondary" },
              { name: "Success", var: "--color-success" },
              { name: "Warning", var: "--color-warning" },
              { name: "Error", var: "--color-error" },
              { name: "Background", var: "--color-background" },
              { name: "Surface", var: "--color-surface" },
              { name: "Text Primary", var: "--color-text-primary" },
              { name: "Text Secondary", var: "--color-text-secondary" },
              { name: "Border", var: "--color-border" },
            ].map((color) => (
              <div key={color.name} className="card">
                <div
                  className="h-16 rounded-md mb-2"
                  style={{ backgroundColor: `var(${color.var})` }}
                />
                <p className="text-sm font-medium">{color.name}</p>
                <p className="text-xs text-[var(--color-text-secondary)]">
                  {color.var}
                </p>
              </div>
            ))}
          </div>
        </section>

        {/* Typography */}
        <section>
          <h2 className="mb-4">2. Typography Scale</h2>
          <div className="card space-y-4">
            <div>
              <h1>Heading 1 – The quick brown fox jumps over the lazy dog</h1>
              <p className="text-sm text-[var(--color-text-secondary)]">
                2.5rem / 700 / 1.2
              </p>
            </div>
            <div>
              <h2>Heading 2 – The quick brown fox jumps over the lazy dog</h2>
              <p className="text-sm text-[var(--color-text-secondary)]">
                2.0rem / 600 / 1.3
              </p>
            </div>
            <div>
              <h3>Heading 3 – The quick brown fox jumps over the lazy dog</h3>
              <p className="text-sm text-[var(--color-text-secondary)]">
                1.5rem / 600 / 1.4
              </p>
            </div>
            <div>
              <h4>Heading 4 – The quick brown fox jumps over the lazy dog</h4>
              <p className="text-sm text-[var(--color-text-secondary)]">
                1.25rem / 600 / 1.4
              </p>
            </div>
            <div>
              <p className="text-base">
                Body text – The quick brown fox jumps over the lazy dog. This is
                an example of body text used throughout the application. It
                should be readable and comfortable for long-form content.
              </p>
              <p className="text-sm text-[var(--color-text-secondary)]">
                1.0rem / 400 / 1.6
              </p>
            </div>
            <div>
              <p className="text-sm">
                Small text – The quick brown fox jumps over the lazy dog.
              </p>
              <p className="text-sm text-[var(--color-text-secondary)]">
                0.875rem / 400 / 1.5
              </p>
            </div>
            <div>
              <p className="text-xs">
                Caption text – The quick brown fox jumps over the lazy dog.
              </p>
              <p className="text-xs text-[var(--color-text-secondary)]">
                0.75rem / 400 / 1.4
              </p>
            </div>
          </div>
        </section>

        {/* Spacing */}
        <section>
          <h2 className="mb-4">3. Spacing Scale</h2>
          <div className="card flex flex-wrap gap-4">
            {[
              { label: "xs", value: "var(--spacing-xs)" },
              { label: "sm", value: "var(--spacing-sm)" },
              { label: "md", value: "var(--spacing-md)" },
              { label: "lg", value: "var(--spacing-lg)" },
              { label: "xl", value: "var(--spacing-xl)" },
              { label: "2xl", value: "var(--spacing-2xl)" },
              { label: "3xl", value: "var(--spacing-3xl)" },
            ].map((space) => (
              <div key={space.label} className="flex flex-col items-center gap-2">
                <div
                  className="bg-[var(--color-primary)] rounded"
                  style={{ width: space.value, height: space.value }}
                />
                <span className="text-xs text-[var(--color-text-secondary)]">
                  {space.label}
                </span>
              </div>
            ))}
          </div>
        </section>

        {/* Buttons */}
        <section>
          <h2 className="mb-4">4. Buttons</h2>
          <div className="card space-y-6">
            <div>
              <p className="text-sm text-[var(--color-text-secondary)] mb-3">
                Variants
              </p>
              <div className="flex flex-wrap gap-3">
                <button className="btn btn-primary btn-md">Primary</button>
                <button className="btn btn-secondary btn-md">
                  Secondary
                </button>
                <button className="btn btn-ghost btn-md">Ghost</button>
                <button className="btn btn-destructive btn-md">
                  Destructive
                </button>
              </div>
            </div>
            <div>
              <p className="text-sm text-[var(--color-text-secondary)] mb-3">
                Sizes
              </p>
              <div className="flex flex-wrap items-center gap-3">
                <button className="btn btn-primary btn-md">Medium</button>
                <button className="btn btn-primary btn-lg">Large</button>
              </div>
            </div>
            <div>
              <p className="text-sm text-[var(--color-text-secondary)] mb-3">
                States
              </p>
              <div className="flex flex-wrap gap-3">
                <button className="btn btn-primary btn-md">Default</button>
                <button className="btn btn-primary btn-md" disabled>
                  Disabled
                </button>
                <button className="btn btn-primary btn-md btn-loading">
                  Processing...
                </button>
              </div>
            </div>
          </div>
        </section>

        {/* Inputs */}
        <section>
          <h2 className="mb-4">5. Form Inputs</h2>
          <div className="card space-y-6 max-w-2xl">
            <div className="form-group">
              <label className="form-label" htmlFor="name">
                Full Name
              </label>
              <input
                id="name"
                className="form-input"
                placeholder="John Doe"
                type="text"
              />
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="email">
                Email Address
              </label>
              <input
                id="email"
                className="form-input"
                placeholder="john@example.com"
                type="email"
              />
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="message">
                Message
              </label>
              <textarea
                id="message"
                className="form-textarea"
                placeholder="Write your message here..."
                rows={4}
              />
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="error-input">
                With Error
              </label>
              <input
                id="error-input"
                className="form-input error"
                defaultValue="Invalid value"
                type="text"
              />
              <p className="form-error-message">
                This field contains an error.
              </p>
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="success-input">
                With Success
              </label>
              <div className="relative">
                <input
                  id="success-input"
                  className="form-input success"
                  defaultValue="Valid value"
                  type="text"
                />
                <span className="form-success-icon">
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <path d="M20 6 9 17l-5-5" />
                  </svg>
                </span>
              </div>
            </div>
          </div>
        </section>

        {/* Cards */}
        <section>
          <h2 className="mb-4">6. Cards</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="card">
              <div className="card-header">
                <h3 className="text-lg font-semibold">Standard Card</h3>
              </div>
              <div className="card-body">
                <p className="text-sm text-[var(--color-text-secondary)]">
                  This is a standard card with a border, shadow, and consistent
                  padding.
                </p>
              </div>
              <div className="card-footer">
                <button className="btn btn-ghost btn-sm">Cancel</button>
                <button className="btn btn-primary btn-sm">Action</button>
              </div>
            </div>
            <div className="card card-borderless">
              <div className="card-body">
                <h3 className="text-lg font-semibold mb-2">
                  Borderless Card
                </h3>
                <p className="text-sm text-[var(--color-text-secondary)]">
                  This card has no border, only a shadow for elevation.
                </p>
              </div>
            </div>
            <div className="card">
              <div className="card-body">
                <h3 className="text-lg font-semibold mb-2">Stat Card</h3>
                <p className="text-3xl font-bold">$45,231</p>
                <span className="badge badge-success badge-md mt-2">
                  +12.5%
                </span>
              </div>
            </div>
          </div>
        </section>

        {/* Modal */}
        <section>
          <h2 className="mb-4">7. Modal / Dialog</h2>
          <button
            className="btn btn-primary btn-md"
            onClick={() => setModalOpen(true)}
          >
            Open Modal
          </button>
          <div
            className={`modal-overlay ${modalOpen ? "open" : ""}`}
            onClick={() => setModalOpen(false)}
          >
            <div
              className="modal-content modal-md"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="modal-header">
                <h3 className="modal-title">Confirm Action</h3>
                <button
                  className="modal-close"
                  onClick={() => setModalOpen(false)}
                  aria-label="Close modal"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="24"
                    height="24"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <path d="M18 6 6 18" />
                    <path d="m6 6 12 12" />
                  </svg>
                </button>
              </div>
              <div className="modal-body">
                <p className="text-sm text-[var(--color-text-secondary)]">
                  Are you sure you want to proceed? This action cannot be
                  undone. Please review the details before confirming.
                </p>
              </div>
              <div className="modal-footer">
                <button
                  className="btn btn-ghost btn-md"
                  onClick={() => setModalOpen(false)}
                >
                  Cancel
                </button>
                <button
                  className="btn btn-primary btn-md"
                  onClick={() => setModalOpen(false)}
                >
                  Confirm
                </button>
              </div>
            </div>
          </div>
        </section>

        {/* Navigation */}
        <section>
          <h2 className="mb-4">8. Navigation</h2>
          <div className="card">
            <nav className="navbar" style={{ position: "static", boxShadow: "none", borderBottom: "none" }}>
              <span className="navbar-brand">Brand</span>
              <div className="navbar-actions">
                <a href="#" className="sidebar-item" style={{ marginBottom: 0 }}>
                  Dashboard
                </a>
                <a href="#" className="sidebar-item active" style={{ marginBottom: 0 }}>
                  Portfolio
                </a>
                <a href="#" className="sidebar-item" style={{ marginBottom: 0 }}>
                  Settings
                </a>
              </div>
            </nav>
          </div>
        </section>

        {/* Table */}
        <section>
          <h2 className="mb-4">9. Tables</h2>
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Symbol</th>
                  <th>Name</th>
                  <th>Price</th>
                  <th>Change</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td className="font-medium">AAPL</td>
                  <td>Apple Inc.</td>
                  <td>$178.45</td>
                  <td>
                    <span className="badge badge-success badge-sm">+2.3%</span>
                  </td>
                  <td>
                    <span className="badge badge-primary badge-sm">
                      Active
                    </span>
                  </td>
                </tr>
                <tr>
                  <td className="font-medium">MSFT</td>
                  <td>Microsoft Corp.</td>
                  <td>$415.20</td>
                  <td>
                    <span className="badge badge-error badge-sm">-1.1%</span>
                  </td>
                  <td>
                    <span className="badge badge-primary badge-sm">
                      Active
                    </span>
                  </td>
                </tr>
                <tr>
                  <td className="font-medium">GOOGL</td>
                  <td>Alphabet Inc.</td>
                  <td>$175.10</td>
                  <td>
                    <span className="badge badge-warning badge-sm">0.0%</span>
                  </td>
                  <td>
                    <span className="badge badge-neutral badge-sm">
                      Pending
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        {/* Alerts */}
        <section>
          <h2 className="mb-4">10. Alerts</h2>
          <div className="space-y-4">
            <div className="alert alert-info" role="alert">
              <span className="alert-icon" aria-hidden="true">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <circle cx="12" cy="12" r="10" />
                  <path d="M12 16v-4" />
                  <path d="M12 8h.01" />
                </svg>
              </span>
              <span>This is an informational alert message.</span>
            </div>
            <div className="alert alert-success" role="alert">
              <span className="alert-icon" aria-hidden="true">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="M20 6 9 17l-5-5" />
                </svg>
              </span>
              <span>Operation completed successfully.</span>
            </div>
            <div className="alert alert-warning" role="alert">
              <span className="alert-icon" aria-hidden="true">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z" />
                  <path d="M12 9v4" />
                  <path d="M12 17h.01" />
                </svg>
              </span>
              <span>Please review before proceeding.</span>
            </div>
            <div className="alert alert-error" role="alert">
              <span className="alert-icon" aria-hidden="true">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <circle cx="12" cy="12" r="10" />
                  <path d="m15 9-6 6" />
                  <path d="m9 9 6 6" />
                </svg>
              </span>
              <span>An error occurred. Please try again.</span>
            </div>
          </div>
        </section>

        {/* Badges */}
        <section>
          <h2 className="mb-4">11. Badges / Tags</h2>
          <div className="card">
            <div className="flex flex-wrap gap-3">
              <span className="badge badge-primary badge-md">Primary</span>
              <span className="badge badge-success badge-md">Success</span>
              <span className="badge badge-warning badge-md">Warning</span>
              <span className="badge badge-error badge-md">Error</span>
              <span className="badge badge-neutral badge-md">Neutral</span>
            </div>
            <div className="flex flex-wrap gap-3 mt-4">
              <span className="badge badge-primary badge-sm">Small</span>
              <span className="badge badge-primary badge-md">Medium</span>
            </div>
          </div>
        </section>

        {/* Grid System */}
        <section>
          <h2 className="mb-4">12. Responsive Grid System</h2>
          <p className="text-sm text-[var(--color-text-secondary)] mb-4">
            12-column fluid grid with 16px gutters. Resize the browser to see
            responsive behavior.
          </p>
          <div className="grid grid-cols-12 gap-4">
            {Array.from({ length: 12 }).map((_, i) => (
              <div
                key={i}
                className="bg-[var(--color-primary)] text-white rounded-md p-4 text-center text-sm font-medium"
              >
                {i + 1}
              </div>
            ))}
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mt-6">
            {["Column 1", "Column 2", "Column 3", "Column 4"].map((col) => (
              <div
                key={col}
                className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-md p-4 text-center text-sm"
              >
                {col}
              </div>
            ))}
          </div>
        </section>

        {/* Dark Mode Toggle */}
        <section>
          <h2 className="mb-4">13. Dark Mode</h2>
          <button
            className="btn btn-secondary btn-md"
            onClick={() => {
              const current = document.documentElement.getAttribute(
                "data-theme"
              );
              const next = current === "dark" ? "light" : "dark";
              document.documentElement.setAttribute("data-theme", next);
            }}
          >
            Toggle Dark Mode
          </button>
        </section>
      </main>

      {/* Toast */}
      {toastVisible && (
        <div className="toast-container">
          <div className="toast">
            <span className="alert-icon" aria-hidden="true">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                fill="none"
                stroke="var(--color-primary)"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M20 6 9 17l-5-5" />
              </svg>
            </span>
            <span>This is a toast notification.</span>
            <button
              className="alert-close"
              onClick={() => setToastVisible(false)}
              aria-label="Close toast"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M18 6 6 18" />
                <path d="m6 6 12 12" />
              </svg>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
