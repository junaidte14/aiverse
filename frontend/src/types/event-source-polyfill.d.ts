declare module 'event-source-polyfill' {
    export class EventSourcePolyfill extends EventSource {
        constructor(
            url: string,
            eventSourceInitDict?: {
                headers?: Record<string, string>;
                heartbeatTimeout?: number;
                withCredentials?: boolean;
                https?: {
                    rejectUnauthorized?: boolean;
                };
            }
        );
    }
}