# 环境配置指南 (Environment Setup Guide)

## ⚠️ 重要安全提示

**环境文件 (`.env`, `.env.development`, `.env.test`) 包含敏感信息（API keys），绝对不能提交到 Git！**

这些文件已被添加到 `.gitignore`，Git 不会追踪它们。

---

## 📋 环境文件说明

| 文件 | 用途 | 包含内容 | Git | 本地 |
|------|------|--------|-----|------|
| `.env` | 生产环境 | API keys, secrets | ❌ | ✅ |
| `.env.development` | 开发环境 | 开发 API keys | ❌ | ✅ |
| `.env.test` | 测试环境 | 测试 API keys | ❌ | ✅ |
| `.env.example` | 模板文件 | 占位符，无敏感信息 | ✅ | ✅ |

---

## 🔧 设置步骤

### 1. 复制示例文件

```bash
# 从示例创建开发环境文件
cp .env.example .env.development

# 从示例创建测试环境文件  
cp .env.example .env.test

# 从示例创建生产环境文件
cp .env.example .env
```

### 2. 填入真实的 API Keys

编辑各环境文件，替换占位符：

#### `.env.development` (开发环境)
```env
FLASK_ENV=development
FLASK_DEBUG=True
FLASK_HOST=localhost
FLASK_PORT=5000
GEMINI_API_KEY=<你的开发API key>
DATABASE_URL=sqlite:///./data/tranotra_leads.db
LOG_LEVEL=INFO
```

#### `.env.test` (测试环境)
```env
FLASK_ENV=testing
FLASK_DEBUG=False
GEMINI_API_KEY=<你的测试API key>
DATABASE_URL=sqlite:///./data/test.db
LOG_LEVEL=DEBUG
```

#### `.env` (生产环境)
```env
FLASK_ENV=production
FLASK_DEBUG=False
GEMINI_API_KEY=<你的生产API key>
DATABASE_URL=<生产数据库URL>
LOG_LEVEL=WARNING
```

### 3. 获取 Gemini API Key

访问：https://aistudio.google.com/app/apikey

1. 使用 Google 账号登录
2. 创建或复制现有 API key
3. 将其添加到环境文件中
4. **不要在代码或提交消息中暴露 key**

---

## ✅ 验证配置

### 检查文件是否被保护

```bash
# 验证敏感文件不在 git 中
git ls-files | grep -E "\.env($|\.local|\.development|\.test)"

# 预期输出: (空，没有敏感文件)
```

### 检查本地文件是否存在

```bash
# 验证本地文件存在
ls -la .env .env.development .env.test

# 预期: 所有文件都存在
```

### 运行集成测试

```bash
# 使用 .env.development 中的 API key 运行测试
pytest tests/integration/test_real_gemini_api.py -v
```

---

## 🔐 安全最佳实践

### ✅ 请做

- [x] 为每个环境使用不同的 API key
- [x] 定期轮换 API key
- [x] 使用强随机密钥
- [x] 在 CI/CD 中使用 GitHub Secrets
- [x] 本地保护 `.env` 文件权限

### ❌ 请勿

- [ ] 提交 `.env` 文件到 Git
- [ ] 在代码中硬编码 API key
- [ ] 在提交消息中暴露敏感信息
- [ ] 将 API key 发送到聊天或公共平台
- [ ] 使用公开的 API key（容易被滥用）

---

## 🚀 CI/CD 配置（GitHub Actions）

### 使用 GitHub Secrets

1. **在 GitHub 仓库设置 Secrets**
   ```
   Settings → Secrets and variables → Actions → New repository secret
   ```

2. **配置 Secret 名称**
   ```
   GEMINI_API_KEY=<你的API key>
   ```

3. **在 GitHub Actions 工作流中使用**
   ```yaml
   - name: Run Integration Tests
     env:
      GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
     run: pytest tests/integration/test_real_gemini_api.py -v
   ```

---

## 📝 环境文件说明

### .env.example（提交到 Git ✅）

这是一个模板文件，包含所有必需的变量但不包含真实值。

```env
# 模板示例
FLASK_ENV=development
FLASK_DEBUG=True
GEMINI_API_KEY=your-api-key-here  # 占位符
DATABASE_URL=sqlite:///./data/tranotra_leads.db
```

### .env（不提交到 Git ❌）

- **本地生产环境配置**
- 包含真实 API key
- 被 `.gitignore` 保护
- 每个开发者有自己的副本

### .env.development（不提交到 Git ❌）

- **开发环境配置**
- 使用开发 API key（可能有不同的速率限制）
- 本地开发时使用
- 被 `.gitignore` 保护

### .env.test（不提交到 Git ❌）

- **测试环境配置**
- 可以使用测试 API key 或 mock key
- 运行集成测试时使用
- 被 `.gitignore` 保护

---

## 🔄 更新环境变量

如果添加了新的环境变量：

1. **更新 `.env.example`**
   ```bash
   # 添加新变量（占位符形式）
   echo "NEW_VAR=placeholder" >> .env.example
   ```

2. **提交更新**
   ```bash
   git add .env.example
   git commit -m "docs: Add NEW_VAR to environment template"
   ```

3. **每个开发者更新本地文件**
   ```bash
   # 本地手动添加或从 git pull 后更新
   cp .env.example .env.development
   # 然后编辑 .env.development，填入真实值
   ```

---

## 🆘 常见问题

### Q: 我不小心提交了 API key 怎么办？

**立即操作：**
1. 停止使用该 key
2. 在 Google Cloud Console 中禁用该 key
3. 生成新 key
4. 从 git 历史中移除（使用 `git-filter-branch` 或 `BFG Repo-Cleaner`）
5. 强制推送到远程（仅在小团队中）

```bash
# 从 git 历史中移除文件（需要 BFG）
bfg --delete-files .env --force
git push --force
```

### Q: 如何测试不同环境？

```bash
# 开发环境（使用 .env.development）
export $(cat .env.development | xargs)
pytest tests/integration/test_real_gemini_api.py

# 测试环境（使用 .env.test）
export $(cat .env.test | xargs)
pytest tests/integration/test_end_to_end_search_pipeline.py
```

### Q: API key 过期了怎么办？

1. 生成新 key：https://aistudio.google.com/app/apikey
2. 更新所有环境文件
3. 测试连接
4. 更新 GitHub Secrets（用于 CI/CD）

### Q: 如何与新队友共享环境配置？

**不要分享 `.env` 文件本身，而是：**

1. 共享 `.env.example`（已在 Git 中）
2. 新队友自己获取 API key
3. 新队友运行 `cp .env.example .env.development`
4. 新队友填入自己的 API key

---

## 📚 参考资源

- [Node.js 环境变量最佳实践](https://nodejs.org/en/knowledge/file-system/security/introduction/)
- [Python python-dotenv 文档](https://python-dotenv.readthedocs.io/)
- [GitHub Secrets 文档](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [Google API 安全性](https://cloud.google.com/docs/authentication/api-keys)

---

## ✔️ 设置完成检查清单

- [ ] 复制了 `.env.example` 到 `.env.development`
- [ ] 获取了有效的 Gemini API key
- [ ] 更新了 `.env.development` 中的 `GEMINI_API_KEY`
- [ ] 验证了敏感文件不在 Git 中（`git ls-files | grep .env`）
- [ ] 运行了集成测试验证配置（`pytest tests/integration/test_real_gemini_api.py`）
- [ ] 理解了安全最佳实践
- [ ] 如果使用 CI/CD，已配置 GitHub Secrets

---

**文档版本:** 1.0  
**最后更新:** 2026-04-04  
**安全等级:** 🔒 高
