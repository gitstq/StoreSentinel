<div align="center">

# 🛡️ StoreSentinel

**零依赖 · 离线优先的应用商店拒审风险静态扫描引擎**

对 iOS / Android / Flutter / React Native 项目做「提交审核前」的自查，
15 条内置规则覆盖两大应用商店最常见的拒审原因，输出带修复建议的
就绪度评分与 text / JSON / SARIF 报告。

[简体中文](README.md) · [繁體中文](README.zh-TW.md) · [English](README.en.md)

`Python ≥3.8` · 无第三方依赖 · CI 门禁就绪 · MIT

</div>

---

## 🎉 介绍

> 提审前 3 分钟，跑一次 StoreSentinel，把"驳回—修改—重提"的循环扼杀在本地。

应用商店审核失败最常见的诱因（权限用途说明缺失、隐私清单缺失、debuggable 构建、
targetSdk 过低、明文流量等）其实都可以在提交前用静态扫描发现。StoreSentinel 参考
社区拒审经验的**产品思路**，用零依赖的纯 Python 实现了一个轻量级扫描引擎：

- **本地运行，代码不出机器**——不联网、不上传、不依赖任何 LLM API；
- **开箱即用**——单文件 zipapp 也能跑，不污染项目依赖；
- **CI 门禁就绪**——`--fail-on-error` + SARIF 输出可直接接入 GitHub Code Scanning。

## ✨ 特性

- ✅ **15 条内置规则**：iOS 5 条 · Android 7 条 · Flutter 2 条 · 通用 1 条
- 🧠 **权限反查**：扫描 Swift / ObjC / Dart 源码中引用的敏感 API，反查 Info.plist 是否补齐用途说明（`IOS005`）
- 📊 **就绪度评分**：0–100 分（error -10 / warn -3 / info 0），一眼看清提审风险
- 📄 **三种报告**：终端彩色文本 / JSON / SARIF 2.1.0（GitHub Code Scanning 兼容）
- 🚦 **CI 门禁**：`--fail-on-error` 时存在 error 级发现即退出码 1
- ⚡ **零依赖**：仅用 Python 3.8+ 标准库，克隆即测、打包即用
- 🎯 **规则可查**：`--list-rules` 列出全部规则、级别与适用平台

## 🚀 快速开始

```bash
# 方式一：pip 安装
pip install storesentinel

# 方式二：单文件运行（免安装）
python3 storesentinel-1.0.0.pyz <项目路径>

# 方式三：克隆仓库
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

### 常用命令

| 命令 | 说明 |
| --- | --- |
| `storesentinel <path>` | 扫描项目并输出彩色报告 |
| `-f json / sarif` | 切换报告格式（`-o` 写入文件） |
| `--fail-on-error` | 存在 error 级发现时退出码 1（CI 门禁） |
| `--target-sdk 35` | 自定义 Android 最低 targetSdk（默认 34） |
| `--list-rules` | 列出全部规则 |
| `--no-color` | 关闭 ANSI 颜色 |

### 内置规则总览

| ID | 级别 | 平台 | 规则 |
| --- | --- | --- | --- |
| IOS001 | error | iOS | 缺少 `ITSAppUsesNonExemptEncryption`（出口合规） |
| IOS002 | error | iOS | 缺少 `PrivacyInfo.xcprivacy` 隐私清单 |
| IOS003 | warn | iOS | ATS 全局放行（`NSAllowsArbitraryLoads`） |
| IOS004 | warn | iOS | 未配置启动屏 |
| IOS005 | error | iOS | 源码使用敏感 API 但缺少对应用途说明 |
| AND001 | error | Android | `android:debuggable="true"` |
| AND002 | warn | Android | 全局允许明文流量 |
| AND003 | info | Android | 声明了危险权限 |
| AND004 | error | Android | targetSdk 低于商店最低要求 |
| AND005 | warn | Android | 带 intent-filter 的组件缺 `android:exported` |
| AND006 | warn | Android | `com.example.*` 占位包名 |
| AND007 | error | Android | 缺少 versionCode / versionName |
| FLT001 | error | Flutter | pubspec.yaml 缺少 version |
| FLT002 | warn | Flutter | pubspec.yaml 缺少 description |
| GEN001 | info | 通用 | 仓库内无隐私政策文件 |

### 接入 CI（GitHub Actions 示例）

```yaml
- name: StoreSentinel gate
  run: |
    pip install storesentinel
    storesentinel . --fail-on-error -f sarif -o report.sarif
  # 可继续使用 upload-artifact / code-scanning 上传 SARIF
```

## 💡 设计迭代

- **v1.0.0**：首发。15 条规则、SARIF 支持、zipapp 一键打包。
- **规划中**：iOS Info.plist 与声明权限交叉校验、Android Data Safety 清单对照、
  自定义规则文件（YAML）、`--strict` 把 warn 纳入门禁。

## 📦 打包部署

```bash
./build.sh            # 测试 → zipapp → wheel → SHA256SUMS.txt
```

产物位于 `dist/`：

- `storesentinel-<version>.pyz`：跨平台单文件，`python3 xxx.pyz <路径>` 直接运行
- `storesentinel-<version>-py3-none-any.whl`：pip 安装包
- `SHA256SUMS.txt`：全部产物的 SHA-256 校验和

## 🤝 贡献

欢迎 Issue 与 PR！新增规则请遵循 [CONTRIBUTING.md](CONTRIBUTING.md) 中的约定
（注册规则表 + 正反两个测试用例 + 更新三份 README）。

## 📄 协议

[MIT](LICENSE) © gitstq
