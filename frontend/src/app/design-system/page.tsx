"use client";

import { useState } from "react";
import { NewDashboardShell } from "@/components/layout/NewDashboardShell";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { InputField } from "@/components/ui/InputField";
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@/components/ui/Table";
import { Modal } from "@/components/ui/Modal";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { Spinner } from "@/components/ui/Spinner";
import { ErrorMessage } from "@/components/ui/ErrorMessage";

const colors = [
  { name: "Primary", var: "--color-primary", value: "#005A9C" },
  { name: "Primary Hover", var: "--color-primary-hover", value: "#004578" },
  { name: "Primary Light", var: "--color-primary-light", value: "#E6F0FA" },
  { name: "Secondary", var: "--color-secondary", value: "#64748B" },
  { name: "Success", var: "--color-success", value: "#22C55E" },
  { name: "Warning", var: "--color-warning", value: "#F59E0B" },
  { name: "Error", var: "--color-error", value: "#EF4444" },
  { name: "Background", var: "--color-background", value: "#F8FAFC" },
  { name: "Surface", var: "--color-surface", value: "#FFFFFF" },
  { name: "Text Primary", var: "--color-text-primary", value: "#0F172A" },
  { name: "Text Secondary", var: "--color-text-secondary", value: "#64748B" },
  { name: "Border", var: "--color-border", value: "#E2E8F0" },
];

const spacingScale = [
  { label: "xs", value: "0.25rem" },
  { label: "sm", value: "0.5rem" },
  { label: "md", value: "0.75rem" },
  { label: "lg", value: "1rem" },
  { label: "xl", value: "1.5rem" },
  { label: "2xl", value: "2rem" },
  { label: "3xl", value: "3rem" },
];

