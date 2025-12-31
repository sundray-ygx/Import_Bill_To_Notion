# 将代码上传至GitHub仓库的详细步骤

## 1. 初始化Git仓库
- 检查当前目录是否已初始化Git仓库
- 如果未初始化，执行`git init`命令初始化

## 2. 创建并配置.gitignore文件
- 创建适合Python项目的.gitignore文件
- 包含常见的需要忽略的文件和目录（如__pycache__、venv、.env等）

## 3. 本地代码提交
- 添加所有文件到暂存区：`git add .`
- 提交代码到本地仓库：`git commit -m "Initial commit"`

## 4. 创建GitHub仓库
- 在GitHub网站上创建新的仓库
- 获取仓库的SSH或HTTPS URL

## 5. 添加远程仓库
- 将本地仓库关联到GitHub远程仓库：`git remote add origin <github-repo-url>`

## 6. 推送代码到GitHub
- 推送本地代码到GitHub：`git push -u origin main`

## 7. 验证上传结果
- 检查GitHub仓库是否包含所有代码文件
- 确认提交记录正确

## 执行计划

1. **准备工作**
   - 检查Git是否已安装：`git --version`
   - 如果未安装，先安装Git

2. **初始化仓库**
   - 在项目根目录执行：`git init`

3. **创建.gitignore文件**
   - 使用适合Python项目的模板创建.gitignore文件
   - 确保包含以下内容：
     ```
     __pycache__/
     *.py[cod]
     *$py.class
     .env
     .env.local
     .env.*.local
     venv/
     .venv/
     logs/
     *.log
     ```

4. **添加并提交代码**
   - `git add .`
   - `git commit -m "Initial commit - Notion账单导入服务"`

5. **创建GitHub仓库**
   - 访问GitHub网站，登录账号
   - 点击"New repository"创建新仓库
   - 填写仓库名称，选择公开/私有
   - 不要初始化README、.gitignore或license
   - 点击"Create repository"

6. **关联远程仓库**
   - 复制GitHub仓库的URL
   - 执行：`git remote add origin <repository-url>`

7. **推送代码**
   - 执行：`git push -u origin main`
   - 如果需要输入GitHub账号密码或SSH密钥，请按提示操作

8. **验证结果**
   - 访问GitHub仓库页面
   - 确认所有代码文件已上传
   - 查看提交历史，确认初始提交已显示

## 注意事项

- 如果项目中包含敏感信息（如API密钥、密码等），请确保已从代码中移除或通过环境变量管理
- 确保.gitignore文件已正确配置，避免上传不必要的文件
- 首次推送可能需要配置Git的用户名和邮箱：
  ```
  git config --global user.name "Your Name"
  git config --global user.email "your.email@example.com"
  ```
- 如果使用SSH URL，需要确保已配置SSH密钥

## 后续维护

- 每次代码修改后，使用`git add`和`git commit`提交到本地仓库
- 使用`git push`推送到GitHub仓库
- 定期拉取远程仓库的更新：`git pull`
- 必要时创建分支进行功能开发：`git checkout -b feature-branch`