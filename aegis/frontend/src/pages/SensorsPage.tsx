import { Panel } from "../components/ui/Panel";
import { SensorPanel } from "../components/SensorPanel";
import type { SensorFrame } from "../types";

interface SensorsPageProps {
  sensors: SensorFrame | null;
}

export function SensorsPage({ sensors }: SensorsPageProps) {
  return (
    <Panel eyebrow="Sensor Suite" title="LiDAR · Ultrasonic · GPS · IMU" className="h-full">
      <SensorPanel sensors={sensors} />
    </Panel>
  );
}
