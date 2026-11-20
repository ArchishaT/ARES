import { Panel } from "../components/ui/Panel";
import { EventLog } from "../components/EventLog";
import type { LogEntry } from "../types";

interface EventLogPageProps {
  logs: LogEntry[];
}

export function EventLogPage({ logs }: EventLogPageProps) {
  return (
    <Panel eyebrow="System Events" title="Event Log" className="h-full">
      <EventLog logs={logs} />
    </Panel>
  );
}
