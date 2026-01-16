/**
 * JavaScript 性能优化工具库
 */

(function(global) {
    'use strict';

    /**
     * 防抖函数 - 延迟执行，只在最后一次调用后等待指定时间
     * @param {Function} func - 要执行的函数
     * @param {number} wait - 等待时间（毫秒）
     * @param {boolean} immediate - 是否立即执行
     * @returns {Function} 防抖后的函数
     */
    function debounce(func, wait, immediate = false) {
        let timeout;
        return function executedFunction(...args) {
            const context = this;
            const later = function() {
                timeout = null;
                if (!immediate) func.apply(context, args);
            };
            const callNow = immediate && !timeout;
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
            if (callNow) func.apply(context, args);
        };
    }

    /**
     * 节流函数 - 限制执行频率，在指定时间内只执行一次
     * @param {Function} func - 要执行的函数
     * @param {number} limit - 时间限制（毫秒）
     * @returns {Function} 节流后的函数
     */
    function throttle(func, limit) {
        let inThrottle;
        return function(...args) {
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }

    /**
     * 请求缓存 - 缓存API响应，避免重复请求
     * @param {Function} requestFn - 请求函数
     * @param {number} cacheTime - 缓存时间（毫秒）
     * @returns {Function} 带缓存的请求函数
     */
    function cacheRequest(requestFn, cacheTime = 5000) {
        const cache = new Map();
        const timestamps = new Map();

        return async function(...args) {
            const key = JSON.stringify(args);
            const now = Date.now();

            // 检查缓存
            if (cache.has(key)) {
                const timestamp = timestamps.get(key);
                if (now - timestamp < cacheTime) {
                    return cache.get(key);
                }
            }

            // 执行请求
            const result = await requestFn.apply(this, args);

            // 存入缓存
            cache.set(key, result);
            timestamps.set(key, now);

            return result;
        };
    }

    /**
     * 批量执行 - 将多次调用合并为一次执行
     * @param {Function} func - 要执行的函数
     * @param {number} delay - 延迟时间（毫秒）
     * @returns {Function} 批量执行后的函数
     */
    function batch(func, delay = 0) {
        let batchedArgs = [];
        let timeoutId;

        return function(...args) {
            batchedArgs.push(args);

            if (!timeoutId) {
                timeoutId = setTimeout(() => {
                    func.call(this, batchedArgs);
                    batchedArgs = [];
                    timeoutId = null;
                }, delay);
            }
        };
    }

    /**
     * 懒加载图片 - 延迟加载视口外的图片
     * @param {string} selector - 图片选择器
     * @param {Object} options - IntersectionObserver选项
     */
    function lazyLoadImages(selector = 'img[data-src]', options = {}) {
        const defaultOptions = {
            rootMargin: '50px',
            threshold: 0.01
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    const src = img.getAttribute('data-src');
                    if (src) {
                        img.src = src;
                        img.removeAttribute('data-src');
                        observer.unobserve(img);
                    }
                }
            });
        }, { ...defaultOptions, ...options });

        document.querySelectorAll(selector).forEach(img => {
            observer.observe(img);
        });

        return observer;
    }

    /**
     * 资源预加载 - 预加载关键资源
     * @param {Array<string>} urls - 资源URL数组
     * @param {string} type - 资源类型 (style, script, image, font)
     */
    function preloadResources(urls, type = 'script') {
        urls.forEach(url => {
            let link;

            switch (type) {
                case 'style':
                    link = document.createElement('link');
                    link.rel = 'preload';
                    link.as = 'style';
                    link.href = url;
                    break;
                case 'script':
                    link = document.createElement('link');
                    link.rel = 'preload';
                    link.as = 'script';
                    link.href = url;
                    break;
                case 'image':
                    link = document.createElement('link');
                    link.rel = 'preload';
                    link.as = 'image';
                    link.href = url;
                    break;
                case 'font':
                    link = document.createElement('link');
                    link.rel = 'preload';
                    link.as = 'font';
                    link.href = url;
                    link.crossOrigin = 'anonymous';
                    break;
                default:
                    return;
            }

            if (link) {
                document.head.appendChild(link);
            }
        });
    }

    /**
     * DOM更新批处理 - 批量更新DOM，减少重排重绘
     * @param {Function} updates - 更新函数
     */
    function batchDOMUpdates(updates) {
        // 使用 requestAnimationFrame 在浏览器重绘前执行
        requestAnimationFrame(() => {
            updates();
        });
    }

    /**
     * 虚拟滚动 - 只渲染可见区域的列表项
     * @param {Element} container - 容器元素
     * @param {Array} items - 数据项
     * @param {Function} renderItem - 渲染项的函数
     * @param {Object} options - 配置选项
     */
    function virtualScroll(container, items, renderItem, options = {}) {
        const {
            itemHeight = 50,
            buffer = 5
        } = options;

        let scrollTop = 0;
        let visibleStart = 0;
        let visibleEnd = 0;

        function update() {
            const containerHeight = container.clientHeight;
            const startIndex = Math.max(0, Math.floor(scrollTop / itemHeight) - buffer);
            const endIndex = Math.min(
                items.length - 1,
                Math.ceil((scrollTop + containerHeight) / itemHeight) + buffer
            );

            if (startIndex !== visibleStart || endIndex !== visibleEnd) {
                visibleStart = startIndex;
                visibleEnd = endIndex;

                const fragment = document.createDocumentFragment();
                for (let i = startIndex; i <= endIndex; i++) {
                    const element = renderItem(items[i], i);
                    fragment.appendChild(element);
                }

                container.innerHTML = '';
                container.appendChild(fragment);
            }
        }

        // 初始化
        container.style.height = `${items.length * itemHeight}px`;
        update();

        // 监听滚动
        container.addEventListener('scroll', throttle(() => {
            scrollTop = container.scrollTop;
            update();
        }, 16));

        return {
            update,
            scrollToIndex: (index) => {
                scrollTop = index * itemHeight;
                container.scrollTop = scrollTop;
                update();
            }
        };
    }

    /**
     * 请求IdleCallback - 在浏览器空闲时执行低优先级任务
     * @param {Function} callback - 要执行的回调
     * @param {Object} options - 选项
     */
    function requestIdle(callback, options = {}) {
        if ('requestIdleCallback' in window) {
            window.requestIdleCallback(callback, options);
        } else {
            // 降级方案
            setTimeout(callback, 1);
        }
    }

    /**
     * 分块执行 - 将大任务分块执行，避免阻塞主线程
     * @param {Array} items - 要处理的数据项
     * @param {Function} processFn - 处理函数
     * @param {number} chunkSize - 每块大小
     * @param {Function} onComplete - 完成回调
     */
    function processChunks(items, processFn, chunkSize = 50, onComplete) {
        let index = 0;

        function processChunk() {
            const end = Math.min(index + chunkSize, items.length);

            for (; index < end; index++) {
                processFn(items[index], index);
            }

            if (index < items.length) {
                requestIdle(processChunk);
            } else if (onComplete) {
                onComplete();
            }
        }

        processChunk();
    }

    /**
     * 内存缓存 - 简单的内存缓存实现
     */
    function MemoryCache(maxSize = 100) {
        this.cache = new Map();
        this.maxSize = maxSize;

        this.get = function(key) {
            return this.cache.get(key);
        };

        this.set = function(key, value) {
            if (this.cache.size >= this.maxSize) {
                // 删除最早的缓存项
                const firstKey = this.cache.keys().next().value;
                this.cache.delete(firstKey);
            }
            this.cache.set(key, value);
        };

        this.has = function(key) {
            return this.cache.has(key);
        };

        this.clear = function() {
            this.cache.clear();
        };

        this.delete = function(key) {
            return this.cache.delete(key);
        };
    }

    // 导出到全局
    global.PerfUtils = {
        debounce,
        throttle,
        cacheRequest,
        batch,
        lazyLoadImages,
        preloadResources,
        batchDOMUpdates,
        virtualScroll,
        requestIdle,
        processChunks,
        MemoryCache
    };

})(typeof window !== 'undefined' ? window : global);
