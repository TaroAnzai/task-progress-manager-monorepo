import { fireEvent, render, screen } from '@testing-library/react';
import { Link } from 'react-router-dom';

import App from '@/App';

vi.mock('@/components/layout/Header', () => ({
  Header: () => <Link to="/login">Login</Link>,
}));

vi.mock('@/pages/TaskPage', () => ({ default: () => <div>Task page</div> }));
vi.mock('@/pages/LoginPage', () => ({ default: () => <div>Login page</div> }));

describe('App routing', () => {
  beforeEach(() => {
    window.history.pushState({}, '', '/');
  });

  it('renders the initial lazy-loaded page and navigates to another lazy-loaded page', async () => {
    render(<App />);

    expect(await screen.findByText('Task page')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('link', { name: 'Login' }));

    expect(await screen.findByText('Login page')).toBeInTheDocument();
  });
});
