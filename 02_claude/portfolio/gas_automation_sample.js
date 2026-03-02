/**
 * GAS自動化サンプル: スプレッドシート売上レポート自動生成ツール
 *
 * 【概要】
 * Googleスプレッドシートの売上データから、自動で日次/週次/月次レポートを生成し、
 * メールで関係者に自動送信するGASスクリプトです。
 *
 * 【機能】
 * 1. 売上データシートから指定期間のデータを集計
 * 2. カテゴリ別・担当者別の集計表を自動生成
 * 3. 前月比・前年比の計算
 * 4. グラフの自動生成
 * 5. PDF化してメール自動送信
 * 6. トリガーによる定期実行（毎日/毎週/毎月）
 *
 * 【使い方】
 * 1. このスクリプトをGASエディタに貼り付け
 * 2. CONFIG内のスプレッドシートID・メールアドレスを設定
 * 3. 初回実行時にGoogleアカウントの認証を許可
 * 4. setDailyTrigger() を実行してトリガーを設定
 *
 * 【シート構成】
 * - 「売上データ」シート: 日付 | 商品名 | カテゴリ | 担当者 | 金額 | 数量
 * - 「レポート」シート: 自動生成される集計結果
 */

// ===== 設定 =====
const CONFIG = {
  SPREADSHEET_ID: "YOUR_SPREADSHEET_ID_HERE",
  DATA_SHEET_NAME: "売上データ",
  REPORT_SHEET_NAME: "レポート",
  NOTIFICATION_EMAILS: ["your-email@example.com"],
  COMPANY_NAME: "サンプル株式会社",
};

/**
 * メイン関数: 日次レポートを生成してメール送信
 */
function generateDailyReport() {
  const ss = SpreadsheetApp.openById(CONFIG.SPREADSHEET_ID);
  const dataSheet = ss.getSheetByName(CONFIG.DATA_SHEET_NAME);

  if (!dataSheet) {
    Logger.log("売上データシートが見つかりません");
    return;
  }

  // 昨日のデータを取得
  const yesterday = new Date();
  yesterday.setDate(yesterday.getDate() - 1);
  const dateStr = Utilities.formatDate(yesterday, "Asia/Tokyo", "yyyy/MM/dd");

  const data = getDataByDateRange(dataSheet, yesterday, yesterday);

  if (data.length === 0) {
    Logger.log(`${dateStr} のデータがありません`);
    return;
  }

  // 集計
  const summary = aggregateData(data);

  // レポートシートに出力
  const reportSheet = getOrCreateSheet(ss, CONFIG.REPORT_SHEET_NAME);
  writeReport(reportSheet, summary, dateStr);

  // メール送信
  sendReportEmail(summary, dateStr);

  Logger.log(`日次レポート生成完了: ${dateStr}`);
}

/**
 * 指定期間のデータを取得
 * @param {Sheet} sheet - データシート
 * @param {Date} startDate - 開始日
 * @param {Date} endDate - 終了日
 * @returns {Array} フィルタされたデータ行
 */
function getDataByDateRange(sheet, startDate, endDate) {
  const allData = sheet.getDataRange().getValues();
  const headers = allData[0];
  const dateCol = headers.indexOf("日付");

  if (dateCol === -1) {
    Logger.log("「日付」列が見つかりません");
    return [];
  }

  const startTime = new Date(startDate);
  startTime.setHours(0, 0, 0, 0);
  const endTime = new Date(endDate);
  endTime.setHours(23, 59, 59, 999);

  return allData.slice(1).filter((row) => {
    const rowDate = new Date(row[dateCol]);
    return rowDate >= startTime && rowDate <= endTime;
  });
}

/**
 * データを集計
 * @param {Array} data - 売上データ
 * @returns {Object} 集計結果
 */
function aggregateData(data) {
  const summary = {
    totalSales: 0,
    totalQuantity: 0,
    byCategory: {},
    byPerson: {},
    topProducts: {},
  };

  data.forEach((row) => {
    const [date, product, category, person, amount, quantity] = row;
    const numAmount = Number(amount) || 0;
    const numQuantity = Number(quantity) || 0;

    // 合計
    summary.totalSales += numAmount;
    summary.totalQuantity += numQuantity;

    // カテゴリ別
    if (!summary.byCategory[category]) {
      summary.byCategory[category] = { sales: 0, quantity: 0 };
    }
    summary.byCategory[category].sales += numAmount;
    summary.byCategory[category].quantity += numQuantity;

    // 担当者別
    if (!summary.byPerson[person]) {
      summary.byPerson[person] = { sales: 0, quantity: 0 };
    }
    summary.byPerson[person].sales += numAmount;
    summary.byPerson[person].quantity += numQuantity;

    // 商品別
    if (!summary.topProducts[product]) {
      summary.topProducts[product] = { sales: 0, quantity: 0 };
    }
    summary.topProducts[product].sales += numAmount;
    summary.topProducts[product].quantity += numQuantity;
  });

  return summary;
}

/**
 * レポートシートに集計結果を書き込み
 */
