/**
 * Secure logging utility for production environment
 * Only logs in development mode, prevents console exposure in production
 */

type LogLevel = 'log' | 'warn' | 'error' | 'debug';

interface LoggerInterface {
  (message?: any, ...optionalParams: any[]): void;
  error: (message?: any, ...optionalParams: any[]) => void;
  warn: (message?: any, ...optionalParams: any[]) => void;
  debug: (message?: any, ...optionalParams: any[]) => void;
}

const createSecureLogger = (): LoggerInterface => {
  const isDevelopment = process.env.NODE_ENV !== 'production';

  const logFunction = (level: LogLevel) => {
    return (message?: any, ...optionalParams: any[]) => {
      if (isDevelopment) {
        switch (level) {
          case 'log':
            console.log(message, ...optionalParams);
            break;
          case 'warn':
            console.warn(message, ...optionalParams);
            break;
          case 'error':
            console.error(message, ...optionalParams);
            break;
          case 'debug':
            console.debug(message, ...optionalParams);
            break;
        }
      }
      // In production, all logs are silently dropped
    };
  };

  const logger = logFunction('log') as LoggerInterface;
  logger.error = logFunction('error');
  logger.warn = logFunction('warn');
  logger.debug = logFunction('debug');

  return logger;
};

export const logger = createSecureLogger();

// Export individual methods for convenience
export const log = logger;
export const logError = logger.error;
export const logWarn = logger.warn;
export const logDebug = logger.debug;

// Export a default logger
export default logger;
