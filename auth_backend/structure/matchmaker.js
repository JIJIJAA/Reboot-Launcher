const functions = require("./functions.js");
const { debugLog } = require("./debug.js");

module.exports = async (ws) => {
  const ticketId = functions.MakeID().replace(/-/gi, "");
  const matchId = functions.MakeID().replace(/-/gi, "");
  const sessionId = functions.MakeID().replace(/-/gi, "");

  debugLog("MATCHMAKER", "Client connected", { ticketId, matchId, sessionId });

  Connecting();
  Waiting();
  Queued();
  SessionAssignment();
  Join();

  function Connecting() {
    debugLog("MATCHMAKER", "State: Connecting", { matchId });
    ws.send(
      JSON.stringify({
        payload: {
          state: "Connecting",
        },
        name: "StatusUpdate",
      })
    );
  }

  function Waiting() {
    debugLog("MATCHMAKER", "State: Waiting", { matchId });
    ws.send(
      JSON.stringify({
        payload: {
          totalPlayers: 1,
          connectedPlayers: 1,
          state: "Waiting",
        },
        name: "StatusUpdate",
      })
    );
  }

  function Queued() {
    debugLog("MATCHMAKER", "State: Queued", { matchId, ticketId });
    ws.send(
      JSON.stringify({
        payload: {
          ticketId: ticketId,
          queuedPlayers: 0,
          estimatedWaitSec: 0,
          status: {},
          state: "Queued",
        },
        name: "StatusUpdate",
      })
    );
  }

  function SessionAssignment() {
    debugLog("MATCHMAKER", "State: SessionAssignment", { matchId });
    ws.send(
      JSON.stringify({
        payload: {
          matchId: matchId,
          state: "SessionAssignment",
        },
        name: "StatusUpdate",
      })
    );
  }

  function Join() {
    debugLog("MATCHMAKER", "State: Join (Play)", { matchId, sessionId });
    ws.send(
      JSON.stringify({
        payload: {
          matchId: matchId,
          sessionId: sessionId,
          joinDelaySec: 1,
        },
        name: "Play",
      })
    );
  }
};