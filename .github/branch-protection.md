# Настройка защиты веток

Этот документ описывает рекомендуемые настройки защиты веток для репозитория.

## Настройки для ветки `main`

### Обязательные проверки статуса
Следующие проверки должны пройти успешно перед слиянием:

- `test (3.9)` - Тесты на Python 3.9
- `test (3.10)` - Тесты на Python 3.10  
- `test (3.11)` - Тесты на Python 3.11
- `security-check` - Проверка безопасности
- `build-check` - Проверка сборки
- `code-quality` - Проверка качества кода
- `pr-validation` - Валидация Pull Request
- `size-check` - Проверка размера PR
- `conflict-check` - Проверка конфликтов

### Правила защиты ветки

#### ✅ Включить следующие опции:

1. **Require a pull request before merging**
   - Require approvals: 1
   - Dismiss stale PR approvals when new commits are pushed: ✅
   - Require review from code owners: ✅ (если есть CODEOWNERS файл)

2. **Require status checks to pass before merging**
   - Require branches to be up to date before merging: ✅
   - Status checks (указать все из списка выше)

3. **Require conversation resolution before merging**: ✅

4. **Require signed commits**: ✅ (рекомендуется)

5. **Require linear history**: ✅ (предотвращает merge commits)

6. **Include administrators**: ✅ (применять правила ко всем)

#### ❌ Отключить следующие опции:

1. **Allow force pushes**: ❌
2. **Allow deletions**: ❌

## Настройки для ветки `develop`

### Обязательные проверки статуса
- `test (3.11)` - Тесты на последней версии Python
- `code-quality` - Проверка качества кода
- `pr-validation` - Валидация Pull Request

### Правила защиты ветки

#### ✅ Включить следующие опции:

1. **Require a pull request before merging**
   - Require approvals: 1
   - Dismiss stale PR approvals when new commits are pushed: ✅

2. **Require status checks to pass before merging**
   - Require branches to be up to date before merging: ✅
   - Status checks (указать все из списка выше)

3. **Require conversation resolution before merging**: ✅

## Автоматическая настройка через API

Для автоматической настройки защиты веток можно использовать GitHub API:

```bash
# Настройка защиты для main ветки
curl -X PUT \
  -H "Accept: application/vnd.github.v3+json" \
  -H "Authorization: token YOUR_TOKEN" \
  https://api.github.com/repos/OWNER/REPO/branches/main/protection \
  -d '{
    "required_status_checks": {
      "strict": true,
      "contexts": [
        "test (3.9)",
        "test (3.10)", 
        "test (3.11)",
        "security-check",
        "build-check",
        "code-quality",
        "pr-validation",
        "size-check",
        "conflict-check"
      ]
    },
    "enforce_admins": true,
    "required_pull_request_reviews": {
      "required_approving_review_count": 1,
      "dismiss_stale_reviews": true,
      "require_code_owner_reviews": true
    },
    "restrictions": null,
    "required_linear_history": true,
    "allow_force_pushes": false,
    "allow_deletions": false,
    "required_conversation_resolution": true
  }'
```

## CODEOWNERS файл

Создайте файл `.github/CODEOWNERS` для автоматического назначения ревьюеров:

```
# Глобальные владельцы кода
* @username

# Владельцы для конкретных директорий
/webapp/ @frontend-team
/botapp/ @backend-team
/.github/ @devops-team

# Владельцы для конкретных файлов
requirements.txt @devops-team
docker-compose.yml @devops-team
```

## Рекомендации

1. **Регулярно обновляйте список обязательных проверок** при добавлении новых workflow
2. **Используйте draft PR** для работы в процессе разработки
3. **Настройте уведомления** для команды о статусе проверок
4. **Документируйте процесс** создания и ревью PR для новых участников команды
5. **Регулярно анализируйте** эффективность настроек защиты веток