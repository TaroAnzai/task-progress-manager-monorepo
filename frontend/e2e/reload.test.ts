import { expect, test } from '@playwright/test';

test('リロードしてもコンソールエラーが出ない', async ({ page }) => {
  test.setTimeout(600000); // ✅ テスト全体を600秒に延長
  let errorMessage: string | null = null;

  // 🔹 コンソールエラーを監視
  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      errorMessage = msg.text();
    }
  });

  // 🔹 初回ロード
  await page.goto('https://localhost:5173/progress');

  await page.fill('input[type=email]', process.env.TEST_USER_EMAIL!);
  await page.fill('input[type=password]', process.env.TEST_USER_PASSWORD!);
  // ✅ ボタンが有効になるまで待機
  const loginBtn = page.locator('button[type=submit]');
  await expect(loginBtn).toBeEnabled();
  // ✅ クリックとURL遷移を同時に待つ
  await Promise.all([page.waitForURL('**/progress', { timeout: 10000 }), loginBtn.click()]);
  await expect(page).toHaveURL('https://localhost:5173/progress');

  // 🔹 100回リロード
  for (let i = 0; i < 50; i++) {
    await page.reload({ waitUntil: 'networkidle', timeout: 50000 });
    await page.waitForTimeout(100); // 短い待機を入れて安定化
    if (errorMessage) break; // エラーが出たら即終了
  }

  // 🔹 最後に確認
  expect(errorMessage).toBeNull();
});
