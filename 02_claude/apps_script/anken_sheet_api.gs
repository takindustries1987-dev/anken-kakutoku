/**
 * 案件探索ツール Sheet API (Google Apps Script Web App)
 *
 * GET  ?action=settings → 「条件設定」タブをJSONで返す
 * POST { action:"append", secret:"...", rows:[[...]] } → 「案件一覧」に追記
 */

const SHEET_ID = '1LrLqdK_eudw6aND1umx-B203nOq7XFP2i9MkJuTkc0A';
const SETTINGS_TAB = '条件設定';
const CANDIDATES_TAB = '案件一覧';

function getSecret_() {
  return PropertiesService.getScriptProperties().getProperty('SHARED_SECRET') || '';
}

/** 手動実行用: 書き込み権限のOAuth承認をトリガーする */
function testWrite() {
  const sheet = SpreadsheetApp.openById(SHEET_ID).getSheetByName(CANDIDATES_TAB);
  sheet.getRange(sheet.getLastRow() + 1, 1, 1, 2).setValues([['AUTH_TEST', new Date().toISOString()]]);
}

function jsonOut_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

function doGet(e) {
  e = e || { parameter: {} };
  const action = (e.parameter.action || 'settings');
  if (action !== 'settings') {
    return jsonOut_({error: 'unknown action'});
  }
  const sheet = SpreadsheetApp.openById(SHEET_ID).getSheetByName(SETTINGS_TAB);
  if (!sheet) return jsonOut_({error: 'settings tab not found'});

  const values = sheet.getDataRange().getValues();
  const settings = {platforms: {}};
  let inPlatformSection = false;

  for (let i = 1; i < values.length; i++) {
    const item = values[i][0];
    const val = values[i][1];
    if (!item) continue;
    if (item === '対象プラットフォーム') {
      inPlatformSection = true;
      continue;
    }
    if (inPlatformSection) {
      settings.platforms[String(item)] = (String(val).trim() === 'はい');
    } else {
      settings[String(item)] = val;
    }
  }
  return jsonOut_(settings);
}

function doPost(e) {
  e = e || { postData: { contents: '{}' } };
  let body;
  try {
    body = JSON.parse(e.postData.contents);
  } catch (err) {
    return jsonOut_({error: 'invalid json'});
  }
  if ((body.secret || '') !== getSecret_()) {
    return jsonOut_({error: 'unauthorized'});
  }
  if (body.action !== 'append') {
    return jsonOut_({error: 'unknown action'});
  }
  const rows = body.rows;
  if (!Array.isArray(rows) || rows.length === 0) {
    return jsonOut_({error: 'rows is empty'});
  }
  const sheet = SpreadsheetApp.openById(SHEET_ID).getSheetByName(CANDIDATES_TAB);
  if (!sheet) return jsonOut_({error: 'candidates tab not found'});

  const startRow = sheet.getLastRow() + 1;
  sheet.getRange(startRow, 1, rows.length, rows[0].length).setValues(rows);
  return jsonOut_({ok: true, appended: rows.length, startRow: startRow});
}
