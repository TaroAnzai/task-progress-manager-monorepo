import { expect, test } from '@playwright/test';

const anonymousUser = {
  id: null,
  name: '',
  email: '',
  is_superuser: false,
  organization_id: null,
  organization_name: null,
  company_id: null,
  access_scopes: [],
};

test.beforeEach(async ({ page }) => {
  await page.route('**/api/sessions/current', async (route) => {
    await route.fulfill({ json: anonymousUser });
  });
});

test('CIHログインとローカルログインを表示し、Redirectフローを開始する', async ({ page }) => {
  await page.goto('/login');

  const cihButton = page.getByRole('button', { name: 'Common Identity Hubでログイン' });
  await expect(cihButton).toBeVisible();
  await expect(page.getByLabel('メールアドレス')).toBeVisible();
  await expect(page.locator('input[type="password"]')).toBeVisible();
  await expect(page.getByRole('button', { name: 'ログイン', exact: true })).toBeVisible();

  const oidcRequest = page.waitForRequest('**/api/sessions/oidc/login');
  await cihButton.click();
  expect((await oidcRequest).url()).toBe('http://127.0.0.1:5175/api/sessions/oidc/login');
});

test('TPM未登録のOIDCユーザーへ案内を表示する', async ({ page }) => {
  await page.goto('/login?oidc_error=user_not_registered');

  await expect(page.getByRole('alertdialog')).toContainText(
    'Task Progress Managerの利用登録がありません'
  );
  await expect(page.getByRole('alertdialog')).toContainText('管理者にお問い合わせください');
});

test('callback後のFlask Sessionからログイン済みユーザーを復元する', async ({ page }) => {
  await page.unroute('**/api/sessions/current');
  await page.route('**/api/sessions/current', async (route) => {
    await route.fulfill({
      json: {
        ...anonymousUser,
        id: 42,
        name: 'CIH User',
        email: 'cih@example.com',
      },
    });
  });

  await page.goto('/');

  await expect(page.getByRole('button', { name: 'ログアウト' })).toBeVisible();
});
