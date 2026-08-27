import { render, screen } from '@testing-library/react';
import { ProgressBar } from '@/components/ui/ProgressBar';

describe('ProgressBar', () => {
  it('renders step count and percentage', () => {
    render(<ProgressBar currentStep={2} totalSteps={4} />);

    expect(screen.getByText('Step 2 of 4')).not.toBeNull();
    expect(screen.getByText('33%')).not.toBeNull();
  });

  it('renders progress bar with correct aria attributes', () => {
    render(<ProgressBar currentStep={1} totalSteps={3} />);

    const progressBar = screen.getByRole('progressbar');
    expect(progressBar).toHaveAttribute('aria-valuenow', '33');
    expect(progressBar).toHaveAttribute('aria-valuemin', '0');
    expect(progressBar).toHaveAttribute('aria-valuemax', '100');
  });

  it('renders step indicators with correct count', () => {
    const { container } = render(<ProgressBar currentStep={2} totalSteps={4} />);
    const steps = container.querySelectorAll('span[class*="rounded-full"]');
    // The rounded-full spans are the step indicators
    expect(steps.length).toBe(4);
  });

  it('marks current step with aria-current', () => {
    render(<ProgressBar currentStep={3} totalSteps={5} />);
    const withAriaCurrent = document.querySelector('[aria-current="step"]');
    expect(withAriaCurrent).not.toBeNull();
  });

  it('uses step labels when provided', () => {
    render(
      <ProgressBar
        currentStep={2}
        totalSteps={4}
        stepLabels={['Welcome', 'Enter email', 'Confirm', 'Done']}
      />,
    );
    expect(screen.getByText('Enter email')).not.toBeNull();
  });

  it('handles currentStep beyond totalSteps (clamps)', () => {
    render(<ProgressBar currentStep={99} totalSteps={4} />);
    expect(screen.getByText('Step 4 of 4')).not.toBeNull();
    expect(screen.getByText('100%')).not.toBeNull();
  });

  it('handles currentStep = 0 (clamps to 1)', () => {
    render(<ProgressBar currentStep={0} totalSteps={4} />);
    expect(screen.getByText('Step 1 of 4')).not.toBeNull();
  });
});
