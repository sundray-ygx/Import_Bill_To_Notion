/**
 * Notion Bill Importer - Form Validator
 * 版本: 2.0
 *
 * 统一的表单验证工具，提供实时验证和友好的错误提示
 */

class FormValidator {
    constructor(form, options = {}) {
        this.form = typeof form === 'string' ? document.querySelector(form) : form;
        this.options = {
            validateOnBlur: true,
            validateOnChange: false,
            showErrorMessages: true,
            errorClass: 'input-error',
            successClass: 'input-success',
            ...options
        };
        this.validators = new Map();
        this.errors = new Map();
        this.init();
    }

    /**
     * 初始化表单验证
     */
    init() {
        if (!this.form) {
            console.error('Form element not found');
            return;
        }

        // 设置提交事件
        this.form.addEventListener('submit', (e) => this.handleSubmit(e));

        // 设置实时验证
        if (this.options.validateOnBlur) {
            this.form.querySelectorAll('input, select, textarea').forEach(field => {
                field.addEventListener('blur', () => this.validateField(field));
            });
        }

        if (this.options.validateOnChange) {
            this.form.querySelectorAll('input, select, textarea').forEach(field => {
                field.addEventListener('input', () => this.validateField(field));
            });
        }
    }

    /**
     * 添加字段验证规则
     * @param {string} fieldName - 字段名
     * @param {Array} rules - 验证规则数组
     */
    addField(fieldName, rules) {
        this.validators.set(fieldName, rules);
    }

    /**
     * 批量添加字段验证规则
     * @param {Object} fields - 字段规则对象
     */
    addFields(fields) {
        Object.entries(fields).forEach(([fieldName, rules]) => {
            this.addField(fieldName, rules);
        });
    }

    /**
     * 验证单个字段
     * @param {HTMLElement} field - 表单字段
     * @returns {boolean}
     */
    validateField(field) {
        const fieldName = field.name;
        const rules = this.validators.get(fieldName);

        if (!rules) return true;

        const value = field.value.trim();
        let error = null;

        // 依次检查规则
        for (const rule of rules) {
            error = this.checkRule(value, rule, field);
            if (error) break;
        }

        // 更新状态
        this.updateFieldStatus(field, error);
        if (error) {
            this.errors.set(fieldName, error);
            return false;
        } else {
            this.errors.delete(fieldName);
            return true;
        }
    }

    /**
     * 检查单个验证规则
     * @param {string} value - 字段值
     * @param {Object} rule - 验证规则
     * @param {HTMLElement} field - 表单字段
     * @returns {string|null}
     */
    checkRule(value, rule, field) {
        const { type, message, ...params } = rule;

        switch (type) {
            case 'required':
                if (!value) {
                    return message || `${getFieldLabel(field)}不能为空`;
                }
                break;

            case 'email':
                if (value && !this.isValidEmail(value)) {
                    return message || '请输入有效的邮箱地址';
                }
                break;

            case 'url':
                if (value && !this.isValidUrl(value)) {
                    return message || '请输入有效的URL地址';
                }
                break;

            case 'minLength':
                if (value && value.length < params.min) {
                    return message || `${getFieldLabel(field)}至少需要${params.min}个字符`;
                }
                break;

            case 'maxLength':
                if (value && value.length > params.max) {
                    return message || `${getFieldLabel(field)}不能超过${params.max}个字符`;
                }
                break;

            case 'pattern':
                if (value && !params.regex.test(value)) {
                    return message || `${getFieldLabel(field)}格式不正确`;
                }
                break;

            case 'min':
                if (value && parseFloat(value) < params.min) {
                    return message || `${getFieldLabel(field)}不能小于${params.min}`;
                }
                break;

            case 'max':
                if (value && parseFloat(value) > params.max) {
                    return message || `${getFieldLabel(field)}不能大于${params.max}`;
                }
                break;

            case 'match':
                const matchField = this.form.querySelector(`[name="${params.field}"]`);
                if (matchField && value !== matchField.value) {
                    return message || `两次输入不一致`;
                }
                break;

            case 'custom':
                if (params.validator && !params.validator(value, field)) {
                    return message || `${getFieldLabel(field)}验证失败`;
                }
                break;

            default:
                console.warn(`Unknown validation rule: ${type}`);
        }

        return null;
    }

    /**
     * 更新字段状态
     * @param {HTMLElement} field - 表单字段
     * @param {string|null} error - 错误信息
     */
    updateFieldStatus(field, error) {
        const formGroup = field.closest('.form-group');
        if (!formGroup) return;

        // 移除现有状态类
        field.classList.remove(this.options.errorClass, this.options.successClass);

        // 移除现有错误消息
        let errorElement = formGroup.querySelector('.form-error');
        if (errorElement) {
            errorElement.remove();
        }

        if (error) {
            // 添加错误状态
            field.classList.add(this.options.errorClass);

            // 添加错误消息
            if (this.options.showErrorMessages) {
                errorElement = document.createElement('div');
                errorElement.className = 'form-error';
                errorElement.innerHTML = `
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"/>
                        <line x1="12" y1="8" x2="12" y2="12"/>
                        <line x1="12" y1="16" x2="12.01" y2="16"/>
                    </svg>
                    <span>${error}</span>
                `;
                formGroup.appendChild(errorElement);
            }

            // 设置ARIA属性
            field.setAttribute('aria-invalid', 'true');
            field.setAttribute('aria-describedby', `${field.id}-error`);
            if (errorElement) {
                errorElement.id = `${field.id}-error`;
            }
        } else {
            // 添加成功状态
            if (field.value.trim()) {
                field.classList.add(this.options.successClass);
            }
            field.setAttribute('aria-invalid', 'false');
            field.removeAttribute('aria-describedby');
        }
    }

