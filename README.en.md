<div align="center">

# 🛡️ StoreSentinel

**Zero-dependency · Offline-first static analyzer for app-store rejection risks**

Self-check your iOS / Android / Flutter / React Native project *before* you
submit for review. 15 built-in rules cover the most common App Store &
Google Play rejection reasons, and the scan produces a readiness score plus
text / JSON / SARIF reports with concrete fix hints.

[简体中文](README.md) · [繁體中文](README.zh-TW.md) · [English](README.en.md)

`Python ≥3.8` · No third-party dependencies · CI-gate ready · MIT

</div>

---

## 🎉 Introduction

> Three minutes before you hit "Submit for Review", run StoreSentinel and
> kill the reject-fix-resubmit loop locally.

The most common causes of store review failures — missing permission purpose
strings, missing privacy manifests, debuggable builds, low targetSdk,
cleartext traffic — can all be caught by static scanning *before* submission.
StoreSentinel takes the **product idea** behind community rejection
playbooks and implements a lightweight scanning engine in pure,
dependency-free Python:

- **Runs locally, code never leaves your machine** — no network calls, no
  uploads, no LLM APIs;
- **Works out of the box** — a single-file zipapp is enough, no dependency
  pollution in your project;
- **CI-gate ready** — `--fail-on-error` plus SARIF output plugs straight
  into GitHub Code Scanning.

## ✨ Features

- ✅ **15 built-in rules**: iOS 5 · Android 7 · Flutter 2 · General 1
- 🧠 **Permission back-tracing**: scans Swift / ObjC / Dart sources for
  privacy-sensitive APIs and checks whether the matching Info.plist purpose
  strings exist (`IOS005`)
- 📊 **Readiness score**: 0–100 (error -10 / warn -3 / info 0)
- 📄 **Three report formats**: colored terminal text / JSON / SARIF 2.1.0
  (GitHub Code Scanning compatible)
- 🚦 **CI gate**: exit code 1 on any error-severity finding with
  `--fail-on-error`
- ⚡ **Zero dependencies**: Python 3.8+ standard library only
- 🎯 **Rule discovery**: `--list-rules` prints every rule, severity and
  platform

## 🚀 Quick Start

```bash
# Option 1: pip install
pip install storesentinel

# Option 2: single file, no install
python3 storesentinel-1.0.0.pyz <project-path>

# Option 3: clone
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

## 📖 Usage Guide

### Command reference

| Command | Description |
| --- | --- |
| `storesentinel <path>` | Scan a project and print a colored report |
| `-f json / sarif` | Choose the report format (`-o` writes to file) |
| `--fail-on-error` | Exit code 1 when error findings exist (CI gate) |
| `--target-sdk 35` | Custom Android minimum targetSdk (default 34) |
| `--list-rules` | List all rules |
| `--no-color` | Disable ANSI colors |

### Built-in rules

| ID | Severity | Platform | Rule |
| --- | --- | --- | --- |
| IOS001 | error | iOS | Missing `ITSAppUsesNonExemptEncryption` (export compliance) |
| IOS002 | error | iOS | Missing `PrivacyInfo.xcprivacy` privacy manifest |
| IOS003 | warn | iOS | ATS globally disabled (`NSAllowsArbitraryLoads`) |
| IOS004 | warn | iOS | No launch screen configured |
| IOS005 | error | iOS | Sensitive API used without matching purpose string |
| AND001 | error | Android | `android:debuggable="true"` |
| AND002 | warn | Android | Cleartext traffic globally allowed |
| AND003 | info | Android | Dangerous permission declared |
| AND004 | error | Android | targetSdk below store minimum |
| AND005 | warn | Android | intent-filter component missing `android:exported` |
| AND006 | warn | Android | Placeholder `com.example.*` package name |
| AND007 | error | Android | Missing versionCode / versionName |
| FLT001 | error | Flutter | pubspec.yaml missing version |
| FLT002 | warn | Flutter | pubspec.yaml missing description |
| GEN001 | info | General | No privacy policy file in repository |

### CI integration (GitHub Actions example)

```yaml
- name: StoreSentinel gate
  run: |
    pip install storesentinel
    storesentinel . --fail-on-error -f sarif -o report.sarif
  # optionally upload SARIF via upload-artifact / code-scanning
```

## 💡 Design Notes

- **v1.0.0**: first release. 15 rules, SARIF support, one-command zipapp
  packaging.
- **Planned**: iOS declared-permission cross-check, Android Data Safety
  mapping, custom YAML rule files, `--strict` to include warnings in the
  gate.

## 📦 Packaging

```bash
./build.sh            # tests → zipapp → wheel → SHA256SUMS.txt
```

Artifacts land in `dist/`:

- `storesentinel-<version>.pyz`: cross-platform single file, run with
  `python3 xxx.pyz <path>`
- `storesentinel-<version>-py3-none-any.whl`: pip-installable wheel
- `SHA256SUMS.txt`: SHA-256 checksums for all artifacts

## 🤝 Contributing

Issues and PRs are welcome! Please follow the conventions in
[CONTRIBUTING.md](CONTRIBUTING.md) when adding a rule (register it, add a
positive and a negative test case, update all three READMEs).

## 📄 License

[MIT](LICENSE) © gitstq