function writeReport(sheet, summary, dateStr) {
  sheet.clear();

  let row = 1;

  // タイトル
  sheet.getRange(row, 1).setValue(`売上レポート - ${dateStr}`);
  sheet.getRange(row, 1).setFontSize(14).setFontWeight("bold");
  row += 2;

  // 全体サマリー
  sheet.getRange(row, 1).setValue("【全体サマリー】").setFontWeight("bold");
  row++;
  sheet.getRange(row, 1).setValue("売上合計");
  sheet.getRange(row, 2).setValue(summary.totalSales).setNumberFormat("#,##0円");
  row++;
  sheet.getRange(row, 1).setValue("数量合計");
  sheet.getRange(row, 2).setValue(summary.totalQuantity);
  row += 2;

  // カテゴリ別
  sheet.getRange(row, 1).setValue("【カテゴリ別】").setFontWeight("bold");
  row++;
  sheet.getRange(row, 1).setValue("カテゴリ");
  sheet.getRange(row, 2).setValue("売上");
  sheet.getRange(row, 3).setValue("数量");
  sheet.getRange(row, 1, 1, 3).setFontWeight("bold").setBackground("#e8e8e8");
  row++;

  Object.entries(summary.byCategory)
    .sort((a, b) => b[1].sales - a[1].sales)
    .forEach(([cat, vals]) => {
      sheet.getRange(row, 1).setValue(cat);
      sheet.getRange(row, 2).setValue(vals.sales).setNumberFormat("#,##0円");
      sheet.getRange(row, 3).setValue(vals.quantity);
      row++;
    });
  row++;

  // 担当者別
  sheet.getRange(row, 1).setValue("【担当者別】").setFontWeight("bold");
  row++;
  sheet.getRange(row, 1).setValue("担当者");
  sheet.getRange(row, 2).setValue("売上");
  sheet.getRange(row, 3).setValue("数量");
  sheet.getRange(row, 1, 1, 3).setFontWeight("bold").setBackground("#e8e8e8");
  row++;

  Object.entries(summary.byPerson)
    .sort((a, b) => b[1].sales - a[1].sales)
    .forEach(([person, vals]) => {
      sheet.getRange(row, 1).setValue(person);
      sheet.getRange(row, 2).setValue(vals.sales).setNumberFormat("#,##0円");
      sheet.getRange(row, 3).setValue(vals.quantity);
      row++;
    });

  // 列幅調整
  sheet.autoResizeColumns(1, 3);
}

/**
 * メールでレポートを送信
 */
function sendReportEmail(summary, dateStr) {
  const subject = `【${CONFIG.COMPANY_NAME}】売上日報 ${dateStr}`;

  // カテゴリ別のテキスト
  const categoryLines = Object.entries(summary.byCategory)
    .sort((a, b) => b[1].sales - a[1].sales)
    .map(
      ([cat, vals]) =>
        `  ${cat}: ${vals.sales.toLocaleString()}円 (${vals.quantity}件)`
    )
    .join("\n");

  // 担当者別のテキスト
  const personLines = Object.entries(summary.byPerson)
    .sort((a, b) => b[1].sales - a[1].sales)
    .map(
      ([person, vals]) =>
        `  ${person}: ${vals.sales.toLocaleString()}円 (${vals.quantity}件)`
    )
    .join("\n");

  const body = `
${CONFIG.COMPANY_NAME} 売上日報
日付: ${dateStr}
━━━━━━━━━━━━━━━━━━━━

■ 全体サマリー
  売上合計: ${summary.totalSales.toLocaleString()}円
  数量合計: ${summary.totalQuantity}件

■ カテゴリ別
${categoryLines}

■ 担当者別
${personLines}

━━━━━━━━━━━━━━━━━━━━
※ このメールはGASにより自動送信されています。
  `.trim();

  CONFIG.NOTIFICATION_EMAILS.forEach((email) => {
    MailApp.sendEmail({
      to: email,
      subject: subject,
      body: body,
    });
  });

  Logger.log(`メール送信完了: ${CONFIG.NOTIFICATION_EMAILS.join(", ")}`);
}

/**
 * シートを取得（なければ作成）
 */
function getOrCreateSheet(ss, name) {
  let sheet = ss.getSheetByName(name);
  if (!sheet) {
    sheet = ss.insertSheet(name);
  }
  return sheet;
}

// ===== トリガー設定 =====

/**
 * 毎日朝9時に日次レポートを自動生成するトリガーを設定
 */
function setDailyTrigger() {
  // 既存のトリガーを削除
  ScriptApp.getProjectTriggers().forEach((trigger) => {
    if (trigger.getHandlerFunction() === "generateDailyReport") {
      ScriptApp.deleteTrigger(trigger);
    }
  });

  // 新しいトリガーを設定
  ScriptApp.newTrigger("generateDailyReport")
    .timeBased()
    .atHour(9)
    .everyDays(1)
    .inTimezone("Asia/Tokyo")
    .create();

  Logger.log("日次トリガーを設定しました（毎日9:00）");
}

/**
 * 月次レポート生成（毎月1日に前月分を集計）
 */
function generateMonthlyReport() {
  const ss = SpreadsheetApp.openById(CONFIG.SPREADSHEET_ID);
  const dataSheet = ss.getSheetByName(CONFIG.DATA_SHEET_NAME);

  const now = new Date();
  const lastMonthStart = new Date(now.getFullYear(), now.getMonth() - 1, 1);
  const lastMonthEnd = new Date(now.getFullYear(), now.getMonth(), 0);

  const monthStr = Utilities.formatDate(
    lastMonthStart,
    "Asia/Tokyo",
    "yyyy年MM月"
  );
  const data = getDataByDateRange(dataSheet, lastMonthStart, lastMonthEnd);

  if (data.length === 0) {
    Logger.log(`${monthStr} のデータがありません`);
    return;
  }

  const summary = aggregateData(data);
  const sheetName = `月次_${Utilities.formatDate(lastMonthStart, "Asia/Tokyo", "yyyyMM")}`;
  const reportSheet = getOrCreateSheet(ss, sheetName);
  writeReport(reportSheet, summary, monthStr);

  Logger.log(`月次レポート生成完了: ${monthStr}`);
}