export default function DesignSystemPage() {
  const [modalOpen, setModalOpen] = useState(false);

  return (
    <NewDashboardShell title="Design System">
      <div className="space-y-10">
        <header className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-[var(--color-text-primary)]">Design System</h1>
            <p className="mt-1 text-sm text-[var(--color-text-secondary)]">
              Standard, accessible, and responsive UI components built with CSS custom properties.
            </p>
          </div>
        </header>

        {/* Colors */}
        <section>
          <h2 className="mb-4 text-xl font-semibold text-[var(--color-text-primary)]">1. Color Palette</h2>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {colors.map((color) => (
              <Card key={color.name} padding="sm">
                <div
                  className="h-16 rounded-md mb-3"
                  style={{ backgroundColor: color.value }}
                />
                <p className="text-sm font-semibold text-[var(--color-text-primary)]">{color.name}</p>
                <p className="text-xs text-[var(--color-text-muted)]">{color.var}</p>
                <p className="text-xs text-[var(--color-text-muted)] font-mono">{color.value}</p>
              </Card>
            ))}
          </div>
        </section>

        {/* Typography */}
        <section>
          <h2 className="mb-4 text-xl font-semibold text-[var(--color-text-primary)]">2. Typography Scale</h2>
          <Card>
            <div className="space-y-6">
              <div>
                <h1 className="text-4xl font-bold text-[var(--color-text-primary)]">Heading 1 – The quick brown fox</h1>
                <p className="text-sm text-[var(--color-text-muted)]">2.25rem / 700 / 1.2</p>
              </div>
              <div>
                <h2 className="text-3xl font-semibold text-[var(--color-text-primary)]">Heading 2 – The quick brown fox</h2>
                <p className="text-sm text-[var(--color-text-muted)]">1.875rem / 600 / 1.3</p>
              </div>
              <div>
                <h3 className="text-2xl font-semibold text-[var(--color-text-primary)]">Heading 3 – The quick brown fox</h3>
                <p className="text-sm text-[var(--color-text-muted)]">1.5rem / 600 / 1.4</p>
              </div>
              <div>
                <h4 className="text-xl font-semibold text-[var(--color-text-primary)]">Heading 4 – The quick brown fox</h4>
                <p className="text-sm text-[var(--color-text-muted)]">1.25rem / 600 / 1.4</p>
              </div>
              <div>
                <p className="text-base text-[var(--color-text-primary)]">
                  Body text – The quick brown fox jumps over the lazy dog. This is an example of body text used throughout the application.
                </p>
                <p className="text-sm text-[var(--color-text-muted)]">1.0rem / 400 / 1.6</p>
              </div>
              <div>
                <p className="text-sm text-[var(--color-text-primary)]">Small text – The quick brown fox jumps over the lazy dog.</p>
                <p className="text-sm text-[var(--color-text-muted)]">0.875rem / 400 / 1.5</p>
              </div>
              <div>
                <p className="text-xs text-[var(--color-text-primary)]">Caption text – The quick brown fox jumps over the lazy dog.</p>
                <p className="text-sm text-[var(--color-text-muted)]">0.75rem / 400 / 1.4</p>
              </div>
            </div>
          </Card>
        </section>

        {/* Spacing */}
        <section>
          <h2 className="mb-4 text-xl font-semibold text-[var(--color-text-primary)]">3. Spacing Scale</h2>
          <Card>
            <div className="flex flex-wrap items-end gap-4">
              {spacingScale.map((space) => (
                <div key={space.label} className="flex flex-col items-center gap-2">
                  <div
                    className="bg-[var(--color-primary)] rounded"
                    style={{ width: space.value, height: space.value }}
                  />
                  <span className="text-xs text-[var(--color-text-secondary)]">{space.label}</span>
                  <span className="text-[10px] text-[var(--color-text-muted)] font-mono">{space.value}</span>
                </div>
              ))}
            </div>
          </Card>
        </section>

        {/* Buttons */}
        <section>
          <h2 className="mb-4 text-xl font-semibold text-[var(--color-text-primary)]">4. Buttons</h2>
          <Card>
            <div className="space-y-6">
              <div>
                <p className="text-sm text-[var(--color-text-secondary)] mb-3">Variants</p>
                <div className="flex flex-wrap gap-3">
                  <Button variant="primary">Primary</Button>
                  <Button variant="secondary">Secondary</Button>
                  <Button variant="outline">Outline</Button>
                  <Button variant="ghost">Ghost</Button>
                  <Button variant="destructive">Destructive</Button>
                </div>
              </div>
              <div>
                <p className="text-sm text-[var(--color-text-secondary)] mb-3">Sizes</p>
                <div className="flex flex-wrap items-center gap-3">
                  <Button size="sm">Small</Button>
                  <Button size="md">Medium</Button>
                  <Button size="lg">Large</Button>
                </div>
              </div>
              <div>
                <p className="text-sm text-[var(--color-text-secondary)] mb-3">States</p>
                <div className="flex flex-wrap gap-3">
                  <Button>Default</Button>
                  <Button disabled>Disabled</Button>
                  <Button variant="outline" disabled>Disabled Outline</Button>
                </div>
              </div>
            </div>
          </Card>
        </section>

        {/* Inputs */}
        <section>
          <h2 className="mb-4 text-xl font-semibold text-[var(--color-text-primary)]">5. Form Inputs</h2>
          <Card>
            <div className="max-w-2xl space-y-5">
              <InputField
                label="Full Name"
                placeholder="John Doe"
                helpText="Enter your full legal name"
              />
              <InputField
                label="Email Address"
                type="email"
                placeholder="john@example.com"
                helpText="We will never share your email"
              />
              <InputField
                label="With Error"
                validationState="invalid"
                validationMessage="This field contains an error."
                defaultValue="Invalid value"
              />
              <InputField
                label="Disabled"
                disabled
                defaultValue="Cannot edit"
              />
            </div>
          </Card>
        </section>

        {/* Progress */}
        <section>
          <h2 className="mb-4 text-xl font-semibold text-[var(--color-text-primary)]">6. Progress</h2>
          <Card>
            <div className="max-w-xl space-y-6">
              <ProgressBar currentStep={2} totalSteps={4} stepLabels={["Setup", "Configure", "Review", "Launch"]} />
              <div className="flex items-center gap-3">
                <Spinner size="sm" />
                <Spinner size="md" />
                <Spinner size="lg" />
              </div>
            </div>
          </Card>
        </section>

        {/* Badges */}
        <section>
          <h2 className="mb-4 text-xl font-semibold text-[var(--color-text-primary)]">7. Badges</h2>
          <Card>
            <div className="flex flex-wrap gap-3">
              <Badge variant="default">Default</Badge>
              <Badge variant="success">Success</Badge>
              <Badge variant="error">Error</Badge>
              <Badge variant="warning">Warning</Badge>
              <Badge variant="info">Info</Badge>
              <Badge variant="neutral">Neutral</Badge>
            </div>
            <div className="flex flex-wrap gap-3 mt-4">
              <Badge variant="default" size="sm">Small</Badge>
              <Badge variant="default" size="md">Medium</Badge>
            </div>
          </Card>
        </section>

        {/* Table */}
        <section>
          <h2 className="mb-4 text-xl font-semibold text-[var(--color-text-primary)]">8. Tables</h2>
          <Card>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Symbol</TableHead>
                  <TableHead>Name</TableHead>
                  <TableHead numeric>Price</TableHead>
                  <TableHead numeric>Change</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                <TableRow>
                  <TableCell className="font-medium">AAPL</TableCell>
                  <TableCell>Apple Inc.</TableCell>
                  <TableCell numeric>$178.45</TableCell>
                  <TableCell numeric><Badge variant="success">+2.3%</Badge></TableCell>
                  <TableCell><Badge variant="default">Active</Badge></TableCell>
                </TableRow>
                <TableRow>
                  <TableCell className="font-medium">MSFT</TableCell>
                  <TableCell>Microsoft Corp.</TableCell>
                  <TableCell numeric>$415.20</TableCell>
                  <TableCell numeric><Badge variant="error">-1.1%</Badge></TableCell>
                  <TableCell><Badge variant="default">Active</Badge></TableCell>
                </TableRow>
                <TableRow>
                  <TableCell className="font-medium">GOOGL</TableCell>
                  <TableCell>Alphabet Inc.</TableCell>
                  <TableCell numeric>$175.10</TableCell>
                  <TableCell numeric><Badge variant="warning">0.0%</Badge></TableCell>
                  <TableCell><Badge variant="neutral">Pending</Badge></TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </Card>
        </section>

        {/* Modal Trigger */}
        <section>
          <h2 className="mb-4 text-xl font-semibold text-[var(--color-text-primary)]">9. Modal</h2>
          <Button onClick={() => setModalOpen(true)}>Open Modal</Button>
          <Modal
            isOpen={modalOpen}
            onClose={() => setModalOpen(false)}
            title="Confirm Action"
            description="Please review the details before confirming."
            footer={
              <>
                <Button variant="ghost" onClick={() => setModalOpen(false)}>Cancel</Button>
                <Button onClick={() => setModalOpen(false)}>Confirm</Button>
              </>
            }
          >
            <p className="text-sm text-[var(--color-text-secondary)]">
              Are you sure you want to proceed? This action cannot be undone.
            </p>
          </Modal>
        </section>

        {/* Error Message */}
        <section>
          <h2 className="mb-4 text-xl font-semibold text-[var(--color-text-primary)]">10. Error Message</h2>
          <ErrorMessage
            message="Something went wrong. Please try again."
            actions={[{ label: "Retry", onAction: () => {} }]}
            helpTitle="Troubleshooting steps"
            moreHelpSteps={["Check your connection", "Verify your input", "Contact support"]}
          />
        </section>
      </div>
    </NewDashboardShell>
  );
}
