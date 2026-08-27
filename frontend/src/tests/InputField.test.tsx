import { render, screen, fireEvent } from '@testing-library/react';
import { InputField } from '@/components/ui/InputField';

describe('InputField', () => {
  it('renders label and placeholder', () => {
    render(
      <InputField
        label="Email"
        placeholder="you@example.com"
        example="name@domain.com"
        value=""
        onChange={() => {}}
      />,
    );

    expect(screen.getByText('Email')).not.toBeNull();
    expect(screen.getByPlaceholderText('you@example.com')).not.toBeNull();
    expect(screen.getByText(/e.g.*name@domain.com/)).not.toBeNull();
  });

  it('shows validation message when state is invalid', () => {
    render(
      <InputField
        label="Email"
        placeholder="you@example.com"
        value="bad"
        onChange={() => {}}
        validationState="invalid"
        validationMessage="Invalid email format"
      />,
    );

    const msg = screen.getByRole('alert');
    expect(msg).toHaveTextContent('Invalid email format');
  });

  it('shows success icon when valid', () => {
    const { container } = render(
      <InputField
        label="Email"
        placeholder="you@example.com"
        value="good@example.com"
        onChange={() => {}}
        validationState="valid"
        validationMessage="Looks good"
      />,
    );
    expect(container.querySelector('svg')).not.toBeNull();
  });

  it('has aria-invalid when validationState is invalid', () => {
    render(
      <InputField
        label="Email"
        placeholder="you@example.com"
        value=""
        onChange={() => {}}
        validationState="invalid"
        validationMessage="Required"
      />,
    );
    const input = screen.getByRole('textbox');
    expect(input).toHaveAttribute('aria-invalid', 'true');
  });

  it('calls onChange when user types', () => {
    const handleChange = vi.fn();
    render(
      <InputField
        label="Email"
        placeholder="you@example.com"
        value=""
        onChange={handleChange}
      />,
    );
    const input = screen.getByRole('textbox');
    fireEvent.change(input, { target: { value: 'test@test.com' } });
    expect(handleChange).toHaveBeenCalledTimes(1);
  });

  it('links help text via aria-describedby', () => {
    render(
      <InputField
        label="Email"
        placeholder="you@example.com"
        helpText="We never share your email."
        value=""
        onChange={() => {}}
      />,
    );
    const input = screen.getByRole('textbox');
    expect(input).toHaveAttribute('aria-describedby');
  });
});
