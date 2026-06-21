(function () {
    'use strict';

    function ready(fn) {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', fn);
        } else {
            fn();
        }
    }

    ready(function () {
        var root = document.documentElement;
        var menuButton = document.querySelector('.menu-toggle');
        var header = document.querySelector('.site-header');
        var nav = document.querySelector('.nav-links');
        var themeButton = document.querySelector('.theme-toggle');
        var metaTheme = document.querySelector('meta[name="theme-color"]');

        // -----------------------------------------------------------
        // 🍞 Toast notifications — foydalanuvchiga xatolik/muvaffaqiyat
        // haqida ko'rinadigan signal berish uchun (jim qolib ketmaslik uchun)
        // -----------------------------------------------------------
        var toastHost = document.createElement('div');
        toastHost.className = 'kx-toast-host';
        document.body.appendChild(toastHost);

        function toast(message, type) {
            var el = document.createElement('div');
            el.className = 'kx-toast kx-toast-' + (type || 'info');
            el.textContent = message;
            toastHost.appendChild(el);
            requestAnimationFrame(function () { el.classList.add('show'); });
            setTimeout(function () {
                el.classList.remove('show');
                setTimeout(function () { el.remove(); }, 250);
            }, 3600);
        }
        window.kxToast = toast;

        // -----------------------------------------------------------
        // 🌗 Theme toggle
        // -----------------------------------------------------------
        function preferredTheme() {
            var saved = localStorage.getItem('kitobx-theme');
            if (saved === 'dark' || saved === 'light') return saved;
            return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
        }

        function applyTheme(theme) {
            root.dataset.theme = theme;
            if (themeButton) themeButton.setAttribute('aria-pressed', String(theme === 'dark'));
            if (metaTheme) metaTheme.setAttribute('content', theme === 'dark' ? '#09060d' : '#f7f5f2');
        }

        applyTheme(preferredTheme());

        if (themeButton) {
            themeButton.addEventListener('click', function () {
                var next = root.dataset.theme === 'dark' ? 'light' : 'dark';
                localStorage.setItem('kitobx-theme', next);
                applyTheme(next);
            });
        }

        // -----------------------------------------------------------
        // 📱 Mobile menu
        // -----------------------------------------------------------
        if (menuButton && nav && header) {
            menuButton.addEventListener('click', function () {
                var isOpen = header.classList.toggle('menu-open');
                menuButton.setAttribute('aria-expanded', String(isOpen));
            });

            nav.querySelectorAll('a').forEach(function (link) {
                link.addEventListener('click', function () {
                    header.classList.remove('menu-open');
                    menuButton.setAttribute('aria-expanded', 'false');
                });
            });
        }

        // -----------------------------------------------------------
        // ✨ Scroll reveal animation
        // -----------------------------------------------------------
        var revealItems = document.querySelectorAll('[data-reveal]');
        if ('IntersectionObserver' in window) {
            var observer = new IntersectionObserver(function (entries) {
                entries.forEach(function (entry) {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('is-visible');
                        observer.unobserve(entry.target);
                    }
                });
            }, { threshold: 0.1 });

            revealItems.forEach(function (item, index) {
                item.style.transitionDelay = Math.min(index * 35, 175) + 'ms';
                observer.observe(item);
            });
        } else {
            revealItems.forEach(function (item) { item.classList.add('is-visible'); });
        }

        // -----------------------------------------------------------
        // 🔐 CSRF helper — har bir so'rovda cookie qaytadan o'qiladi
        // (sahifa ochilgandan keyin cookie yangilangan holatlarni ham qamrab oladi)
        // -----------------------------------------------------------
        function getCookie(name) {
            var value = '; ' + document.cookie;
            var parts = value.split('; ' + name + '=');
            if (parts.length === 2) return decodeURIComponent(parts.pop().split(';').shift());
            return '';
        }

        function csrfHeaders(extra) {
            var headers = Object.assign({ 'X-CSRFToken': getCookie('csrftoken'), 'X-Requested-With': 'XMLHttpRequest' }, extra || {});
            return headers;
        }

        // Fetch wrapper: agar javob JSON bo'lmasa (masalan login sahifasiga
        // redirect bo'lib qolsa) buni aniq xato sifatida ko'rsatadi, jim
        // qolib ketmaydi.
        function requestJSON(url, options) {
            return fetch(url, options).then(function (res) {
                var contentType = res.headers.get('content-type') || '';
                if (res.status === 401 || res.status === 403 || res.redirected || contentType.indexOf('application/json') === -1) {
                    if (res.status === 403) {
                        throw new Error('AUTH_REQUIRED');
                    }
                    if (res.redirected || contentType.indexOf('text/html') !== -1) {
                        throw new Error('LOGIN_REQUIRED');
                    }
                }
                if (!res.ok) {
                    throw new Error('SERVER_ERROR');
                }
                return res.json();
            });
        }

        function handleFetchError(err) {
            console.error('[KitobX]', err);
            if (err && (err.message === 'LOGIN_REQUIRED' || err.message === 'AUTH_REQUIRED')) {
                toast('Bu amal uchun tizimga kiring.', 'error');
                setTimeout(function () {
                    window.location.href = '/accounts/login/?next=' + encodeURIComponent(window.location.pathname);
                }, 900);
            } else {
                toast('Xatolik yuz berdi. Birozdan keyin qayta urinib ko\'ring.', 'error');
            }
        }

        // -----------------------------------------------------------
        // 🔔 Notifications dropdown
        // -----------------------------------------------------------
        var notifToggle = document.getElementById('notifToggle');
        var notifDropdown = document.getElementById('notifDropdown');
        var notifMarkAll = document.getElementById('notifMarkAll');

        if (notifToggle && notifDropdown) {
            notifToggle.addEventListener('click', function (e) {
                e.preventDefault();
                e.stopPropagation();
                var open = notifDropdown.classList.toggle('open');
                notifToggle.setAttribute('aria-expanded', String(open));
            });
            notifDropdown.addEventListener('click', function (e) { e.stopPropagation(); });
            document.addEventListener('click', function () {
                notifDropdown.classList.remove('open');
                notifToggle.setAttribute('aria-expanded', 'false');
            });
            document.addEventListener('keydown', function (e) {
                if (e.key === 'Escape') notifDropdown.classList.remove('open');
            });

            if (notifMarkAll) {
                notifMarkAll.addEventListener('click', function (e) {
                    e.stopPropagation();
                    requestJSON('/bildirishnomalar/read-all/', {
                        method: 'POST',
                        headers: csrfHeaders()
                    }).then(function () {
                        document.querySelectorAll('.notif-item.unread, .notif-page-item.unread').forEach(function (el) {
                            el.classList.remove('unread');
                        });
                        var dot = notifToggle.querySelector('.notif-dot');
                        if (dot) dot.remove();
                        notifMarkAll.remove();
                    }).catch(handleFetchError);
                });
            }
        }

        // -----------------------------------------------------------
        // ❤ Wishlist toggle buttons
        // -----------------------------------------------------------
        document.querySelectorAll('.wishlist-btn').forEach(function (btn) {
            btn.addEventListener('click', function (e) {
                e.preventDefault();
                e.stopPropagation();
                if (btn.classList.contains('is-loading')) return;
                var url = btn.dataset.url;
                if (!url) return;
                btn.classList.add('is-loading');
                requestJSON(url, {
                    method: 'POST',
                    headers: csrfHeaders()
                })
                    .then(function (data) {
                        btn.classList.remove('is-loading');
                        btn.classList.toggle('active', data.added);
                        btn.setAttribute('aria-pressed', String(data.added));
                        document.querySelectorAll('.wishlist-btn[data-book="' + btn.dataset.book + '"]').forEach(function (other) {
                            other.classList.toggle('active', data.added);
                        });
                        toast(data.added ? 'Wishlistga qo\'shildi ❤' : 'Wishlistdan olib tashlandi', 'success');
                    })
                    .catch(function (err) {
                        btn.classList.remove('is-loading');
                        handleFetchError(err);
                    });
            });
        });

        // -----------------------------------------------------------
        // 📖 Reading progress slider (book_reader.html)
        // -----------------------------------------------------------
        var progressSlider = document.getElementById('progressSlider');
        var progressLabel = document.getElementById('progressLabel');
        var progressFill = document.getElementById('progressFill');
        var progressFinishBtn = document.getElementById('progressFinishBtn');

        function pushProgress(percent) {
            var url = progressSlider ? progressSlider.dataset.url : null;
            if (!url) return;
            requestJSON(url, {
                method: 'POST',
                headers: csrfHeaders({ 'Content-Type': 'application/json' }),
                body: JSON.stringify({ percent: percent })
            }).then(function (data) {
                if (data.completed && progressFinishBtn) {
                    progressFinishBtn.textContent = 'Tugatildi ✓';
                    progressFinishBtn.disabled = true;
                    toast('Tabriklaymiz! Kitobni tugatdingiz 🎉', 'success');
                }
            }).catch(handleFetchError);
        }

        if (progressSlider) {
            progressSlider.addEventListener('input', function () {
                var val = progressSlider.value;
                if (progressLabel) progressLabel.textContent = val + '%';
                if (progressFill) progressFill.style.width = val + '%';
            });
            progressSlider.addEventListener('change', function () {
                pushProgress(parseInt(progressSlider.value, 10));
            });
        }
        if (progressFinishBtn) {
            progressFinishBtn.addEventListener('click', function () {
                if (progressSlider) {
                    progressSlider.value = 100;
                    if (progressLabel) progressLabel.textContent = '100%';
                    if (progressFill) progressFill.style.width = '100%';
                }
                pushProgress(100);
            });
        }

        // -----------------------------------------------------------
        // 🤖 AI Chatbot widget
        // -----------------------------------------------------------
        var chatLauncher = document.getElementById('chatLauncher');
        var chatPanel = document.getElementById('chatPanel');
        var chatClose = document.getElementById('chatClose');
        var chatForm = document.getElementById('chatForm');
        var chatInput = document.getElementById('chatInput');
        var chatBody = document.getElementById('chatBody');

        function appendMessage(role, html) {
            if (!chatBody) return;
            var wrap = document.createElement('div');
            wrap.className = 'ai-msg ai-msg-' + (role === 'user' ? 'user' : 'bot');
            var iconSymbol = role === 'user' ? '#icon-user' : '#icon-sparkles';
            wrap.innerHTML =
                '<span class="ai-msg-icon"><svg><use href="' + iconSymbol + '"></use></svg></span>' +
                '<div class="ai-msg-bubble">' + html + '</div>';
            chatBody.appendChild(wrap);
            chatBody.scrollTop = chatBody.scrollHeight;
        }

        function appendTyping() {
            if (!chatBody) return;
            var wrap = document.createElement('div');
            wrap.className = 'ai-msg ai-msg-bot ai-msg-typing';
            wrap.id = 'aiTyping';
            wrap.innerHTML =
                '<span class="ai-msg-icon"><svg><use href="#icon-sparkles"></use></svg></span>' +
                '<div class="ai-msg-bubble"><span class="ai-dot"></span><span class="ai-dot"></span><span class="ai-dot"></span></div>';
            chatBody.appendChild(wrap);
            chatBody.scrollTop = chatBody.scrollHeight;
        }

        function escapeHtml(str) {
            var div = document.createElement('div');
            div.textContent = str;
            return div.innerHTML;
        }

        if (chatLauncher && chatPanel) {
            chatLauncher.addEventListener('click', function () {
                chatPanel.classList.add('open');
                chatPanel.setAttribute('aria-hidden', 'false');
                chatLauncher.classList.add('hidden');
                if (chatInput) chatInput.focus();
            });
            if (chatClose) {
                chatClose.addEventListener('click', function () {
                    chatPanel.classList.remove('open');
                    chatPanel.setAttribute('aria-hidden', 'true');
                    chatLauncher.classList.remove('hidden');
                });
            }
        }

        if (chatForm) {
            chatForm.addEventListener('submit', function (e) {
                e.preventDefault();
                var message = chatInput.value.trim();
                if (!message) return;
                appendMessage('user', escapeHtml(message));
                chatInput.value = '';
                appendTyping();

                fetch('/chatbot/message/', {
                    method: 'POST',
                    headers: csrfHeaders({ 'Content-Type': 'application/json' }),
                    body: JSON.stringify({ message: message })
                })
                    .then(function (res) {
                        if (!res.ok) throw new Error('SERVER_ERROR');
                        return res.json();
                    })
                    .then(function (data) {
                        var typing = document.getElementById('aiTyping');
                        if (typing) typing.remove();
                        var html = escapeHtml(data.reply || '...');
                        if (data.books && data.books.length) {
                            html += '<div class="ai-book-list">';
                            data.books.forEach(function (book) {
                                html += '<a class="ai-book-chip" href="' + book.url + '">' +
                                    (book.image ? '<img src="' + book.image + '" alt="">' : '') +
                                    '<span><strong>' + escapeHtml(book.title) + '</strong><small>' + escapeHtml(book.author) + '</small></span>' +
                                    '</a>';
                            });
                            html += '</div>';
                        }
                        if (data.action) {
                            html += '<a class="ai-action-btn" href="' + data.action.url + '">' + escapeHtml(data.action.label) + '</a>';
                        }
                        appendMessage('bot', html);
                    })
                    .catch(function (err) {
                        console.error('[KitobX chatbot]', err);
                        var typing = document.getElementById('aiTyping');
                        if (typing) typing.remove();
                        appendMessage('bot', 'Kechirasiz, xatolik yuz berdi. Birozdan keyin qayta urinib ko\'ring.');
                    });
            });
        }

        // -----------------------------------------------------------
        // 👑 VIP — simulyatsiya qilingan karta to'lov oynasi
        // -----------------------------------------------------------
        var vipModal = document.getElementById('vipPaymentModal');
        if (vipModal) {
            var vipForm = document.getElementById('vipPaymentForm');
            var vipCardNumber = document.getElementById('vipCardNumber');
            var vipCardExpiry = document.getElementById('vipCardExpiry');
            var vipCardCvv = document.getElementById('vipCardCvv');
            var vipCardName = document.getElementById('vipCardName');
            var vipPlanLabel = document.getElementById('vipModalPlanName');
            var vipPriceLabel = document.getElementById('vipModalPlanPrice');
            var vipCloseBtn = document.getElementById('vipModalClose');
            var vipCancelBtn = document.getElementById('vipModalCancel');
            var vipSubmitBtn = document.getElementById('vipModalSubmit');
            var vipErrorBox = document.getElementById('vipModalError');
            var vipSuccessBox = document.getElementById('vipModalSuccess');
            var currentSubscribeUrl = null;

            function openVipModal(btn) {
                currentSubscribeUrl = btn.dataset.url;
                vipPlanLabel.textContent = btn.dataset.planName || 'VIP reja';
                vipPriceLabel.textContent = btn.dataset.planPrice || '';
                vipForm.reset();
                vipErrorBox.textContent = '';
                vipErrorBox.style.display = 'none';
                vipSuccessBox.style.display = 'none';
                vipForm.style.display = 'grid';
                vipModal.classList.add('open');
                vipModal.setAttribute('aria-hidden', 'false');
                document.body.classList.add('kx-modal-open');
                setTimeout(function () { vipCardNumber.focus(); }, 150);
            }

            function closeVipModal() {
                vipModal.classList.remove('open');
                vipModal.setAttribute('aria-hidden', 'true');
                document.body.classList.remove('kx-modal-open');
            }

            document.querySelectorAll('.vip-subscribe-btn').forEach(function (btn) {
                btn.addEventListener('click', function (e) {
                    e.preventDefault();
                    openVipModal(btn);
                });
            });

            if (vipCloseBtn) vipCloseBtn.addEventListener('click', closeVipModal);
            if (vipCancelBtn) vipCancelBtn.addEventListener('click', closeVipModal);
            vipModal.addEventListener('click', function (e) {
                if (e.target === vipModal) closeVipModal();
            });
            document.addEventListener('keydown', function (e) {
                if (e.key === 'Escape' && vipModal.classList.contains('open')) closeVipModal();
            });

            // Karta raqamini avtomatik formatlash: 1234 5678 9012 3456
            if (vipCardNumber) {
                vipCardNumber.addEventListener('input', function () {
                    var digits = vipCardNumber.value.replace(/\D/g, '').slice(0, 16);
                    vipCardNumber.value = digits.replace(/(.{4})/g, '$1 ').trim();
                });
            }
            if (vipCardExpiry) {
                vipCardExpiry.addEventListener('input', function () {
                    var digits = vipCardExpiry.value.replace(/\D/g, '').slice(0, 4);
                    if (digits.length > 2) digits = digits.slice(0, 2) + '/' + digits.slice(2);
                    vipCardExpiry.value = digits;
                });
            }
            if (vipCardCvv) {
                vipCardCvv.addEventListener('input', function () {
                    vipCardCvv.value = vipCardCvv.value.replace(/\D/g, '').slice(0, 3);
                });
            }

            function showVipError(msg) {
                vipErrorBox.textContent = msg;
                vipErrorBox.style.display = 'flex';
            }

            if (vipForm) {
                vipForm.addEventListener('submit', function (e) {
                    e.preventDefault();
                    vipErrorBox.style.display = 'none';

                    var digits = vipCardNumber.value.replace(/\s/g, '');
                    if (digits.length !== 16) {
                        showVipError('Karta raqami 16 ta raqamdan iborat bo\'lishi kerak.');
                        return;
                    }
                    if (!/^\d{2}\/\d{2}$/.test(vipCardExpiry.value)) {
                        showVipError('Amal qilish muddatini MM/YY shaklida kiriting.');
                        return;
                    }
                    var mm = parseInt(vipCardExpiry.value.slice(0, 2), 10);
                    if (mm < 1 || mm > 12) {
                        showVipError('Oy noto\'g\'ri kiritildi.');
                        return;
                    }
                    if (vipCardCvv.value.length !== 3) {
                        showVipError('CVV 3 ta raqamdan iborat bo\'lishi kerak.');
                        return;
                    }
                    if (!vipCardName.value.trim()) {
                        showVipError('Karta egasining ismini kiriting.');
                        return;
                    }
                    if (!currentSubscribeUrl) {
                        showVipError('Xatolik: reja aniqlanmadi.');
                        return;
                    }

                    vipSubmitBtn.disabled = true;
                    vipSubmitBtn.classList.add('is-loading');
                    var originalLabel = vipSubmitBtn.textContent;
                    vipSubmitBtn.textContent = 'To\'lov amalga oshirilmoqda...';

                    // Real bank ulanishi yo'q — bu simulyatsiya qilingan to'lov oqimi.
                    // Foydalanuvchi tajribasi uchun qisqa kutish, so'ng faollashtirish so'rovi.
                    setTimeout(function () {
                        requestJSON(currentSubscribeUrl, {
                            method: 'POST',
                            headers: csrfHeaders()
                        }).then(function () {
                            vipForm.style.display = 'none';
                            vipSuccessBox.style.display = 'flex';
                            toast('VIP reja muvaffaqiyatli faollashtirildi! 👑', 'success');
                            setTimeout(function () { window.location.reload(); }, 1600);
                        }).catch(function (err) {
                            vipSubmitBtn.disabled = false;
                            vipSubmitBtn.classList.remove('is-loading');
                            vipSubmitBtn.textContent = originalLabel;
                            if (err && (err.message === 'LOGIN_REQUIRED' || err.message === 'AUTH_REQUIRED')) {
                                showVipError('Davom etish uchun avval tizimga kiring.');
                            } else {
                                showVipError('To\'lovni amalga oshirib bo\'lmadi. Qayta urinib ko\'ring.');
                            }
                        });
                    }, 900);
                });
            }
        }
    });
})();
