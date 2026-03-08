const fs = require("fs");
const path = require("path");

const logFile = path.join(__dirname, "..", "debug.log");

function debugLog(category, message, data) {
    const timestamp = new Date().toISOString();
    const entry = `[${timestamp}] [${category}] ${message}${data ? ' | ' + JSON.stringify(data) : ''}\n`;

    // Log to console
    console.log(entry.trim());

    // Append to debug.log file
    try {
        fs.appendFileSync(logFile, entry);
    } catch (err) {
        console.error("[DEBUG] Failed to write to debug.log:", err.message);
    }
}

function clearLog() {
    try {
        fs.writeFileSync(logFile, `=== Reboot Launcher Debug Log ===\nStarted: ${new Date().toISOString()}\n\n`);
    } catch (err) {
        // Ignore
    }
}

module.exports = { debugLog, clearLog };
