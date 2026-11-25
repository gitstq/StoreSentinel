<div align="center">

# 🛡️ StoreSentinel

**零依賴 · 離線優先的應用程式商店拒審風險靜態掃描引擎**

對 iOS / Android / Flutter / React Native 專案做「送審前」的自查，
15 條內建規則涵蓋兩大應用程式商店最常見的拒審原因，輸出附修復建議的
就緒度評分與 text / JSON / SARIF 報告。

[简体中文](README.md) · [繁體中文](README.zh-TW.md) · [English](README.en.md)

`Python ≥3.8` · 無第三方相依套件 · CI 門檻就緒 · MIT

</div>

---

## 🎉 介紹

> 送審前 3 分鐘，跑一次 StoreSentinel，把「駁回—修改—重送」的迴圈扼殺在本機。

應用程式商店審核失敗最常見的誘因（權限用途說明缺失、隱私清單缺失、
debuggable 建置、targetSdk 過低、明文流量等）其實都能在送審前用靜態掃描發現。
StoreSentinel 參考社群拒審經驗的**產品思路**，以零相依的純 Python 實作了
一個輕量級掃描引擎：

- **本機執行，程式碼不出機器**——不連網、不上傳、不依賴任何 LLM API；
- **開箱即用**——單檔 zipapp 也能跑，不汙染專案相依；
- **CI 門檻就緒**——`--fail-on-error` + SARIF 輸出可直接接入 GitHub Code Scanning。

## ✨ 特性

- ✅ **15 條內建規則**：iOS 5 條 · Android 7 條 · Flutter 2 條 · 通用 1 條
- 🧠 **權限反查**：掃描 Swift / ObjC / Dart 原始碼中引用的敏感 API，
  反查 Info.plist 是否補齊用途說明（`IOS005`）
- 📊 **就緒度評分**：0–100 分（error -10 / warn -3 / info 0），一眼看清送審風險
- 📄 **三種報告**：終端機彩色文字 / JSON / SARIF 2.1.0（GitHub Code Scanning 相容）
- 🚦 **CI 門檻**：`--fail-on-error` 時存在 error 級發現即結束代碼 1
- ⚡ **零相依**：僅用 Python 3.8+ 標準函式庫，複製即測、打包即用
- 🎯 **規則可查**：`--list-rules` 列出全部規則、層級與適用平台

## 🚀 快速開始

```bash
# 方式一：pip 安裝
pip install storesentinel

# 方式二：單檔執行（免安裝）
python3 storesentinel-1.0.0.pyz <專案路徑>

# 方式三：複製儲存庫
git clone https://github.com/gitstq/StoreSentinel.git
cd StoreSentinel
python3 -m storesentinel /path/to/your-mobile-app
```

```console
$ python3 -m storesentinel ./MyApp
StoreSentinel scan report
Project : /work/MyApp
Platforms: ios
Readiness score: 64/100  (3 errors, 2 warnings, 1 infos)

-- ERRORS ----------------------------------------
[IOS001] ITSAppUsesNonExemptEncryption is not set in Info.plist
    fix : Add ITSAppUsesNonExemptEncryption(false) to Info.plist
...
Rules evaluated: 15
```

## 📖 使用指南

### 常用指令

| 指令 | 說明 |
| --- | --- |
| `storesentinel <path>` | 掃描專案並輸出彩色報告 |
| `-f json / sarif` | 切換報告格式（`-o` 寫入檔案） |
| `--fail-on-error` | 存在 error 級發現時結束代碼 1（CI 門檻） |
| `--target-sdk 35` | 自訂 Android 最低 targetSdk（預設 34） |
| `--list-rules` | 列出全部規則 |
| `--no-color` | 關閉 ANSI 顏色 |

### 內建規則總覽

| ID | 層級 | 平台 | 規則 |
| --- | --- | --- | --- |
| IOS001 | error | iOS | 缺少 `ITSAppUsesNonExemptEncryption`（出口合規） |
| IOS002 | error | iOS | 缺少 `PrivacyInfo.xcprivacy` 隱私清單 |
| IOS003 | warn | iOS | ATS 全域放行（`NSAllowsArbitraryLoads`） |
| IOS004 | warn | iOS | 未設定啟動畫面 |
| IOS005 | error | iOS | 原始碼使用敏感 API 但缺少對應用途說明 |
| AND001 | error | Android | `android:debuggable="true"` |
| AND002 | warn | Android | 全域允許明文流量 |
| AND003 | info | Android | 宣告了危險權限 |
| AND004 | error | Android | targetSdk 低於商店最低要求 |
| AND005 | warn | Android | 帶 intent-filter 的元件缺 `android:exported` |
| AND006 | warn | Android | `com.example.*` 佔位套件名稱 |
| AND007 | error | Android | 缺少 versionCode / versionName |
| FLT001 | error | Flutter | pubspec.yaml 缺少 version |
| FLT002 | warn | Flutter | pubspec.yaml 缺少 description |
| GEN001 | info | 通用 | 儲存庫內無隱私權政策檔案 |

### 接入 CI（GitHub Actions 範例）

```yaml
- name: StoreSentinel gate
  run: |
    pip install storesentinel
    storesentinel . --fail-on-error -f sarif -o report.sarif
  # 可繼續使用 upload-artifact / code-scanning 上傳 SARIF
```

## 💡 設計迭代

- **v1.0.0**：首發。15 條規則、SARIF 支援、zipapp 一鍵打包。
- **規劃中**：iOS Info.plist 與宣告權限交叉校驗、Android Data Safety 清單對照、
  自訂規則檔（YAML）、`--strict` 把 warn 納入門檻。

## 📦 打包部署

```bash
./build.sh            # 測試 → zipapp → wheel → SHA256SUMS.txt
```

產物位於 `dist/`：

- `storesentinel-<version>.pyz`：跨平台單檔，`python3 xxx.pyz <路徑>` 直接執行
- `storesentinel-<version>-py3-none-any.whl`：pip 安裝包
- `SHA256SUMS.txt`：全部產物的 SHA-256 校驗和

## 🤝 貢獻

歡迎 Issue 與 PR！新增規則請遵循 [CONTRIBUTING.md](CONTRIBUTING.md) 中的約定
（註冊規則表 + 正反兩個測試案例 + 更新三份 README）。

## 📄 授權條款

[MIT](LICENSE) © gitstq
