// static/js/language-manager.js
// SISTEMA UNIVERSAL DE GESTIÓN DE IDIOMA — VERSION FINAL (CON URL SYNC)

class LanguageManager {
    constructor() {

        // 1️⃣ Intentar obtener idioma desde la URL
        const urlLang = this.getLanguageFromURL();
        if (urlLang) {
            this.currentLang = urlLang;

            // Guardar para persistencia
            localStorage.setItem("preferred_language", urlLang);

            // Sincronizar con la página activa
            setTimeout(() => {
                window.dispatchEvent(
                    new CustomEvent("languageChanged", { detail: { language: urlLang } })
                );
            }, 20);

            this.init();
            return;
        }

        // 2️⃣ Si no viene en URL → usar preferencias guardadas
        this.currentLang = this.getPreferredLanguage();
        this.init();
    }

    // ===============================
    //  LEER IDIOMA DESDE LA URL
    // ===============================
    getLanguageFromURL() {
        const params = new URLSearchParams(window.location.search);
        const lang = params.get("lang");
        return this.isValidLanguage(lang) ? lang : null;
    }

    // Obtener idioma preferido desde varias fuentes
    getPreferredLanguage() {

        // 1. LocalStorage
        const localLang = localStorage.getItem('preferred_language');
        if (localLang && this.isValidLanguage(localLang)) {
            return localLang;
        }

        // 2. Cookie de servidor (si existe)
        const cookieLang = this.getCookie('language');
        if (cookieLang && this.isValidLanguage(cookieLang)) {
            return cookieLang;
        }

        // 3. Idioma del navegador
        const browserLang = navigator.language || navigator.userLanguage;
        if (browserLang.startsWith('es')) return 'espanol';
        if (browserLang.startsWith('en')) return 'ingles';

        // 4. Por defecto español
        return 'espanol';
    }

    // Validar idioma
    isValidLanguage(lang) {
        return ['espanol', 'ingles'].includes(lang);
    }

    // Leer cookie
    getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    }

    // ===============================
    //  CAMBIAR IDIOMA GLOBAL
    // ===============================
    async setLanguage(lang) {
        if (!this.isValidLanguage(lang)) {
            console.error("Idioma inválido:", lang);
            return;
        }

        try {
            // Enviar al servidor
            const response = await fetch('/set_language/' + lang);
            if (!response.ok) throw new Error("Error servidor");

            // Guardar en localStorage
            localStorage.setItem('preferred_language', lang);
            this.currentLang = lang;

            // Avisar a toda la página
            window.dispatchEvent(
                new CustomEvent('languageChanged', { detail: { language: lang } })
            );

        } catch (error) {
            console.error("Fallo setLanguage:", error);

            // fallback local
            localStorage.setItem('preferred_language', lang);
            this.currentLang = lang;
            window.dispatchEvent(
                new CustomEvent('languageChanged', { detail: { language: lang } })
            );
        }
    }

    // ===============================
    //  INICIALIZACIÓN
    // ===============================
    init() {
        console.log("LanguageManager iniciado | Idioma:", this.currentLang);

        // Aplicar idioma inicial
        this.applyLanguage();

        // Escuchar evento global
        window.addEventListener('languageChanged', (event) => {
            this.currentLang = event.detail.language;
            this.applyLanguage();
        });
    }

    // Aplicar a la página actual
    applyLanguage() {
        if (typeof window.showLanguage === 'function') {
            window.showLanguage(this.currentLang);
        }

        this.updateLanguageSwitchers();
    }

    // Actualizar botones y banderas
    updateLanguageSwitchers() {
        document.querySelectorAll('.lang-btn').forEach(btn => {
            btn.classList.remove('active');
            if (btn.id === `btn-${this.currentLang}`) {
                btn.classList.add('active');
            }
        });

        document.querySelectorAll('.lang-flag').forEach(flag => {
            flag.classList.remove('active');
            if (flag.dataset.lang === this.currentLang) {
                flag.classList.add('active');
            }
        });
    }

    // Obtener idioma actual
    getCurrentLanguage() {
        return this.currentLang;
    }

    isSpanish() {
        return this.currentLang === 'espanol';
    }

    isEnglish() {
        return this.currentLang === 'ingles';
    }
}

// Crear instancia global
window.languageManager = new LanguageManager();

// Compatibilidad con código anterior
window.setLanguage = (lang) => window.languageManager.setLanguage(lang);
window.getCurrentLanguage = () => window.languageManager.getCurrentLanguage();
