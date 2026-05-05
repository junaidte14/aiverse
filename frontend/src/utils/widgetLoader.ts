/**
 * Widget Loader Script
 * This file will be bundled separately for external embedding
 */

interface WidgetConfig {
    collection?: string;
    provider?: string;
    model?: string;
    guestAllowed?: boolean;
    initialMessage?: string;
    primaryColor?: string;
    position?: 'bottom-right' | 'bottom-left';
    title?: string;
    apiUrl?: string;
}

class AIVerseWidget {
    private iframe: HTMLIFrameElement | null = null;
    private config: WidgetConfig;
    private baseUrl: string;

    constructor(config: WidgetConfig = {}) {
        this.config = {
            guestAllowed: true,
            provider: 'groq',
            model: 'llama-3.3-70b-versatile',
            primaryColor: '#9333ea',
            position: 'bottom-right',
            title: 'AI Assistant',
            apiUrl: import.meta.env.VITE_API_URL || 'https://junaidte14-aiverse.hf.space/api/v1/',
            ...config,
        };

        this.baseUrl = 'https://aiverse-pi.vercel.app';
        this.init();
        this.setupListeners();
    }

    private init() {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.render());
        } else {
            this.render();
        }
    }

    setupListeners() {
        window.addEventListener('message', (event) => {
            // Security check: ensure the message is the expected type
            if (event.data.type === 'WIDGET_RESIZE' && this.iframe) {
                // Apply the new dimensions sent from the React app
                this.iframe.style.width = event.data.width;
                this.iframe.style.height = event.data.height;

                // Toggle pointer-events if needed
                if (event.data.width === '80px') {
                    // Small bubble state
                    this.iframe.style.pointerEvents = 'auto';
                } else {
                    // Expanded chat state
                    this.iframe.style.pointerEvents = 'auto';
                }
            }
        });
    }

    private buildWidgetUrl(): string {
        const params = new URLSearchParams();

        if (this.config.collection) params.append('collection', this.config.collection);
        if (this.config.provider) params.append('provider', this.config.provider);
        if (this.config.model) params.append('model', this.config.model);
        if (this.config.guestAllowed !== undefined)
            params.append('guestAllowed', this.config.guestAllowed.toString());
        if (this.config.initialMessage) params.append('initialMessage', this.config.initialMessage);
        if (this.config.primaryColor) params.append('primaryColor', this.config.primaryColor);
        if (this.config.position) params.append('position', this.config.position);
        if (this.config.title) params.append('title', this.config.title);

        return `${this.baseUrl}/widget?${params.toString()}`;
    }

    private render() {
        this.iframe = document.createElement('iframe');
        this.iframe.src = this.buildWidgetUrl();

        // Ensure the iframe has a transition for smooth resizing
        Object.assign(this.iframe.style, {
            position: 'fixed',
            bottom: '0',
            right: this.config.position === 'bottom-left' ? 'auto' : '0',
            left: this.config.position === 'bottom-left' ? '0' : 'auto',
            width: '80px',
            height: '80px',
            border: 'none',
            zIndex: '999999',
            background: 'transparent',
            transition: 'width 0.3s ease, height 0.3s ease' // Smooth transition
        });

        document.body.appendChild(this.iframe);
    }

    public destroy() {
        if (this.iframe && this.iframe.parentNode) {
            this.iframe.parentNode.removeChild(this.iframe);
            this.iframe = null;
        }
    }
}

// Make it available globally for external HTML files
if (typeof window !== 'undefined') {
    (window as any).AIVerseWidget = AIVerseWidget;
}

export default AIVerseWidget;