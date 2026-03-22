import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';

test('teacher shell can switch from mock mode to live scoped teacher APIs', () => {
  const src = fs.readFileSync(path.resolve('docs/school-first-teacher/index.html'), 'utf8');

  assert.ok(src.includes("id=\"teacherApiBase\""), 'teacher shell must expose backend base input');
  assert.ok(src.includes("id=\"teacherUsername\""), 'teacher shell must expose teacher username input');
  assert.ok(src.includes("id=\"teacherPassword\""), 'teacher shell must expose teacher password input');
  assert.ok(src.includes("id=\"teacherClassSelect\""), 'teacher shell must expose linked class selector');
  assert.ok(src.includes("id=\"teacherConnectBtn\""), 'teacher shell must expose live connect button');

  assert.ok(src.includes('/v1/app/auth/teacher-session'), 'teacher shell must request a teacher-scoped browser session');
  assert.ok(src.includes('/v1/app/teacher/classes'), 'teacher shell must discover linked classes');
  assert.ok(src.includes('/v1/app/teacher/classes/'), 'teacher shell must call teacher scoped endpoints');
  assert.ok(src.includes('/overview'), 'teacher shell must load live class overview');
  assert.ok(src.includes('/before-after'), 'teacher shell must load live class before-after and student drill-down');
  assert.ok(src.includes('students/'), 'teacher shell must support teacher student drill-down endpoint');
  assert.ok(src.includes("'X-Session-Token'"), 'teacher shell must use session token auth for live teacher reads');

  assert.ok(src.includes("liveState.mode = 'live'"), 'teacher shell must switch into live mode on successful auth');
  assert.ok(src.includes("liveState.mode = 'mock'"), 'teacher shell must fall back to mock mode on failure');
  assert.ok(src.includes('liveState.sessionToken'), 'teacher shell must keep teacher session token instead of raw api key');
  assert.ok(src.includes('mock.getTeacherDashboard'), 'teacher shell must keep mock runtime fallback');
  assert.ok(src.includes('queryParam(\'api\')'), 'teacher shell must support API base from query param');
  assert.ok(src.includes("localStorage.getItem('aimath_parent_report_api_base_v1')"), 'teacher shell should reuse stored backend base when available');
});
