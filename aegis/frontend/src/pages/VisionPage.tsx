import { Panel } from "../components/ui/Panel";
import { VisionDetectionPanel } from "../components/VisionDetectionPanel";

export function VisionPage() {
  return (
    <Panel eyebrow="Computer Vision" title="Detection Pipeline" className="h-full">
      <VisionDetectionPanel />
    </Panel>
  );
}
