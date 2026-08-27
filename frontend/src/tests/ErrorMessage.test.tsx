import { render, screen, fireEvent } from '@testing-library/react';
import { ErrorMessage } from '@/components/ui/ErrorMessage';

describe('ErrorMessage', () => {
  it('renders the error message text', () => {
    render(
      <ErrorMessage message="This email is not registered." />,
    );
    expect(screen.getByText('This email is not registered.')).not.toBeNull();
  });

  it('renders action buttons with actionable solutions', () => {
    const onRetry = vi.fn();
    const onCancel = vi.fn();

    render(
      <ErrorMessage
        message="Something went wrong."
        actions={[
          { label: 'Retry', onAction: onRetry },
          { label: 'Back to start', onAction: onCancel },
        ]}
      />,
    );

    const retryBtn = screen.getByRole('button', { name: 'Retry' });
    const cancelBtn = screen.getByRole('button', { name: 'Back to start' });
    expect(retryBtn).not.toBeNull();
    expect(cancelBtn).not.toBeNull();

    fireEvent.click(retryBtn);
    expect(onRetry).toHaveBeenCalledTimes(1);

    fireEvent.click(cancelBtn);
    expect(onCancel).toHaveBeenCalledTimes(1);
  });

  it('renders the warning icon', () => {
    const { container } = render(
      <ErrorMessage message="Error occurred." />,
    );
    expect(container.querySelector('svg')).not.toBeNull();
  });

  it('renders More Help dialog with step-by-step guide', () => {
    render(
      <ErrorMessage
        message="Error."
        actions={[{ label: 'Retry', onAction: vi.fn() }]}
        moreHelpSteps={[
          'Step 1: Check your email',
          'Step 2: Check internet',
          'Step 3: Contact support',
        ]}
      />,
    );

    const helpButton = screen.getByText('More Help');
    expect(helpButton).not.toBeNull();

    fireEvent.click(helpButton);

    expect(screen.getByText('Step 1: Check your email')).not.toBeNull();
    expect(screen.getByText('Step 2: Check internet')).not.toBeNull();
    expect(screen.getByText('Step 3: Contact support')).not.toBeNull();
    expect(screen.getByText('Got it')).not.toBeNull();
  });

  it('has role alert for accessibility', () => {
    render(<ErrorMessage message="Test error" />);
    expect(screen.getByRole('alert')).not.toBeNull();
  });

  it('does not render More Help when no steps provided', () => {
    render(<ErrorMessage message="Simple error" />);
    expect(screen.queryByText('More Help')).toBeNull();
  });
});
