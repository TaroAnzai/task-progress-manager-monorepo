import { expect, test, type Page } from '@playwright/test';

const backendOrigin = process.env.TPM_BACKEND_PUBLIC_ORIGIN ?? 'https://auth.local:5000';

const currentUser = {
  id: 42,
  organization_id: 10,
  organization_name: '開発部',
  company_id: 1,
  name: 'E2Eユーザー',
  email: 'e2e@example.com',
  is_superuser: false,
  access_scopes: [],
};

const existingTask = {
  id: 101,
  title: 'リリース準備',
  description: '代表タスク',
  due_date: '2026-09-30',
  status: 'NOT_STARTED',
  created_by: currentUser.id,
  create_user_name: currentUser.name,
  organization_id: currentUser.organization_id,
  user_access_level: 'FULL',
  has_assigned_objective: false,
};

const mockLoggedInApi = async (page: Page) => {
  await page.route(`${backendOrigin}/sessions/current`, (route) =>
    route.fulfill({ json: currentUser })
  );
  await page.route(`${backendOrigin}/tasks`, async (route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({ json: { tasks: [existingTask] } });
      return;
    }
    await route.fallback();
  });
  await page.route(`${backendOrigin}/tasks/*`, (route) => {
    const taskId = Number(new URL(route.request().url()).pathname.split('/').at(-1));
    route.fulfill({ json: { ...existingTask, id: taskId } });
  });
  await page.route(`${backendOrigin}/objectives/tasks/*`, (route) =>
    route.fulfill({ json: { objectives: [] } })
  );
};

test.beforeEach(async ({ page }) => {
  await mockLoggedInApi(page);
});

test('ログイン済みユーザーがタスク一覧を表示できる', async ({ page }) => {
  await page.goto('/');

  await expect(page.getByText(/E2Eユーザー \(ID: 42\)/)).toBeVisible();
  await expect(page.getByText(/所属組織:\( 開発部\)/)).toBeVisible();
  await expect(page.getByRole('button', { name: 'ログアウト' })).toBeVisible();
  await expect(page.getByRole('heading', { name: existingTask.title })).toBeVisible();
  await expect(page.getByRole('button', { name: 'タスク新規作成' })).toBeVisible();
});

test('タスクを1件作成し、一覧へ反映できる', async ({ page }) => {
  const newTask = {
    ...existingTask,
    id: 202,
    title: 'E2Eで作成したタスク',
    description: 'ブラウザから登録',
    due_date: '2026-10-15',
  };
  let requestBody: unknown;

  await page.route(`${backendOrigin}/tasks`, async (route) => {
    if (route.request().method() !== 'POST') {
      await route.fallback();
      return;
    }
    requestBody = route.request().postDataJSON();
    await route.fulfill({ status: 201, json: { message: 'created', task: newTask } });
  });

  await page.goto('/');
  await page.getByRole('button', { name: 'タスク新規作成' }).click();

  await expect(page.getByRole('dialog')).toBeVisible();
  await expect(page.getByRole('heading', { name: '新規タスク作成' })).toBeVisible();
  await page.getByLabel('タスク名').fill(newTask.title);
  await page.getByLabel('タスクの説明').fill(newTask.description);
  await page.getByLabel('期限').fill(newTask.due_date);
  await page.getByRole('button', { name: '作成', exact: true }).click();

  await expect.poll(() => requestBody).toEqual({
    title: newTask.title,
    description: newTask.description,
    due_date: newTask.due_date,
  });
  await expect(page.getByRole('heading', { name: newTask.title })).toBeVisible();
});
