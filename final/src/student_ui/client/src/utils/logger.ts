export class Logger {
    private static instance: Logger;
    private logLevel: 'debug' | 'info' | 'warn' | 'error' = 'info';

    private constructor() {}

    static getInstance(): Logger {
        if (!Logger.instance) {
            Logger.instance = new Logger();
        }
        return Logger.instance;
    }

    setLogLevel(level: 'debug' | 'info' | 'warn' | 'error') {
        this.logLevel = level;
    }

    private shouldLog(level: 'debug' | 'info' | 'warn' | 'error'): boolean {
        const levels = ['debug', 'info', 'warn', 'error'];
        return levels.indexOf(level) >= levels.indexOf(this.logLevel);
    }

    debug(message: string, ...args: any[]) {
        if (this.shouldLog('debug')) {
            console.debug(`[DEBUG] ${message}`, ...args);
        }
    }

    info(message: string, ...args: any[]) {
        if (this.shouldLog('info')) {
            console.info(`[INFO] ${message}`, ...args);
        }
    }

    warn(message: string, ...args: any[]) {
        if (this.shouldLog('warn')) {
            console.warn(`[WARN] ${message}`, ...args);
        }
    }

    error(message: string, ...args: any[]) {
        if (this.shouldLog('error')) {
            console.error(`[ERROR] ${message}`, ...args);
        }
    }

    group(label: string) {
        console.group(label);
    }

    groupEnd() {
        console.groupEnd();
    }
}

export const logger = Logger.getInstance();