    /**
     * 处理表单提交
     * @param {Event} e - 提交事件
     */
    handleSubmit(e) {
        const isValid = this.validate();
        if (!isValid) {
            e.preventDefault();
            // 聚焦到第一个错误字段
            const firstErrorField = this.form.querySelector('.input-error');
            if (firstErrorField) {
                firstErrorField.focus();
            }
        }
        return isValid;
    }

    /**
     * 验证整个表单
     * @returns {boolean}
     */
    validate() {
        let isValid = true;
        const fields = this.form.querySelectorAll('input, select, textarea');

        fields.forEach(field => {
            if (this.validators.has(field.name)) {
                const fieldValid = this.validateField(field);
                if (!fieldValid) isValid = false;
            }
        });

        return isValid;
    }

    /**
     * 重置表单
     */
    reset() {
        this.form.reset();
        this.errors.clear();

        // 移除所有状态类
        this.form.querySelectorAll('input, select, textarea').forEach(field => {
            field.classList.remove(this.options.errorClass, this.options.successClass);
            field.removeAttribute('aria-invalid');
            field.removeAttribute('aria-describedby');
        });

        // 移除所有错误消息
        this.form.querySelectorAll('.form-error').forEach(el => el.remove());
    }

    /**
     * 获取所有错误
     * @returns {Object}
     */
    getErrors() {
        return Object.fromEntries(this.errors);
    }

    /**
     * 验证邮箱格式
     * @param {string} email
     * @returns {boolean}
     */
    isValidEmail(email) {
        const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return regex.test(email);
    }

    /**
     * 验证URL格式
     * @param {string} url
     * @returns {boolean}
     */
    isValidUrl(url) {
        try {
            new URL(url);
            return true;
        } catch {
            return false;
        }
    }
}

/**
 * 获取字段标签
 * @param {HTMLElement} field
 * @returns {string}
 */
function getFieldLabel(field) {
    // 优先使用aria-label
    if (field.getAttribute('aria-label')) {
        return field.getAttribute('aria-label');
    }

    // 其次查找关联的label
    const label = document.querySelector(`label[for="${field.id}"]`);
    if (label) {
        return label.textContent.replace('*', '').trim();
    }

    // 最后使用name属性
    return field.name || '此字段';
}

/**
 * 预定义验证规则
 */
const ValidationRules = {
    // 必填
    required: (message) => ({
        type: 'required',
        message
    }),

    // 邮箱
    email: (message) => ({
        type: 'email',
        message
    }),

    // URL
    url: (message) => ({
        type: 'url',
        message
    }),

    // 最小长度
    minLength: (min, message) => ({
        type: 'minLength',
        min,
        message
    }),

    // 最大长度
    maxLength: (max, message) => ({
        type: 'maxLength',
        max,
        message
    }),

    // 正则表达式
    pattern: (regex, message) => ({
        type: 'pattern',
        regex,
        message
    }),

    // 最小值
    min: (min, message) => ({
        type: 'min',
        min,
        message
    }),

    // 最大值
    max: (max, message) => ({
        type: 'max',
        max,
        message
    }),

    // 字段匹配
    match: (fieldName, message) => ({
        type: 'match',
        field: fieldName,
        message
    }),

    // 自定义验证
    custom: (validator, message) => ({
        type: 'custom',
        validator,
        message
    })
};

/**
 * 常用验证规则预设
 */
const CommonValidations = {
    // 用户名
    username: [
        { type: 'required', message: '用户名不能为空' },
        { type: 'minLength', min: 3, message: '用户名至少需要3个字符' },
        { type: 'maxLength', max: 20, message: '用户名不能超过20个字符' },
        {
            type: 'pattern',
            regex: /^[a-zA-Z0-9_-]+$/,
            message: '用户名只能包含字母、数字、下划线和连字符'
        }
    ],

    // 邮箱
    email: [
        { type: 'required', message: '邮箱不能为空' },
        { type: 'email', message: '请输入有效的邮箱地址' }
    ],

    // 密码
    password: [
        { type: 'required', message: '密码不能为空' },
        { type: 'minLength', min: 8, message: '密码至少需要8个字符' },
        {
            type: 'pattern',
            regex: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/,
            message: '密码必须包含大小写字母和数字'
        }
    ],

    // 确认密码
    confirmPassword: (passwordFieldName) => [
        { type: 'required', message: '请确认密码' },
        { type: 'match', field: passwordFieldName, message: '两次输入的密码不一致' }
    ],

    // Notion API Key
    notionApiKey: [
        { type: 'required', message: 'API Key不能为空' },
        {
            type: 'pattern',
            regex: /^secret_[a-zA-Z0-9]+$/,
            message: '请输入有效的Notion API Key (格式: secret_...)'
        }
    ],

    // Notion Database ID
    notionDatabaseId: [
        { type: 'required', message: 'Database ID不能为空' },
        {
            type: 'pattern',
            regex: /^[a-f0-9]{32}$/,
            message: '请输入有效的Notion Database ID (32位十六进制字符)'
        }
    ]
};

// 导出到全局
if (typeof window !== 'undefined') {
    window.FormValidator = FormValidator;
    window.ValidationRules = ValidationRules;
    window.CommonValidations = CommonValidations;
}
