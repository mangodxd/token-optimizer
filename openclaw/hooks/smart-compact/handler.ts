import { captureCheckpoint, captureCheckpointV2, restoreCheckpoint } from "../../src/smart-compact";

interface HookEvent {
  type: string;
  action: string;
  sessionId?: string;
  messages?: Array<{ role: string; content: string; timestamp?: string }>;
  inject?: (content: string) => void;
}

const handler = async (event: HookEvent) => {
  if (event.type !== "session") return;

  if (event.action === "compact:before" && event.sessionId) {
    const session = {
      sessionId: event.sessionId,
      messages: event.messages,
    };
    captureCheckpointV2(session) ?? captureCheckpoint(session);
  }

  if (event.action === "compact:after" && event.sessionId) {
    const checkpoint = restoreCheckpoint(event.sessionId);
    if (checkpoint && event.inject) {
      event.inject(checkpoint);
    }
  }
};

export default handler;
